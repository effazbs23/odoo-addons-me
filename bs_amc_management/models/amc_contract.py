from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_round


class AmcContract(models.Model):
    """An annual maintenance contract, and the service periods it is cut into.

    One record covers both, told apart by ``parent_amc_id``:

    * a **Mother AMC** is raised from a purchase order line when the order is marked
      as signed. It carries the money, the dates and the vendor.
    * a **service period** is a child of a Mother, one per unit of frequency. It is
      what gets serviced, closed, and reversed when it is not.
    """
    _name = 'amc.contract'
    _description = 'Annual Maintenance Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_names_search = ['name', 'amc_ref', 'po_id.name']

    name = fields.Char(string='Contract Name', required=True, tracking=True)
    amc_ref = fields.Char(string='AMC Reference', compute='_compute_amc_ref', store=True,
                          copy=False, index=True, recursive=True,
                          help='Reference of the contract: the order number followed by the '
                               'rank of the Mother AMC on that order, and by the period '
                               'number on a service period. Stamped once and never '
                               'renumbered afterwards.')
    parent_amc_id = fields.Many2one('amc.contract', string='Mother AMC', ondelete='restrict',
                                    index=True, copy=False)
    child_amc_ids = fields.One2many('amc.contract', 'parent_amc_id', string='Service Periods')
    company_id = fields.Many2one('res.company', string='Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    site_id = fields.Many2one('amc.site', string='Site', check_company=True, tracking=True)
    site_code = fields.Char(related='site_id.code', string='Site Code', store=True)
    contractor_id = fields.Many2one('res.partner', string='Contractor', tracking=True)
    po_id = fields.Many2one('purchase.order', string='Purchase Order', check_company=True,
                            index=True, ondelete='restrict')
    currency_id = fields.Many2one('res.currency', related='po_id.currency_id', string='Currency',
                                  store=True)
    payment_term_id = fields.Many2one('account.payment.term', related='po_id.payment_term_id',
                                      string='Payment Terms', store=True)
    po_total = fields.Monetary(string='Order Total', related='po_id.amount_total',
                               currency_field='currency_id', store=True)

    amc_charge_annum = fields.Monetary(string='Contract Value', currency_field='currency_id',
                                       tracking=True,
                                       help='Value of the contract net of tax. Provisions accrue '
                                            'this amount over the contract period.')
    frequency_number = fields.Integer(string='Number of Service Periods', default=1, tracking=True)
    amc_period_amount = fields.Monetary(string='Amount Per Period', compute='_compute_amc_period_amount',
                                        currency_field='currency_id', store=True)
    start_date = fields.Date(string='Start Date', default=fields.Date.context_today, tracking=True)
    end_date = fields.Date(string='End Date', default=fields.Date.context_today, tracking=True)
    service_days = fields.Integer(string='Service Days', compute='_compute_service_days', store=True)
    period_seq = fields.Integer(string='Period Number', copy=False)
    expiry_time = fields.Integer(string='Time To Expiry (in days)', copy=False)
    completed_date = fields.Date(string='Completed Date', copy=False)

    service_report = fields.Binary(string='Service Report', attachment=True, copy=False)
    service_report_filename = fields.Char(string='Service Report Filename', copy=False)
    other_attachment_ids = fields.Many2many(
        'ir.attachment', 'amc_other_attachment_rel', 'amc_id', 'attachment_id',
        string='Other Attachments', copy=False)
    service_report_count = fields.Integer(string='Service Reports', compute='_compute_service_report_count')

    purchase_line_ids = fields.One2many('purchase.order.line', 'amc_id', string='Purchase Lines')
    all_purchase_line_ids = fields.Many2many('purchase.order.line', string='Purchase History',
                                             compute='_compute_all_purchase_line_ids')
    product_id = fields.Many2one('product.product', string='Product',
                                 compute='_compute_product_id', store=True, recursive=True,
                                 help='Product this contract was raised for, taken from the order '
                                      'line. AMC vendor bills are billed against it, and its '
                                      'accounts drive the provision entries.')
    product_categ_id = fields.Many2one('product.category', string='Product Category',
                                       compute='_compute_product_categ_id', store=True,
                                       help='Category of the product on the contract purchase line. '
                                            'Its AMC Provision Account is what the monthly provision '
                                            'entries credit.')

    cnt_child_amc = fields.Integer(string='Periods', default=0, copy=False)
    cnt_validated_periods = fields.Integer(string='Settled Periods', default=0, copy=False)
    is_validated = fields.Boolean(string='Validated', default=False, copy=False)
    is_signed = fields.Boolean(string='Signed', default=False, copy=False, tracking=True)
    signed_date = fields.Date(string='Signed Date', copy=False, readonly=True)
    # The signed contract itself lives on the purchase order
    # (purchase.order.amc_signed_contract): one document covers every Mother AMC the
    # order carries. This only mirrors whether it has been uploaded, so the form can
    # offer it for download.
    has_signed_contract = fields.Boolean(string='Signed Contract Uploaded',
                                         compute='_compute_has_signed_contract')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('validation_pending', 'Validation Pending'),
        ('closed', 'Done'),
        ('partially_serviced', 'Partially Serviced'),
        ('terminated', 'Terminated'),
        ('expired', 'Expired'),
    ], string='Status', default='draft', required=True, tracking=True, copy=False)

    # -- service completion (service periods only) ------------------------------
    days_serviced = fields.Integer(string='Days Serviced', copy=False, tracking=True)
    days_not_serviced = fields.Integer(string='Days Not Serviced', copy=False,
                                       compute='_compute_days_not_serviced', store=True)
    completed_by_id = fields.Many2one('res.users', string='Completed By', copy=False, readonly=True)
    expiry_reason = fields.Text(string='Expiry Reason', copy=False, readonly=True)
    expired_by_id = fields.Many2one('res.users', string='Expired By', copy=False, readonly=True)
    expired_date = fields.Date(string='Expired On', copy=False, readonly=True)
    is_frozen = fields.Boolean(string='Frozen', compute='_compute_is_frozen',
                               help='Terminal service periods are read-only.')

    # -- billing / payment ------------------------------------------------------
    # amc_id also tags the provision journal entries, so the o2m has to be narrowed to
    # real bills -- otherwise every monthly provision counts as a vendor bill.
    bill_ids = fields.One2many('account.move', 'amc_id', string='Vendor Bills',
                               domain=[('move_type', 'in', ('in_invoice', 'in_refund'))])
    bill_count = fields.Integer(string='Vendor Bill Count', compute='_compute_bill_count')
    vendor_bill_ids = fields.Many2many('account.move', 'amc_period_account_move_rel',
                                       'amc_period_id', 'move_id', string='Linked Vendor Bills')
    vendor_bill_id = fields.Many2one('account.move', string='Vendor Bill',
                                     compute='_compute_vendor_bill_id')
    payment_ids = fields.Many2many('account.payment', string='Payments', compute='_compute_payment_info')
    payment_count = fields.Integer(string='Payment Count', compute='_compute_payment_info')
    payment_reference = fields.Char(string='Payment Reference', compute='_compute_payment_info')
    amount_paid = fields.Monetary(string='Total Paid', compute='_compute_billed_amounts',
                                  currency_field='currency_id',
                                  help="Settled portion of this AMC's posted vendor bills, "
                                       "net of any credit notes. Tax inclusive.")
    amount_outstanding = fields.Monetary(string='Outstanding Amount', compute='_compute_billed_amounts',
                                         currency_field='currency_id',
                                         help="Unsettled balance of this AMC's posted vendor bills, "
                                              "net of any credit notes. Tax inclusive. Contract value "
                                              "not yet billed is not counted here.")
    payment_status = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('advance_paid', 'Advance Paid'),
        ('paid', 'Paid'),
    ], string='Payment Status', compute='_compute_payment_status', store=True)
    finance_state = fields.Selection([
        ('none', 'Not Billed'),
        ('waiting', 'Waiting for Validation'),
        ('validated', 'Validated'),
    ], string='Finance Status', compute='_compute_finance_state', store=True, default='none')

    # -- provisioning -----------------------------------------------------------
    provision_move_ids = fields.Many2many('account.move', string='Provision Entries',
                                          compute='_compute_provision_move_ids')
    provision_move_count = fields.Integer(string='Monthly Provisions',
                                          compute='_compute_provision_move_ids')
    purchase_order_ids = fields.Many2many('purchase.order', string='Purchase Orders',
                                          compute='_compute_purchase_order_ids')
    purchase_order_count = fields.Integer(string='Purchase Order Count', compute='_compute_purchase_order_ids')

    # ------------------------------------------------------------------
    # Reference
    # ------------------------------------------------------------------

    def _amc_period_rank(self):
        """Position of this service period among its siblings, by creation order.

        Only used for periods carrying no period_seq, where numbering every one of
        them P1 would hand a Mother's periods the same reference.
        _amc_build_periods creates the periods in date order, so id order and period
        order agree.
        """
        self.ensure_one()
        record_id = self._origin.id
        if not record_id:
            return 1
        return self.search_count([
            ('parent_amc_id', '=', self.parent_amc_id.id),
            ('id', '<', record_id),
        ]) + 1

    def _amc_next_reference(self, taken=()):
        """Reference to stamp on this record, or False while it cannot be derived yet.

        A Mother AMC is numbered inside its purchase order: ``PO name-1``, ``-2``, one
        number per Mother the order carries. A service period extends its Mother's
        reference with its own period number, so ``PO name-1-P3`` reads back to both
        the contract it belongs to and the period within it.
        """
        self.ensure_one()
        if self.parent_amc_id:
            # A Mother's rank is a function of ids only, so a period whose Mother has
            # not been numbered yet can derive the same string its Mother will settle
            # on rather than end up with no reference.
            parent_ref = self.parent_amc_id.amc_ref or self.parent_amc_id._amc_next_reference()
            return '%s-P%s' % (parent_ref, self.period_seq or self._amc_period_rank()) \
                if parent_ref else False
        # The rank is read off the record's own id, so an unsaved record cannot be
        # numbered yet; it picks its reference up once it is created.
        record_id = self._origin.id
        if not self.po_id or not record_id:
            return False
        # Only Mother AMCs are counted, so a second Mother is numbered after its
        # sibling rather than after its sibling's periods.
        siblings = self.search([
            ('po_id', '=', self.po_id.id),
            ('parent_amc_id', '=', False),
            ('id', '!=', record_id),
        ])
        rank = len(siblings.filtered(lambda amc: amc.id < record_id)) + 1
        # A Mother deleted after its siblings were numbered would leave a gap, and the
        # next one would reuse a reference that is already in print; skip past those,
        # and past anything handed out earlier in the same compute batch.
        used = set(siblings.mapped('amc_ref')) | set(taken)
        reference = '%s-%s' % (self.po_id.name, rank)
        while reference in used:
            rank += 1
            reference = '%s-%s' % (self.po_id.name, rank)
        return reference

    @api.depends('po_id.name', 'parent_amc_id.amc_ref', 'period_seq')
    def _compute_amc_ref(self):
        """Stamp the reference once, then leave it alone.

        The depends only serve to fill a record that has none yet. An existing
        reference is never recomputed: it is printed on the AMC schedule and quoted by
        Finance, so renaming the order or deleting a sibling contract must not
        renumber contracts that are already in circulation.
        """
        # Records computed together are not flushed yet, so the search behind
        # _amc_next_reference cannot see them; carry what this batch has already
        # handed out so two Mothers of one order cannot take the same number.
        taken = set()
        # Mothers first: a period reads its Mother's reference, and a batch computed
        # in id desc order puts the periods ahead of the Mothers they hang off.
        mothers = self.filtered(lambda record: not record.parent_amc_id)
        for record in mothers + (self - mothers):
            record.amc_ref = record.amc_ref or record._amc_next_reference(taken=taken)
            if record.amc_ref:
                taken.add(record.amc_ref)

    @api.depends('name', 'po_id.name')
    def _compute_display_name(self):
        for record in self:
            name = record.name or ''
            record.display_name = '%s - %s' % (name, record.po_id.name) if record.po_id else name

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------

    @api.depends('amc_charge_annum', 'parent_amc_id.amc_charge_annum',
                 'frequency_number', 'parent_amc_id.frequency_number')
    def _compute_amc_period_amount(self):
        for record in self:
            # A service period covers one period, so the split is always driven by the
            # Mother's frequency.
            contract = record.parent_amc_id or record
            periods = contract.frequency_number
            record.amc_period_amount = contract.amc_charge_annum / periods if periods else 0.0

    @api.depends('start_date', 'end_date')
    def _compute_service_days(self):
        for record in self:
            # Inclusive of both endpoints, matching how the periods are cut in
            # _amc_build_periods and how expiry_time is computed.
            record.service_days = (record.end_date - record.start_date).days + 1 \
                if record.start_date and record.end_date else 0

    @api.depends('service_days', 'days_serviced', 'state')
    def _compute_days_not_serviced(self):
        for record in self:
            if record.state == 'expired':
                record.days_not_serviced = record.service_days
            elif record.state == 'partially_serviced':
                record.days_not_serviced = max(record.service_days - record.days_serviced, 0)
            else:
                record.days_not_serviced = 0

    @api.depends('state', 'parent_amc_id')
    def _compute_is_frozen(self):
        for record in self:
            record.is_frozen = bool(record.parent_amc_id) and record.state in (
                'closed', 'partially_serviced', 'expired')

    @api.depends('bill_ids', 'vendor_bill_ids', 'parent_amc_id')
    def _compute_bill_count(self):
        for record in self:
            record.bill_count = len(record._amc_related_bills())

    @api.depends('vendor_bill_ids')
    def _compute_vendor_bill_id(self):
        for record in self:
            record.vendor_bill_id = record.vendor_bill_ids[:1]

    @api.depends('child_amc_ids.service_report')
    def _compute_service_report_count(self):
        for record in self:
            record.service_report_count = len(record.child_amc_ids.filtered('service_report'))

    @api.depends('purchase_line_ids.product_id', 'parent_amc_id.product_id')
    def _compute_product_id(self):
        """Product this contract was raised for, stored so every consumer reads one value.

        Only the Mother AMC carries the purchase line, so a service period reads the
        product off its Mother. Read as sudo: AMC roles own contracts but need not
        hold purchase access.
        """
        for record in self:
            if record.parent_amc_id:
                record.product_id = record.parent_amc_id.product_id
            else:
                record.product_id = record.sudo().purchase_line_ids[:1].product_id

    @api.depends('product_id')
    def _compute_product_categ_id(self):
        for record in self:
            record.product_categ_id = record.product_id.categ_id

    @api.depends('purchase_line_ids', 'child_amc_ids.purchase_line_ids',
                 'parent_amc_id.purchase_line_ids')
    def _compute_all_purchase_line_ids(self):
        """Purchase lines to show on both a Mother AMC and its service periods.

        The AMC's own order line is tagged with the Mother, while a follow-up material
        order can be tagged against either the Mother or an individual period through
        purchase.order.line.amc_id -- so both ends have to be read from both sides.
        """
        for record in self:
            if record.parent_amc_id:
                # The contract's own line, plus whatever was bought against this period.
                record.all_purchase_line_ids = \
                    record.parent_amc_id.purchase_line_ids | record.purchase_line_ids
            else:
                # This contract's line, plus everything bought against any of its periods.
                record.all_purchase_line_ids = \
                    record.purchase_line_ids | record.child_amc_ids.purchase_line_ids

    @api.depends('po_id', 'all_purchase_line_ids')
    def _compute_purchase_order_ids(self):
        for record in self:
            orders = record.all_purchase_line_ids.mapped('order_id')
            record.purchase_order_ids = orders
            record.purchase_order_count = len(orders)

    @api.depends('po_id', 'child_amc_ids')
    def _compute_provision_move_ids(self):
        Move = self.env['account.move'].sudo()
        for record in self:
            if record.parent_amc_id:
                # A service period only owns the reversal entries raised against it.
                moves = Move.search([('amc_service_period_id', '=', record.id)])
            else:
                moves = Move.search(Move._amc_provision_domain(contract=record))
            record.provision_move_ids = moves
            record.provision_move_count = len(moves)

    # ------------------------------------------------------------------
    # Bills and payments
    # ------------------------------------------------------------------

    def _amc_related_bills(self):
        """Bills relevant to this record: Mother AMC bills, or the period's own bills.

        Read as sudo so the smart-button counts do not break the form for AMC roles,
        which own contracts but hold no accounting access.
        """
        self.ensure_one()
        record = self.sudo()
        return record.vendor_bill_ids if record.parent_amc_id else record.bill_ids

    def _amc_settled_payments(self):
        """Payments matched to this record's bills, excluding unconfirmed ones."""
        self.ensure_one()
        return self._amc_related_bills().sudo().mapped('matched_payment_ids').filtered(
            lambda pay: pay.state not in ('draft', 'canceled', 'rejected'))

    @api.depends('vendor_bill_ids.matched_payment_ids.state',
                 'vendor_bill_ids.matched_payment_ids.name',
                 'bill_ids.matched_payment_ids.state',
                 'bill_ids.matched_payment_ids.name')
    def _compute_payment_info(self):
        for record in self:
            payments = record._amc_settled_payments()
            record.payment_ids = payments
            record.payment_count = len(payments)
            record.payment_reference = ', '.join(payments.mapped('name')) if payments else False

    # Kept separate from _compute_payment_info: this one is stored, and Odoo requires
    # stored and non-stored computed fields to use distinct compute methods.
    @api.depends('vendor_bill_ids.matched_payment_ids.state',
                 'vendor_bill_ids.matched_payment_ids.date',
                 'bill_ids.matched_payment_ids.state',
                 'bill_ids.matched_payment_ids.date',
                 'start_date')
    def _compute_payment_status(self):
        for record in self:
            payments = record._amc_settled_payments()
            if not payments:
                record.payment_status = 'not_paid'
                continue
            first_payment_date = min(payments.mapped('date'))
            if record.start_date and first_payment_date < record.start_date:
                record.payment_status = 'advance_paid'
            else:
                record.payment_status = 'paid'

    @api.depends('vendor_bill_ids.amount_total', 'vendor_bill_ids.amount_residual',
                 'vendor_bill_ids.state', 'vendor_bill_ids.move_type',
                 'bill_ids.amount_total', 'bill_ids.amount_residual',
                 'bill_ids.state', 'bill_ids.move_type')
    def _compute_billed_amounts(self):
        """Paid and outstanding, taken from the bills rather than the contract value.

        Both figures are tax inclusive, and follow what was actually invoiced and
        settled rather than what the order said it would be. Only posted bills count
        -- a draft bill is not yet a liability -- and a credit note subtracts, so a
        refunded milestone unwinds both figures.
        """
        for record in self:
            # _amc_related_bills already sudo's: AMC roles own contracts but cannot
            # read moves.
            bills = record._amc_related_bills().filtered(lambda bill: bill.state == 'posted')
            paid = outstanding = 0.0
            for bill in bills:
                sign = -1 if bill.move_type == 'in_refund' else 1
                paid += sign * (bill.amount_total - bill.amount_residual)
                outstanding += sign * bill.amount_residual
            record.amount_paid = paid
            record.amount_outstanding = outstanding

    @api.depends('vendor_bill_ids.state')
    def _compute_finance_state(self):
        for record in self:
            bills = record.sudo().vendor_bill_ids
            if not bills:
                record.finance_state = 'none'
            elif all(bill.state == 'posted' for bill in bills):
                record.finance_state = 'validated'
            else:
                record.finance_state = 'waiting'

    # ------------------------------------------------------------------
    # Provisioning helpers
    # ------------------------------------------------------------------

    def _amc_daily_rate(self):
        """Daily provision rate of the Mother AMC this record belongs to, in company currency.

        Matches what the monthly breakdown books, so a reversal always undoes the same
        money the provision entries put in.
        """
        self.ensure_one()
        contract = self.parent_amc_id or self
        if not contract.start_date or not contract.end_date:
            return 0.0
        total_days = (contract.end_date - contract.start_date).days + 1
        if total_days <= 0:
            return 0.0
        value = contract.po_id._amc_contract_value(contract) if contract.po_id \
            else contract.amc_charge_annum
        return value / total_days

    def _amc_expense_account(self):
        """Expense account debited by this contract's provision entries.

        Read from the contract's product: the product's own Expense Account, else the
        one on its product category. This is the same account the AMC's vendor bill
        would post to, so the provision and the bill that draws it down land in the
        same place.

        Returns an empty recordset when the product resolves to neither; use
        ``_amc_check_expense_accounts`` to turn that into a user-facing error.

        Resolved fresh on every call, so changing the product's expense account
        mid-contract sends later provisions -- and any reversal raised after the
        change -- to the new account rather than the one already debited.
        """
        self.ensure_one()
        contract = self.sudo()
        if not contract.product_id:
            return self.env['account.account']
        # The expense account is company-dependent, hence with_company.
        company = contract.company_id or self.env.company
        accounts = contract.product_id.with_company(company).product_tmpl_id.get_product_accounts()
        return accounts.get('expense') or self.env['account.account']

    def _amc_provision_account(self):
        """Provision account credited by this contract's provision entries.

        Read from the AMC Provision Account set on the category of the contract's
        product. Unlike the expense account, there is no product-level override --
        provisioning is configured per category only.

        Returns an empty recordset when the product or its category resolves to none;
        use ``_amc_check_provision_accounts`` to turn that into a user-facing error.
        """
        self.ensure_one()
        contract = self.sudo()
        if not contract.product_id:
            return self.env['account.account']
        company = contract.company_id or self.env.company
        return contract.product_id.categ_id.with_company(company).amc_provision_account_id \
            or self.env['account.account']

    def _amc_site(self):
        """Site carried by this contract's purchase line, or the contract's own."""
        self.ensure_one()
        line = self.sudo().purchase_line_ids[:1]
        if line and line.amc_site_id:
            return line.amc_site_id
        return self.site_id

    def _amc_check_expense_accounts(self):
        """Resolve every contract's expense account up front, or raise naming the gaps."""
        missing = self.filtered(lambda contract: not contract._amc_expense_account())
        if missing:
            raise UserError(_(
                "No expense account could be determined for %(names)s.\n"
                "Set an Expense Account on the product used on the purchase order line, "
                "or on its product category.",
                names=', '.join(missing.mapped('display_name')),
            ))

    def _amc_check_provision_accounts(self):
        """Resolve every contract's provision account up front, or raise naming the gaps."""
        missing = self.filtered(lambda contract: not contract._amc_provision_account())
        if missing:
            raise UserError(_(
                "No AMC Provision Account could be determined for %(names)s.\n"
                "Set an AMC Provision Account on the product category used on the purchase "
                "order line.",
                names=', '.join(missing.mapped('display_name')),
            ))

    def _amc_create_reversal_provision(self, reason_label):
        """Book a standalone draft reversal entry for the non-serviced days of this period.

        Existing monthly provision entries are never touched: the reversal is an
        independent entry that Finance reviews and posts on its own.
        """
        self.ensure_one()
        Move = self.env['account.move'].sudo()
        mother = self.parent_amc_id
        if not mother or not mother.po_id:
            return Move
        amount = self._amc_daily_rate() * self.days_not_serviced
        currency = mother.po_id._amc_company_currency()
        if float_is_zero(amount, precision_rounding=currency.rounding):
            return Move

        reference = _('Reversal - P%(seq)s %(reason)s', seq=self.period_seq or '?', reason=reason_label)
        accounting_date = fields.Date.context_today(self)
        amount = float_round(amount, precision_rounding=currency.rounding)

        # The 'reversal' type is what flips the entry to Dr Provision / Cr Expense.
        vals = Move._prepare_amc_provision_vals(
            mother.po_id, reference, 'reversal',
            accounting_date.replace(day=1), accounting_date, {mother: amount})
        vals['amc_service_period_id'] = self.id
        return Move.create(vals)

    # ------------------------------------------------------------------
    # Attachments
    # ------------------------------------------------------------------

    def _amc_field_attachment(self, field_name):
        """The ir.attachment backing an ``attachment=True`` binary field."""
        self.ensure_one()
        return self.env['ir.attachment'].sudo().search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('res_field', '=', field_name),
        ], limit=1)

    def _amc_service_attachments(self):
        """(attachment, display name) pairs held by this service period.

        The service report is stored behind a binary field, so its ir.attachment is
        named after the field rather than the uploaded file; the real filename lives
        in service_report_filename and is what the copy should carry.
        """
        self.ensure_one()
        pairs = []
        report = self._amc_field_attachment('service_report')
        if report:
            pairs.append((report, self.service_report_filename or report.name))
        for attachment in self.other_attachment_ids:
            pairs.append((attachment, attachment.name))
        return pairs

    def _amc_copy_attachments_to(self, record):
        """Duplicate this record's attachments onto ``record``, leaving the originals intact."""
        self.ensure_one()
        copies = self.env['ir.attachment']
        for attachment, name in self._amc_service_attachments():
            copies |= attachment.sudo().copy({
                'res_model': record._name,
                'res_id': record.id,
                # res_field must be cleared or the copy becomes an inaccessible binary
                # field store
                'res_field': False,
                'name': name,
            })
        return copies

    def _amc_signed_contract_source(self):
        """(purchase order, attachment) holding the signed contract for this AMC."""
        self.ensure_one()
        order = (self.parent_amc_id or self).po_id
        if not order:
            return order, self.env['ir.attachment']
        return order, order._amc_signed_contract_attachment()

    @api.depends('po_id.amc_signed_contract', 'parent_amc_id.po_id.amc_signed_contract')
    def _compute_has_signed_contract(self):
        for record in self:
            order = (record.parent_amc_id or record).po_id
            # bin_size yields the file size instead of the payload, so this stays cheap
            # in list views where every row would otherwise load the whole document.
            # sudo for the same reason as _amc_related_bills: this feeds a stat
            # button's invisible, and an AccessError here would fail the whole form.
            record.has_signed_contract = bool(
                order.sudo().with_context(bin_size=True).amc_signed_contract) if order else False

    def _amc_copy_signed_contract_to(self, record):
        """Attach the order's signed AMC contract to ``record``."""
        self.ensure_one()
        order, source = self._amc_signed_contract_source()
        if not source:
            return self.env['ir.attachment']
        return source.sudo().copy({
            'res_model': record._name,
            'res_id': record.id,
            'res_field': False,
            'name': order.amc_signed_contract_filename or _('Signed AMC Contract'),
        })

    # ------------------------------------------------------------------
    # Period generation
    # ------------------------------------------------------------------

    def _amc_whole_months(self):
        """Number of whole calendar months between start_date and end_date, or 0.

        A contract runs to the day before its anniversary -- 15 Jan to 14 Feb is one
        month -- so the span is whole when the day after end_date lands exactly on a
        month step from start_date. Both the month difference and the one above it are
        tried because that difference undercounts whenever end_date falls earlier in
        its month than start_date does in its own.
        """
        self.ensure_one()
        months = ((self.end_date.year - self.start_date.year) * 12
                  + self.end_date.month - self.start_date.month)
        for candidate in (months, months + 1):
            if candidate > 0 and self.start_date + relativedelta(months=candidate) \
                    == self.end_date + timedelta(days=1):
                return candidate
        return 0

    def _amc_period_vals(self, index, start_date, end_date):
        """Values for one service period of this Mother AMC."""
        self.ensure_one()
        return {
            'parent_amc_id': self.id,
            'company_id': self.company_id.id,
            'site_id': self.site_id.id,
            'po_id': self.po_id.id,
            'name': '%s (P%s)' % (self.name, index + 1),
            'period_seq': index + 1,
            'contractor_id': self.contractor_id.id,
            'start_date': start_date,
            'end_date': end_date,
            'expiry_time': (end_date - fields.Date.context_today(self)).days,
            'state': 'draft',
        }

    def _amc_build_periods(self):
        """Cut this Mother AMC into ``frequency_number`` consecutive service periods.

        A contract covering a whole number of months that divides evenly by the
        frequency is cut on the calendar: a monthly AMC starting on the 15th then runs
        the 15th to the 14th throughout. Anything else -- a 100-day contract, or 12
        months split 5 ways -- gets an even split by days, with the remainder handed
        one day at a time to the earliest periods.
        """
        self.ensure_one()
        total_days = (self.end_date - self.start_date).days + 1
        base_days = total_days // self.frequency_number
        remaining_days = total_days % self.frequency_number
        whole_months = self._amc_whole_months()
        months_per_period = (whole_months // self.frequency_number
                             if whole_months and not whole_months % self.frequency_number
                             else 0)

        vals_list = []
        current_start = self.start_date
        for index in range(self.frequency_number):
            if months_per_period:
                # Measured from start_date rather than from the period before it, so
                # the clamping relativedelta does at the end of a short month cannot
                # accumulate and the last period still ends exactly on end_date.
                current_start = self.start_date + relativedelta(months=index * months_per_period)
                current_end = self.start_date + relativedelta(
                    months=(index + 1) * months_per_period) - timedelta(days=1)
            else:
                duration = base_days + (1 if index < remaining_days else 0)
                current_end = current_start + timedelta(days=duration - 1)
            vals_list.append(self._amc_period_vals(index, current_start, current_end))
            current_start = current_end + timedelta(days=1)

        self.cnt_child_amc = self.frequency_number
        return self.create(vals_list)

    def _amc_check_activatable(self):
        """Everything period generation needs, checked before a single record is written."""
        self.ensure_one()
        if not self.start_date or not self.end_date:
            raise UserError(_("The Start Date and End Date must be set on %s.", self.display_name))
        if self.start_date > self.end_date:
            raise UserError(_("The Start Date cannot be after the End Date on %s.", self.display_name))
        if self.frequency_number <= 0:
            raise UserError(_("The Number of Service Periods must be a positive integer on %s.",
                              self.display_name))

    def action_activate_parent_amc(self):
        """Generate the service periods of a Mother AMC and put it in progress."""
        for record in self:
            if record.parent_amc_id:
                continue
            record._amc_check_activatable()
            if not record.child_amc_ids:
                record._amc_build_periods()
            record.state = 'in_progress'
        return True

    def action_activate_child_amc(self):
        self.write({'state': 'in_progress'})
        return True

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    TERMINAL_PERIOD_STATES = ('closed', 'partially_serviced', 'expired')

    def action_send_for_validation(self):
        self.write({'state': 'validation_pending'})
        return True

    def action_terminate(self):
        for record in self:
            record.write({'state': 'terminated'})
            record.child_amc_ids.filtered(
                lambda child: child.state not in ('closed', 'terminated')
            ).write({'state': 'terminated'})
        return True

    def action_close(self):
        """Close a Mother AMC by hand, ahead of all its periods being settled.

        Guarded to match the button's visibility so the action cannot be reached in a
        state the UI never offers it in.
        """
        for record in self:
            if record.parent_amc_id:
                raise UserError(_(
                    "Only a Mother AMC can be closed here. Close a service period with "
                    "Mark as Done instead."))
            if record.state != 'in_progress':
                raise UserError(_("Only an in-progress AMC can be closed."))
            record.state = 'closed'
        return True

    def action_reset_to_draft(self):
        for record in self:
            if record.parent_amc_id:
                raise UserError(_("Only a Mother AMC can be reset to draft here."))
            record.write({'state': 'draft', 'is_signed': False, 'signed_date': False})
        return True

    def _amc_sync_parent_progress(self):
        """Recount terminal periods on the Mother AMC and close it when all are settled."""
        for mother in self.mapped('parent_amc_id'):
            children = mother.child_amc_ids
            settled = children.filtered(lambda c: c.state in self.TERMINAL_PERIOD_STATES)
            mother.cnt_validated_periods = len(settled)
            if children and len(settled) == len(children) and mother.state not in ('terminated', 'closed'):
                mother.state = 'closed'
            elif mother.state == 'closed' and len(settled) != len(children):
                mother.state = 'in_progress'

    def _amc_check_period_editable(self):
        """Guard the wizard entry points: only a live service period can be closed."""
        self.ensure_one()
        if not self.parent_amc_id:
            raise UserError(_("Only a service period can be marked as serviced or expired."))
        if self.state in self.TERMINAL_PERIOD_STATES:
            raise UserError(_(
                "Service period %(name)s is already in a terminal state (%(state)s) and cannot be changed.",
                name=self.display_name, state=dict(self._fields['state'].selection).get(self.state),
            ))

    def _amc_open_wizard(self, wizard_model, title, context=None):
        self.ensure_one()
        self._amc_check_period_editable()
        ctx = dict(self.env.context, default_service_period_id=self.id)
        ctx.update(context or {})
        return {
            'name': title,
            'type': 'ir.actions.act_window',
            'res_model': wizard_model,
            'view_mode': 'form',
            'target': 'new',
            'context': ctx,
        }

    def action_mark_done(self):
        return self._amc_open_wizard('amc.mark.done.wizard', _('Mark Service Period as Done'))

    def action_mark_partially_serviced(self):
        return self._amc_open_wizard('amc.partial.service.wizard', _('Mark as Partially Serviced'))

    def action_mark_expired(self):
        return self._amc_open_wizard('amc.expire.period.wizard', _('Expire Service Period'))

    def _amc_apply_done(self):
        """Backing write for the Mark as Done wizard."""
        self.ensure_one()
        self.write({
            'is_validated': True,
            'state': 'closed',
            'completed_date': fields.Date.context_today(self),
            'completed_by_id': self.env.user.id,
            'days_serviced': self.service_days,
        })
        # Keep a copy of the service report on the Mother AMC for consolidated review.
        if self.parent_amc_id:
            self._amc_copy_attachments_to(self.parent_amc_id)
        self._amc_sync_parent_progress()
        return True

    def _amc_apply_partial_service(self, days_serviced):
        """Backing write for the Mark as Partially Serviced wizard."""
        self.ensure_one()
        if days_serviced <= 0 or days_serviced >= self.service_days:
            raise ValidationError(_(
                "Days serviced must be between 1 and %(total)s for this period. "
                "Use Mark as Done for a fully serviced period.", total=self.service_days,
            ))
        self.write({
            'is_validated': True,
            'state': 'partially_serviced',
            'days_serviced': days_serviced,
            'completed_date': fields.Date.context_today(self),
            'completed_by_id': self.env.user.id,
        })
        if self.parent_amc_id:
            self._amc_copy_attachments_to(self.parent_amc_id)
        reversal = self._amc_create_reversal_provision(_('Partial Service'))
        self._amc_sync_parent_progress()
        return reversal

    def _amc_apply_expiry(self, reason):
        """Backing write for the Expire Service Period wizard.

        Existing financials are left untouched; the shortfall is reversed through a
        separate draft entry instead.
        """
        self.ensure_one()
        self.write({
            'state': 'expired',
            'days_serviced': 0,
            'expiry_reason': reason,
            'expired_by_id': self.env.user.id,
            'expired_date': fields.Date.context_today(self),
        })
        reversal = self._amc_create_reversal_provision(_('Expired'))
        self._amc_sync_parent_progress()
        return reversal

    def action_reset_expired_to_draft(self):
        """Undo an expiry. Restricted to System Administrators."""
        for record in self:
            if not self.env.user.has_group('base.group_system'):
                raise UserError(_("Only a System Administrator can reset an expired service period to draft."))
            if record.state != 'expired':
                raise UserError(_("Only an expired service period can be reset to draft."))
            record.write({
                'state': 'draft',
                'expiry_reason': False,
                'expired_by_id': False,
                'expired_date': False,
                'days_serviced': 0,
                'is_validated': False,
            })
            record._amc_sync_parent_progress()
        return True

    # ------------------------------------------------------------------
    # Vendor billing
    # ------------------------------------------------------------------

    def action_create_vendor_bill(self):
        self.ensure_one()
        if self.parent_amc_id:
            raise UserError(_("Vendor bills are created from the Mother AMC, not from a service period."))
        if not self.is_signed:
            raise UserError(_("Mark the AMC as signed before creating vendor bills."))
        return {
            'name': _('Create Vendor Bill'),
            'type': 'ir.actions.act_window',
            'res_model': 'amc.vendor.bill.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': dict(self.env.context, default_amc_id=self.id),
        }

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def action_view_child_amc(self):
        self.ensure_one()
        children = self.child_amc_ids.sorted(lambda c: (c.period_seq, c.id), reverse=True)
        action = {
            'name': _('Service Periods'),
            'type': 'ir.actions.act_window',
            'res_model': 'amc.contract',
            'target': 'current',
            'context': {'create': False, 'amc_period_list': 1},
        }
        if len(children) == 1:
            action.update({'view_mode': 'form', 'res_id': children.id})
        else:
            action.update({'view_mode': 'list,form', 'domain': [('parent_amc_id', '=', self.id)]})
        return action

    def action_view_service_reports(self):
        """Open the service report documents themselves, not the periods holding them."""
        self.ensure_one()
        periods = self.child_amc_ids.filtered('service_report')
        attachments = self.env['ir.attachment'].sudo().search([
            ('res_model', '=', self._name),
            ('res_id', 'in', periods.ids),
            ('res_field', '=', 'service_report'),
        ])
        return {
            'name': _('Service Reports'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban',
            'views': [(self.env.ref('bs_amc_management.view_amc_service_report_kanban').id, 'kanban')],
            'target': 'current',
            # The 'id' term is load-bearing: ir.attachment._search silently injects
            # ('res_field', '=', False) unless the domain already mentions res_field or
            # id, which would hide every one of these binary-field attachments.
            'domain': [('id', 'in', attachments.ids)],
            'context': {'create': False, 'edit': False, 'delete': False},
        }

    def action_view_vendor_bills(self):
        self.ensure_one()
        bills = self._amc_related_bills()
        return {
            'name': _('Vendor Bills'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', bills.ids)],
            'context': {'create': False, 'default_move_type': 'in_invoice'},
        }

    def action_view_payments(self):
        self.ensure_one()
        return {
            'name': _('Payment History'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.payment_ids.ids)],
            'context': {'create': False},
        }

    def action_view_provision_moves(self):
        self.ensure_one()
        return {
            'name': _('AMC Provision Entries'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.provision_move_ids.ids)],
            'context': {'create': False},
        }

    def action_view_purchase_orders(self):
        self.ensure_one()
        orders = self.purchase_order_ids
        action = {
            'name': _('Purchase Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'context': {'create': False},
        }
        if len(orders) == 1:
            action.update({'view_mode': 'form', 'res_id': orders.id})
        else:
            action.update({'view_mode': 'list,form', 'domain': [('id', 'in', orders.ids)]})
        return action

    def action_view_signed_contract(self):
        """Open the signed AMC contract attachment."""
        self.ensure_one()
        order, attachment = self._amc_signed_contract_source()
        if not attachment:
            raise UserError(_(
                "No signed AMC contract has been uploaded on the purchase order %s.",
                order.display_name or ''))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    # ------------------------------------------------------------------
    # Scheduled actions
    # ------------------------------------------------------------------

    @api.model
    def _cron_update_service_periods(self):
        """Activate periods that have started, and queue the ones whose window closed.

        Reaching the terminal 'expired' state stays a deliberate user action through
        the wizard, because it carries a mandatory reason and books a reversal entry.
        """
        today = fields.Date.context_today(self)
        self.search([
            ('parent_amc_id', '!=', False),
            ('start_date', '<=', today),
            ('state', '=', 'draft'),
        ]).write({'state': 'in_progress'})
        self.search([
            ('parent_amc_id', '!=', False),
            ('state', 'in', ('draft', 'in_progress')),
            ('end_date', '<', today),
        ]).write({'state': 'validation_pending'})
        return True

    @api.model
    def _cron_update_expiry_time(self):
        """Refresh the days-to-expiry counter on every live contract."""
        today = fields.Date.context_today(self)
        contracts = self.search([
            ('state', 'not in', ('closed', 'terminated', 'expired')),
            ('end_date', '!=', False),
        ])
        for contract in contracts:
            expiry_time = (contract.end_date - today).days + 1
            if contract.expiry_time != expiry_time:
                contract.expiry_time = expiry_time
        return True

    @api.model
    def _cron_send_expiry_reminders(self):
        """Mail the contractor of every Mother AMC expiring in exactly N days."""
        params = self.env['ir.config_parameter'].sudo()
        reminder_days = params.get_param('bs_amc_management.expiry_reminder_days')
        if not reminder_days or int(reminder_days) <= 0:
            return True
        template = self.env.ref('bs_amc_management.mail_template_amc_expiry_reminder',
                                raise_if_not_found=False)
        if not template:
            return True
        target_date = fields.Date.context_today(self) + timedelta(days=int(reminder_days))
        contracts = self.search([
            ('parent_amc_id', '=', False),
            ('state', '=', 'in_progress'),
            ('end_date', '=', target_date),
        ])
        for contract in contracts:
            if not contract.contractor_id.email:
                continue
            template.send_mail(contract.id, force_send=False)
            contract.message_post(body=_(
                "AMC expiry reminder sent to %(name)s (%(email)s).",
                name=contract.contractor_id.name, email=contract.contractor_id.email))
        return True
