from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError


class PettyCashAdvance(models.Model):
    _name = 'petty.cash.advance'
    _description = 'Petty Cash Advance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char('Reference', required=True, copy=False, readonly=True, default='New')
    date = fields.Date('Advance Date', required=True, default=fields.Date.context_today, tracking=True)
    request_id = fields.Many2one('petty.cash.request', 'Cash Request',
                                 domain="[('employee_id', '=', employee_id),('state', '=', 'approved'), ('company_id', '=', company_id)]")
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True,
                                  default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)],
                                                                                      limit=1),
                                  tracking=True)
    line_ids = fields.One2many('petty.cash.advance.line', 'advance_id', 'Purpose Lines', copy=True)
    requested_amount = fields.Monetary('Request Amount', tracking=True)
    amount = fields.Monetary('Advance Amount', compute='_compute_amount', store=True, tracking=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env.company)
    purpose = fields.Text('Purpose', required=False)
    expected_settlement_date = fields.Date('Expected Settlement Date', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('partially_settled', 'Partially Settled'),
        ('settled', 'Settled'),
        ('cancelled', 'Cancelled')
    ], default='draft', tracking=True)
    is_returned = fields.Boolean('Is Returned', default=False, readonly=True,
                                 help='True if this advance was returned without expenses')
    settlement_ids = fields.Many2many('petty.cash.settlement', 'advance_settlement_rel',
                                      'advance_id', 'settlement_id',
                                      string='Settlements', readonly=True)
    settlement_line_ids = fields.One2many('petty.cash.advance.settlement.line', 'advance_id',
                                          string='Settlement Lines', readonly=True)
    settlement_id = fields.Many2one('petty.cash.settlement', 'Settlement', readonly=True)

    # ── ANALYTICS NOTE ────────────────────────────────────────────────────────
    # Both `settled_amount` and `balance` carry store=True so that
    # _compute_top_outstanding_employees() can aggregate them via read_group /
    # direct search without loading every record into Python memory.
    # If you ever remove store=True, the dashboard's top-employees chart will
    # still work (it uses search + Python grouping) but will be slower on large
    # datasets.  Keep store=True as the recommended setting.
    # ─────────────────────────────────────────────────────────────────────────
    settled_amount = fields.Monetary(
        'Settled Amount',
        compute='_compute_settled',
        store=True,   # stored so SQL-level aggregation is possible
    )
    balance = fields.Monetary(
        'Balance',
        compute='_compute_settled',
        store=True,   # stored — required for domain ("balance", ">", 0) in searches
                      # and for future read_group("balance:sum") aggregation
    )
    notes = fields.Text('Notes')

    employee_advance_account_id = fields.Many2one(
        'account.account',
        'Employee Advance Account', domain="[('company_ids', 'in', [company_id])]",
        required=True)
    move_id = fields.Many2one('account.move', 'Journal Entry', readonly=True, copy=False)
    payment_id = fields.Many2one('account.payment', 'Payment', readonly=True, copy=False)
    return_move_id = fields.Many2one('account.move', 'Return Journal Entry', readonly=True, copy=False,
                                     help='Journal entry created when advance is returned')

    journal_id = fields.Many2one('account.journal', 'Journal', required=True, domain="[('type', 'in', ['cash']), ('company_id', '=', company_id)]")
    vessel_id = fields.Many2one(
        "account.analytic.account",
        string="Cost Center", required=True,
        domain="[('plan_id.name', 'in', ['Vessels', 'Cost Centers']), ('company_id', 'in', [False, company_id])]"
    )
    signed_advance_document = fields.Binary(attachment=True)
    signed_advance_document_name = fields.Char('Document Name')

    @api.depends('line_ids.amount')
    def _compute_amount(self):
        for record in self:
            record.amount = sum(record.line_ids.mapped('amount'))

    @api.onchange('request_id')
    def _onchange_request_id(self):
        if self.request_id:
            self.employee_id = self.request_id.employee_id
            self.requested_amount = self.request_id.amount
            self.purpose = self.request_id.purpose
            self.vessel_id = self.request_id.vessel_id

            # Copy purpose lines from request
            line_vals = []
            for line in self.request_id.line_ids:
                line_vals.append((0, 0, {
                    'purpose': line.purpose,
                    'amount': line.amount,
                }))
            self.line_ids = line_vals

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("petty.cash.advance") or _("New")
        return super().create(vals_list)

    @api.depends('settlement_line_ids', 'settlement_line_ids.settled_amount',
                 'settlement_line_ids.settlement_id.state', 'amount')
    def _compute_settled(self):
        for rec in self:
            # Sum all posted settlement amounts
            posted_settlements = rec.settlement_line_ids.filtered(
                lambda l: l.settlement_id.state == 'posted'
            )
            rec.settled_amount = sum(posted_settlements.mapped('settled_amount'))
            rec.balance = rec.amount - rec.settled_amount

    def _check_manager(self):
        """Approval / payment actions require the Petty Cash Manager group."""
        if not self.env.user.has_group('petty_cash.group_petty_cash_manager'):
            raise AccessError(_(
                'Only a Petty Cash Manager can approve or pay a cash advance.'
            ))

    def action_approve(self):
        self._check_manager()
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft advances can be approved.'))
            if rec.amount <= 0:
                raise UserError(_('Advance amount must be greater than zero.'))
        self.write({'state': 'approved'})

    def action_pay(self):
        self._check_manager()
        for rec in self:
            if rec.state != 'approved':
                raise UserError(_('Only approved advances can be paid.'))
            # Validate signed advance document is attached
            if not rec.signed_advance_document:
                raise UserError(_('Please attach a signed advance document before processing payment.'))

            # Get employee partner
            related_partner = rec.employee_id.work_contact_id | rec.employee_id.user_id.partner_id
            if not related_partner:
                raise UserError(_('Employee must have a related user and partner.'))

            # Prepare analytic distribution if vessel_id is set
            analytic_distribution = {}
            if rec.vessel_id:
                analytic_distribution = {str(rec.vessel_id.id): 100}

            # Create account.payment record. Posting is done sudo() because the
            # petty-cash groups intentionally do not carry full accounting rights;
            # the manager check above is the authorization gate.
            payment_vals = {
                'partner_id': related_partner.id,
                'amount': rec.amount,
                'journal_id': rec.journal_id.id,
                'date': rec.date,
                'memo': rec.purpose,
                'payment_type': 'outbound',  # Payment going out to employee
                'partner_type': 'supplier',  # Employee is treated as supplier for advance
                'company_id': rec.company_id.id,
            }

            payment = self.env['account.payment'].sudo().create(payment_vals)

            # Post the payment
            payment.action_post()

            # Add analytic distribution to payment move lines if vessel_id is set
            if analytic_distribution and payment.move_id:
                for line in payment.move_id.line_ids:
                    line.write({'analytic_distribution': analytic_distribution})

            # Store the payment and journal entry reference
            rec.payment_id = payment.id
            rec.move_id = payment.move_id.id
            rec.state = 'paid'

            if rec.request_id:
                rec.request_id.write({
                    'state': 'issued',
                    'advance_id': rec.id
                })

    def action_cancel(self):
        for rec in self:
            if rec.state in ('settled', 'partially_settled'):
                raise UserError(_('A settled or partially settled advance cannot be cancelled.'))
            if rec.state == 'paid' and not self.env.user.has_group('petty_cash.group_petty_cash_manager'):
                raise AccessError(_('Only a Petty Cash Manager can cancel a paid advance.'))
        self.write({'state': 'cancelled'})

    def action_open_payment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'res_id': self.payment_id.id,
            'target': 'current',
        }

    def action_open_return_journal(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Return Journal Entry',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.return_move_id.id,
            'target': 'current',
        }
