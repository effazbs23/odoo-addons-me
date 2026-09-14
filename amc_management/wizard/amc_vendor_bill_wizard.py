from odoo import Command, api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round


class AmcVendorBillWizard(models.TransientModel):
    _name = 'amc.vendor.bill.wizard'
    _description = 'Create AMC Vendor Bill'

    amc_id = fields.Many2one('amc.contract', string='Mother AMC',
                             required=True, readonly=True, ondelete='cascade',
                             domain=[('parent_amc_id', '=', False)])
    po_id = fields.Many2one('purchase.order', related='amc_id.po_id', string='Purchase Order',
                            readonly=True)
    partner_id = fields.Many2one('res.partner', related='amc_id.contractor_id', string='Vendor',
                                 readonly=True)
    currency_id = fields.Many2one('res.currency', related='amc_id.currency_id', readonly=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, readonly=True)
    # Defaulted from the contract's purchase line but left editable: the line does not
    # always name a site, and this is the last point at which the charge can be pointed
    # at the right one before the bill reaches Finance.
    site_id = fields.Many2one('amc.site', string='Site', compute='_compute_site_id',
                              store=True, readonly=False)

    milestone_number = fields.Integer(string='Payment Milestone', required=True,
                                      default=lambda self: self._default_milestone_number(),
                                      help='Sequential billing milestone: 1 = Q1, 2 = Q2, and so on.')
    milestone_label = fields.Char(string='Milestone', compute='_compute_milestone_label')
    is_advance = fields.Boolean(string='Advance Bill',
                                help='An advance bill carries no service period attachments; '
                                     'only the signed AMC contract is attached.')
    service_period_ids = fields.Many2many(
        'amc.contract', 'amc_vendor_bill_wizard_period_rel', 'wizard_id', 'period_id',
        string='Service Periods',
        domain="[('parent_amc_id', '=', amc_id)]",
        help='Periods this bill covers. They are linked to the bill for traceability.')
    # Kept apart from service_period_ids so a bill can carry the reports of periods it
    # does not itself cover, and so that only settled periods -- the ones that actually
    # have a service report -- can be used as an attachment source.
    service_period_attachment_ids = fields.Many2many(
        'amc.contract', 'amc_vendor_bill_wizard_attachment_rel', 'wizard_id', 'period_id',
        string='Service Report Attachments',
        domain="[('parent_amc_id', '=', amc_id), ('state', 'in', ['closed', 'partially_serviced'])]",
        help='Service reports and other attachments of these periods are copied onto the bill. '
             'Only Done or Partially Serviced periods can be attached.')
    bill_amount = fields.Monetary(string='Bill Amount (excl. tax)', required=True,
                                  currency_field='currency_id')
    invoice_date = fields.Date(string='Bill Date', required=True, default=fields.Date.context_today)
    remarks = fields.Text(string='Remarks')

    @api.model
    def _default_milestone_number(self):
        """Next milestone: one per bill already raised on the AMC.

        Cancelled bills are excluded, matching the duplicate check in
        _check_sequential_billing -- a cancelled milestone frees its number to be
        raised again. AMC roles need no accounting access, hence the sudo.

        The move_type filter is what keeps this a count of bills: amc_id also tags the
        provision journal entries, so without it a year-long AMC would open the wizard
        at milestone Q13.
        """
        amc_id = self.env.context.get('default_amc_id')
        if not amc_id:
            return 1
        return self.env['account.move'].sudo().search_count([
            ('amc_id', '=', amc_id),
            ('move_type', 'in', ('in_invoice', 'in_refund')),
            ('state', '!=', 'cancel'),
        ]) + 1

    @api.depends('milestone_number')
    def _compute_milestone_label(self):
        for wizard in self:
            wizard.milestone_label = 'Q%s' % wizard.milestone_number if wizard.milestone_number else False

    @api.depends('amc_id')
    def _compute_site_id(self):
        """Default the site from the contract's purchase line, keeping a manual pick."""
        for wizard in self:
            wizard.site_id = wizard.site_id or (wizard.amc_id._amc_site() if wizard.amc_id else False)

    def _amc_term_lines(self):
        """Installments of the AMC's payment term, empty when the order carries none.

        account.payment.term.line._order is 'id', the same order _compute_terms walks,
        so installment N here is the one Odoo would bill Nth.
        """
        self.ensure_one()
        return self.amc_id.payment_term_id.line_ids

    def _amc_installment_amount(self, line, total, currency):
        """One installment's share of ``total``, net of tax."""
        amount = total * line.value_amount / 100.0 if line.value == 'percent' else line.value_amount
        return float_round(amount, precision_rounding=currency.rounding)

    def _amc_milestone_amount(self, milestone_number):
        """Amount to bill for a milestone, taken from the matching installment.

        The payment term decides both how many bills an AMC is split into and how much
        each one carries, so milestone N bills installment N. Odoo constrains percent
        lines to sum to 100%, and the last installment absorbs the rounding residue the
        way _compute_terms does, so the milestones add back up to the contract value
        rather than stranding a rounding difference against the provisions accrued on
        it. (They reconcile in contract currency only: provisions are accrued in
        company currency at the order date, so a foreign-currency order leaves an FX
        gap that no rounding rule here can close.)

        Falls back to the AMC's own even split (value / frequency) when the order
        carries no payment term.

        A 'fixed' installment is taken at face value: Odoo applies fixed term amounts
        to the tax-inclusive total, whereas this amount is net, so one may need
        adjusting by hand.
        """
        self.ensure_one()
        amc = self.amc_id
        lines = self._amc_term_lines()
        if not lines:
            return amc.amc_period_amount
        if not 1 <= milestone_number <= len(lines):
            return 0.0

        currency = amc.currency_id or self.env.company.currency_id
        total = amc.amc_charge_annum
        if milestone_number < len(lines):
            return self._amc_installment_amount(lines[milestone_number - 1], total, currency)
        booked = sum(self._amc_installment_amount(line, total, currency) for line in lines[:-1])
        return float_round(total - booked, precision_rounding=currency.rounding)

    @api.onchange('amc_id', 'milestone_number')
    def _onchange_default_bill_amount(self):
        # No 'not bill_amount' guard: the amount is milestone-specific, so moving to
        # another milestone has to re-derive it.
        for wizard in self:
            if wizard.amc_id:
                wizard.bill_amount = wizard._amc_milestone_amount(wizard.milestone_number)

    @api.onchange('is_advance')
    def _onchange_is_advance(self):
        for wizard in self:
            if wizard.is_advance:
                # An advance is billed before the service happens, so there are no
                # reports to attach yet. The periods it covers stay selectable -- that
                # is what records which part of the contract the advance was paid for.
                wizard.service_period_attachment_ids = [Command.clear()]

    # ------------------------------------------------------------------

    def _check_sequential_billing(self):
        """Milestone Qn may only be raised once Q(n-1) has left Draft."""
        self.ensure_one()
        Move = self.env['account.move'].sudo()
        if self.milestone_number <= 0:
            raise ValidationError(_("The payment milestone must be a positive number."))

        # Only when the order carries terms -- an AMC without them has no defined
        # number of bills and keeps billing milestone by milestone.
        term_lines = self._amc_term_lines()
        if term_lines and self.milestone_number > len(term_lines):
            raise UserError(_(
                "The payment term %(term)s splits this AMC into %(count)s bills, "
                "so milestone Q%(n)s cannot be raised.",
                term=self.amc_id.payment_term_id.display_name,
                count=len(term_lines), n=self.milestone_number,
            ))

        duplicate = Move.search([
            ('amc_id', '=', self.amc_id.id),
            ('amc_milestone_number', '=', self.milestone_number),
            ('state', '!=', 'cancel'),
        ], limit=1)
        if duplicate:
            raise UserError(_(
                "A bill for milestone Q%(n)s already exists on this AMC (%(bill)s).",
                n=self.milestone_number, bill=duplicate.display_name,
            ))

        if self.milestone_number == 1:
            return
        previous = Move.search([
            ('amc_id', '=', self.amc_id.id),
            ('amc_milestone_number', '=', self.milestone_number - 1),
            ('state', '!=', 'cancel'),
        ], limit=1)
        if not previous:
            raise UserError(_(
                "Cannot create the Q%(n)s bill: the Q%(prev)s bill has not been created yet.",
                n=self.milestone_number, prev=self.milestone_number - 1,
            ))
        if previous.state == 'draft':
            raise UserError(_(
                "Cannot create the Q%(n)s bill while the Q%(prev)s bill (%(bill)s) is still in "
                "Draft. Submit or post it first.",
                n=self.milestone_number, prev=self.milestone_number - 1, bill=previous.display_name,
            ))

    def _prepare_bill_values(self, provision_account):
        self.ensure_one()
        amc = self.amc_id
        # The bill is raised against the contract's own product, and reuses the taxes
        # of its purchase lines so input tax is booked as configured.
        # sudo on the lines: AMC roles raise these bills but need not read order lines.
        product = amc.product_id
        taxes = amc.sudo().purchase_line_ids.mapped('tax_ids')
        label = _('AMC %(milestone)s - %(name)s', milestone=self.milestone_label, name=amc.name or '')
        if self.is_advance:
            label = _('AMC Advance %(milestone)s - %(name)s',
                      milestone=self.milestone_label, name=amc.name or '')
        distribution = self.site_id._amc_analytic_distribution() if self.site_id else {}
        return {
            'move_type': 'in_invoice',
            'partner_id': amc.contractor_id.id,
            # 'date' is deliberately left out: account.move._compute_date derives the
            # accounting date from invoice_date through _get_accounting_date, which
            # rolls a bill dated inside a locked period into the first open one.
            # Forcing it here would land the bill in the closed period and block posting.
            'invoice_date': self.invoice_date,
            # AMC bills fall due on their accounting date rather than on any payment
            # term. The term is cleared explicitly because it precomputes from the
            # vendor's property_supplier_payment_term_id; left to default, a vendor
            # carrying terms would recompute the due date straight back off them.
            # With no term, _compute_needed_terms takes invoice_date_due as the
            # payable line's date_maturity verbatim. The term is only bypassed for
            # dates -- it still decides how much each milestone bills, see
            # _amc_milestone_amount.
            'invoice_payment_term_id': False,
            'invoice_date_due': self.invoice_date,
            'currency_id': (amc.currency_id or self.env.company.currency_id).id,
            'company_id': (amc.company_id or self.env.company).id,
            'invoice_origin': amc.po_id.name or False,
            'ref': label,
            # Matches how the provision entries are stamped in
            # _prepare_amc_provision_vals, so a bill drawing down the provision carries
            # the same site as the provision it settles.
            'amc_site_id': self.site_id.id or False,
            'amc_id': amc.id,
            'amc_po_id': amc.po_id.id,
            'amc_period_ids': [Command.set(self.service_period_ids.ids)],
            'amc_milestone_number': self.milestone_number,
            'amc_is_advance': self.is_advance,
            'amc_remarks': self.remarks,
            'invoice_line_ids': [Command.create({
                # product_id, account_id, tax_ids, name and price_unit are all
                # compute/store/readonly=False on account.move.line, so the values given
                # here win over what the product would otherwise derive. That is what
                # keeps the line on the provision account and on the order's taxes
                # rather than on the product's own expense account and supplier taxes.
                'product_id': product.id or False,
                'name': label,
                'quantity': 1.0,
                'price_unit': self.bill_amount,
                # Debiting the provision account draws down the accrued AMC provision.
                'account_id': provision_account.id,
                'tax_ids': [Command.set(taxes.ids)],
                'analytic_distribution': distribution or False,
                'amc_site_id': self.site_id.id or False,
            })],
        }

    def action_create_bill(self):
        self.ensure_one()
        amc = self.amc_id
        if amc.parent_amc_id:
            raise UserError(_("Vendor bills must be created from the Mother AMC."))
        if not amc.contractor_id:
            raise UserError(_("The AMC has no contractor set; a vendor bill cannot be created."))
        # Ahead of the amount check: a milestone past the last installment derives an
        # amount of zero, and "must be greater than zero" would hide the real reason.
        self._check_sequential_billing()
        if self.bill_amount <= 0:
            raise ValidationError(_("The bill amount must be greater than zero."))
        if self.is_advance and self.service_period_attachment_ids:
            raise ValidationError(_("An advance bill cannot carry service report attachments."))
        invalid = self.service_period_attachment_ids.filtered(
            lambda period: period.state not in ('closed', 'partially_serviced'))
        if invalid:
            raise ValidationError(_(
                "Only Done or Partially Serviced periods can be attached to a bill. Invalid: %s",
                ', '.join(invalid.mapped('display_name')),
            ))

        amc._amc_check_provision_accounts()
        provision_account = amc._amc_provision_account()
        # The wizard is the controlled path by which AMC roles raise these bills, so
        # the move itself is written as sudo; create_uid still records the real user.
        bill = self.env['account.move'].sudo().create(self._prepare_bill_values(provision_account))
        # The due date is seeded from the bill date, but _compute_date can roll the
        # accounting date forward past a locked period. Realign so the two always match.
        if bill.invoice_date_due != bill.date:
            bill.invoice_date_due = bill.date

        # Attachments: period service reports are copied (originals stay on the period,
        # and deleting the bill cannot take them away), plus the signed AMC contract.
        report_attachments = self.env['ir.attachment']
        for period in self.service_period_attachment_ids:
            report_attachments |= period._amc_copy_attachments_to(bill)
        amc._amc_copy_signed_contract_to(bill)
        if report_attachments:
            bill.amc_service_report_ids = [Command.set(report_attachments.ids)]

        if self.remarks:
            bill.message_post(body=self.remarks)
        amc.sudo().message_post(body=_(
            "Vendor bill %(bill)s created for milestone %(milestone)s.",
            bill=bill.display_name, milestone=self.milestone_label))

        # AMC roles can raise the bill through this wizard but may not read
        # account.move, so only hand them a form they are able to open.
        if not self.env['account.move'].has_access('read'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': _("Vendor bill %s created and sent to Finance.", bill.name or bill.ref),
                    'next': {'type': 'ir.actions.act_window_close'},
                },
            }
        return {
            'name': _('Vendor Bill'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': bill.id,
        }
