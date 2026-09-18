from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_round


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_amc_order = fields.Boolean(
        string='AMC Order', copy=False,
        help='Tick to buy an annual maintenance contract on this order. Its lines then '
             'accept service products only, and confirming the order raises one contract '
             'per line.')
    amc_site_id = fields.Many2one('amc.site', string='AMC Site', check_company=True, copy=False,
                                  help='Default site for the lines of this order.')
    amc_start_date = fields.Date(string='AMC Start Date', copy=False)
    amc_duration_months = fields.Integer(
        string='Duration (Months)', default=12, copy=False,
        help='Used to derive the end date. Set the end date directly to override it.')
    amc_end_date = fields.Date(string='AMC End Date', compute='_compute_amc_end_date',
                               store=True, readonly=False, copy=False)
    amc_frequency_number = fields.Integer(
        string='Number of Service Periods', default=1, copy=False,
        help='How many service periods each contract is cut into: 4 for quarterly '
             'servicing of a one year contract, 12 for monthly.')

    amc_ids = fields.One2many('amc.contract', 'po_id', string='AMC Contracts')
    amc_mother_ids = fields.One2many('amc.contract', 'po_id', string='Mother AMCs',
                                     domain=[('parent_amc_id', '=', False)])
    amc_count = fields.Integer(string='AMC Contract Count', compute='_compute_amc_count')
    amc_is_signed = fields.Boolean(string='AMC Signed', compute='_compute_amc_is_signed')
    amc_signed_contract = fields.Binary(string='Signed AMC Contract', attachment=True, copy=False)
    amc_signed_contract_filename = fields.Char(string='Signed AMC Contract Filename', copy=False)

    amc_provision_move_ids = fields.One2many('account.move', 'amc_po_id',
                                             string='AMC Provision Entries',
                                             domain=[('amc_provision_type', '!=', False)])
    amc_provision_move_count = fields.Integer(string='AMC Provisions',
                                              compute='_compute_amc_provision_move_count')

    # ------------------------------------------------------------------
    # Computes and constraints
    # ------------------------------------------------------------------

    @api.depends('amc_start_date', 'amc_duration_months')
    def _compute_amc_end_date(self):
        """Last day covered by the contract: the day before the duration's anniversary.

        A twelve month AMC starting 15 Jan 2025 therefore ends 14 Jan 2026, which is
        what makes _amc_whole_months read the span back as a whole number of months
        and lets the periods be cut on the calendar.
        """
        for order in self:
            if order.amc_start_date and order.amc_duration_months > 0:
                order.amc_end_date = order.amc_start_date + relativedelta(
                    months=order.amc_duration_months, days=-1)
            else:
                order.amc_end_date = order.amc_end_date

    @api.depends('amc_ids.parent_amc_id')
    def _compute_amc_count(self):
        for order in self:
            order.amc_count = len(order.amc_ids.filtered(lambda amc: not amc.parent_amc_id))

    @api.depends('amc_mother_ids.is_signed')
    def _compute_amc_is_signed(self):
        for order in self:
            mothers = order.amc_mother_ids
            order.amc_is_signed = bool(mothers) and all(mothers.mapped('is_signed'))

    @api.depends('amc_provision_move_ids')
    def _compute_amc_provision_move_count(self):
        for order in self:
            order.amc_provision_move_count = len(order.amc_provision_move_ids)

    @api.constrains('is_amc_order', 'order_line')
    def _check_amc_service_lines(self):
        """An AMC is a service bought over time; a storable line cannot be provisioned."""
        for order in self:
            if not order.is_amc_order:
                continue
            wrong = order.order_line.filtered(
                lambda line: not line.display_type and line.product_id
                and line.product_id.type != 'service')
            if wrong:
                raise ValidationError(_(
                    "An AMC order accepts service products only. Remove or replace: %s",
                    ', '.join(wrong.mapped('product_id.display_name')),
                ))

    @api.onchange('is_amc_order')
    def _onchange_is_amc_order(self):
        """Seed the contract dates so the AMC block is not empty when it appears."""
        if self.is_amc_order and not self.amc_start_date:
            self.amc_start_date = fields.Date.context_today(self)

    @api.onchange('amc_site_id')
    def _onchange_amc_site_id(self):
        """Push the header site down to the lines that carry none of their own."""
        if self.amc_site_id:
            for line in self.order_line:
                if not line.amc_site_id:
                    line.amc_site_id = self.amc_site_id

    # ------------------------------------------------------------------
    # Contract creation
    # ------------------------------------------------------------------

    def _amc_check_ready_for_contracts(self):
        """Everything contract creation needs, checked before anything is written."""
        self.ensure_one()
        if not self.amc_start_date or not self.amc_end_date:
            raise UserError(_("Set the AMC start and end dates before confirming this order."))
        if self.amc_start_date > self.amc_end_date:
            raise UserError(_("The AMC start date cannot be after its end date."))
        if self.amc_frequency_number <= 0:
            raise UserError(_("The number of service periods must be a positive integer."))
        if not self.order_line.filtered(lambda line: not line.display_type):
            raise UserError(_("An AMC order needs at least one line."))

    def _prepare_amc_contract_vals(self, line):
        """Values for the Mother AMC raised from one order line.

        The contract value is taken net of tax: provisions accrue an expense, and the
        vendor bills that draw the provision down are raised net of tax as well, so
        billing an AMC in full lands exactly on the provision accrued for it.
        """
        self.ensure_one()
        return {
            'name': line.name or line.product_id.display_name,
            'company_id': self.company_id.id,
            'site_id': (line.amc_site_id or self.amc_site_id).id or False,
            'po_id': self.id,
            'contractor_id': self.partner_id.id,
            'amc_charge_annum': line.price_subtotal,
            'frequency_number': self.amc_frequency_number,
            'start_date': self.amc_start_date,
            'end_date': self.amc_end_date,
            'expiry_time': max((self.amc_end_date - fields.Date.context_today(self)).days + 1, 0),
            'state': 'draft',
        }

    def _amc_create_contracts(self):
        """Raise one Mother AMC per order line and cut each into its service periods."""
        contracts = self.env['amc.contract']
        for order in self:
            if not order.is_amc_order:
                continue
            order._amc_check_ready_for_contracts()
            for line in order.order_line:
                if line.display_type or line.amc_id:
                    continue
                contract = contracts.create(order._prepare_amc_contract_vals(line))
                contract.action_activate_parent_amc()
                line.amc_id = contract.id
                contracts |= contract
        return contracts

    def button_confirm(self):
        """Validate the AMC terms at confirmation time.

        The contracts themselves are raised in button_approve, which is the only point
        both approval paths pass through: with double validation switched on,
        button_confirm leaves the order in 'to approve' and someone else approves it
        later. Checking here anyway means the buyer is told about a missing date while
        the order is still theirs to fix.
        """
        for order in self.filtered(lambda o: o.is_amc_order and o.state in ('draft', 'sent')):
            order._amc_check_ready_for_contracts()
        return super().button_confirm()

    def button_approve(self, force=False):
        res = super().button_approve(force=force)
        # super() filters out the orders approval is not allowed for, so the state
        # check is what tells which ones actually moved.
        self.filtered(
            lambda order: order.is_amc_order and order.state == 'purchase'
        )._amc_create_contracts()
        return res

    def _amc_check_no_signed_contract(self, action_label):
        """Refuse an order-level action that would strand signed contracts.

        Once an AMC is signed its provision entries exist and may be posted, so
        unwinding the order behind them has to be a deliberate accounting act rather
        than a side effect of a button.
        """
        signed = self.filtered(lambda order: order.amc_mother_ids.filtered('is_signed'))
        if signed:
            raise UserError(_(
                "Cannot %(action)s %(orders)s: their AMCs are already signed and carry "
                "provision entries. Terminate the contracts and reverse their entries first.",
                action=action_label, orders=', '.join(signed.mapped('display_name')),
            ))

    def button_cancel(self):
        self._amc_check_no_signed_contract(_("cancel"))
        res = super().button_cancel()
        # A cancelled order leaves no live contract behind it.
        self.amc_mother_ids.filtered(
            lambda contract: contract.state != 'terminated').action_terminate()
        return res

    def button_draft(self):
        self._amc_check_no_signed_contract(_("reset to draft"))
        return super().button_draft()

    # ------------------------------------------------------------------
    # Signing
    # ------------------------------------------------------------------

    def _amc_mother_contracts(self):
        """Mother AMCs of this order (one per line carrying an AMC)."""
        self.ensure_one()
        return self.env['amc.contract'].search([
            ('po_id', '=', self.id),
            ('parent_amc_id', '=', False),
        ])

    def _amc_signed_contract_attachment(self):
        """The ir.attachment backing amc_signed_contract.

        Read as sudo: the users raising the AMC vendor bills that copy this document
        onto the bill hold no attachment privileges of their own.
        """
        self.ensure_one()
        return self.env['ir.attachment'].sudo().search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('res_field', '=', 'amc_signed_contract'),
        ], limit=1)

    def action_mark_as_signed(self):
        """Sign every Mother AMC of this order in one act, then raise the provisions.

        Signing lives on the order rather than on the individual contracts because an
        order spanning several sites carries one Mother AMC per site, and the monthly
        provisioning consolidates them into a single entry per month.
        """
        self.ensure_one()
        contracts = self._amc_mother_contracts()
        if not contracts:
            raise UserError(_("This purchase order carries no AMC to mark as signed."))
        unsigned = contracts.filtered(lambda contract: not contract.is_signed)
        if not unsigned:
            raise UserError(_("The AMCs of this purchase order are already marked as signed."))
        unsigned.write({
            'is_signed': True,
            'signed_date': fields.Date.context_today(self),
        })
        moves = self._amc_generate_provision_moves()
        self.message_post(body=_(
            "AMC marked as signed. %(contracts)s contract(s) signed, %(moves)s provision "
            "entry(ies) created in draft.",
            contracts=len(unsigned), moves=len(moves) if moves else 0))
        return True

    # ------------------------------------------------------------------
    # Monthly provisioning
    # ------------------------------------------------------------------

    def _amc_company_currency(self):
        return self.company_id.currency_id or self.env.company.currency_id

    def _amc_contract_value(self, contract):
        """Contract value expressed in company currency.

        Provision entries book plain debit/credit, which Odoo always reads as company
        currency, so an order raised in another currency is converted here rather than
        leaving the two out of step.
        """
        company_currency = self._amc_company_currency()
        contract_currency = contract.currency_id or company_currency
        value = contract.amc_charge_annum
        if contract_currency and contract_currency != company_currency:
            value = contract_currency._convert(
                value, company_currency, self.company_id or self.env.company,
                self.date_order.date() if self.date_order else fields.Date.context_today(self))
        return value

    def _amc_monthly_breakdown(self, contract):
        """Split a Mother AMC value over the calendar months it spans.

        Returns an ordered list of (month_start, amount) in company currency. The daily
        rate is the contract value divided by the inclusive contract duration; each
        month gets the daily rate times the number of contract days falling inside it.
        Rounding residue is pushed onto the last month so the months always add up to
        the total.
        """
        total_days = (contract.end_date - contract.start_date).days + 1
        if total_days <= 0:
            return []
        total_value = self._amc_contract_value(contract)
        daily_rate = total_value / total_days
        rounding = self._amc_company_currency().rounding

        breakdown = []
        cursor = contract.start_date.replace(day=1)
        while cursor <= contract.end_date:
            month_end = cursor + relativedelta(months=1, days=-1)
            overlap_start = max(cursor, contract.start_date)
            overlap_end = min(month_end, contract.end_date)
            days = (overlap_end - overlap_start).days + 1
            breakdown.append([cursor, float_round(daily_rate * days, precision_rounding=rounding)])
            cursor += relativedelta(months=1)

        if breakdown:
            residue = total_value - sum(amount for _month, amount in breakdown)
            breakdown[-1][1] = float_round(breakdown[-1][1] + residue, precision_rounding=rounding)
        return [(month, amount) for month, amount in breakdown]

    def _amc_generate_provision_moves(self):
        """Create one draft provision journal entry per not-yet-provisioned month.

        An order may carry several Mother AMCs (one per line / site); they are
        consolidated into a single entry per month with one debit and one credit line
        per site, which is what keeps the one-entry-per-order-per-month rule
        satisfiable. Signing is a single order-level act, so every Mother AMC on the
        order is signed together and they all land in one shared set of monthly
        entries. The check below is kept as a guard for any other caller reaching this
        method with a partly signed order.

        Existing provision entries are never edited or replaced, so a month that
        already has one (regular or catch-up) is skipped outright. This only matters
        for a Mother AMC added to the order *after* provisioning had already started
        for its siblings: it joins in from the first month that has no entry yet, and
        the accountant handles the missed earlier months with a manual adjustment.

        Months that already ended before the current month are folded together with the
        current month into a single catch-up entry (delayed signature case).
        """
        self.ensure_one()
        contracts = self._amc_mother_contracts()
        if not contracts:
            return False
        # Wait until every Mother AMC on the order is signed, otherwise the
        # consolidated entry would be missing site lines that can never be added later.
        if any(not contract.is_signed for contract in contracts):
            return False
        # Provision entries are system bookkeeping: the users triggering them need no
        # accounting access, so every account.move touch here runs as sudo.
        Move = self.env['account.move'].sudo()
        provisioned_months = set(Move.search([
            ('amc_po_id', '=', self.id),
            ('amc_provision_type', 'in', ('regular', 'catchup')),
        ]).mapped('amc_provision_month'))

        # A zero contract value or a missing date would silently produce no entries at
        # all, which is the worst failure mode for an accounting routine -- refuse instead.
        unusable = contracts.filtered(
            lambda c: not c.start_date or not c.end_date or c.end_date < c.start_date
            or float_is_zero(self._amc_contract_value(c),
                             precision_rounding=self._amc_company_currency().rounding))
        if unusable:
            raise UserError(_(
                "AMC provisions cannot be generated for %(names)s: the contract value must be "
                "greater than zero and the start/end dates must be set correctly.",
                names=', '.join(unusable.mapped('display_name')),
            ))

        # Resolve the configuration and every contract's product expense/provision
        # accounts up front so a missing account fails before any record is written,
        # rather than part-way through the month loop.
        Move._get_amc_journal()
        contracts._amc_check_expense_accounts()
        contracts._amc_check_provision_accounts()
        today = fields.Date.context_today(self)
        current_month = today.replace(day=1)

        buckets = {}
        folded_months = set()
        for contract in contracts:
            for month, amount in self._amc_monthly_breakdown(contract):
                key = month if month >= current_month else current_month
                if key != month:
                    folded_months.add(key)
                buckets.setdefault(key, {})
                buckets[key][contract] = buckets[key].get(contract, 0.0) + amount

        company_currency = self._amc_company_currency()
        move_vals = []
        for month in sorted(buckets):
            if month in provisioned_months:
                continue
            contract_amounts = {c: a for c, a in buckets[month].items()
                                if not float_is_zero(a, precision_rounding=company_currency.rounding)}
            if not contract_amounts:
                continue
            provision_type = 'catchup' if month in folded_months else 'regular'
            month_end = month + relativedelta(months=1, days=-1)
            accounting_date = min(month_end, max(c.end_date for c in contract_amounts))
            label = _('AMC Catch-Up Provision') if provision_type == 'catchup' \
                else _('AMC Monthly Provision')
            reference = '%s - %s - %s' % (label, self.name, month.strftime('%b %Y'))

            move_vals.append(Move._prepare_amc_provision_vals(
                self, reference, provision_type, month, accounting_date, contract_amounts))
        return Move.create(move_vals)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def action_view_amc(self):
        self.ensure_one()
        contracts = self._amc_mother_contracts()
        action = {
            'name': _('AMC Contracts'),
            'type': 'ir.actions.act_window',
            'res_model': 'amc.contract',
            'context': {'create': False},
        }
        if len(contracts) == 1:
            action.update({'view_mode': 'form', 'res_id': contracts.id})
        else:
            action.update({
                'view_mode': 'list,form',
                'domain': [('po_id', '=', self.id), ('parent_amc_id', '=', False)],
            })
        return action

    def action_view_amc_provisions(self):
        self.ensure_one()
        return {
            'name': _('AMC Provision Entries'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': self.env['account.move']._amc_provision_domain(po=self),
            'context': {'create': False},
        }


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    amc_id = fields.Many2one('amc.contract', string='AMC', copy=False, ondelete='set null',
                             help='Contract this line belongs to. Set automatically on the lines '
                                  'of an AMC order, and available on any other order to book a '
                                  'follow-up purchase against an existing contract.')
    amc_site_id = fields.Many2one('amc.site', string='AMC Site', check_company=True,
                                  compute='_compute_amc_site_id', store=True, readonly=False)
    is_amc_order = fields.Boolean(related='order_id.is_amc_order')

    @api.depends('order_id.amc_site_id')
    def _compute_amc_site_id(self):
        """Default the line site from the order header, keeping any value set by hand.

        Every record is assigned because the field is stored; falling back to the
        current value is what stops changing the header from wiping a manual entry.
        """
        for line in self:
            line.amc_site_id = line.amc_site_id or line.order_id.amc_site_id

    @api.constrains('product_id')
    def _check_amc_service_product(self):
        for line in self:
            if line.display_type or not line.order_id.is_amc_order or not line.product_id:
                continue
            if line.product_id.type != 'service':
                raise ValidationError(_(
                    "%s is not a service product and cannot be put on an AMC order.",
                    line.product_id.display_name,
                ))
