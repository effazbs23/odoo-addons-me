from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError, AccessError


class PettyCashSettlement(models.Model):
    _name = 'petty.cash.settlement'
    _description = 'Petty Cash Settlement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char('Reference', required=True, copy=False, readonly=True, default='New')
    date = fields.Date('Settlement Date', required=True, default=fields.Date.context_today, tracking=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True,
                                  default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)],
                                                                                      limit=1),
                                  tracking=True)

    # Multiple advances support
    advance_line_ids = fields.One2many('petty.cash.advance.settlement.line', 'settlement_id',
                                       string='Advance Lines', copy=False)
    total_advance_amount = fields.Monetary('Total Advance Amount', compute='_compute_advance_totals', store=True)

    # Keep old field for backward compatibility but make it computed
    advance_id = fields.Many2one('petty.cash.advance', 'Related Advance',
                                 compute='_compute_advance_id', store=False,
                                 help='Deprecated: Shows first advance if only one exists')
    advance_journal_id = fields.Many2one('account.journal', 'Advance Journal',
                                         compute='_compute_advance_journal', store=True, readonly=False,
                                         help='Journal for settlement. Auto-filled for with_advance, manual for without_advance')

    line_ids = fields.One2many(
        'hr.expense',
        compute='_compute_expense_lines',
        string='Expense Lines',
        help='Expenses from HR Expense module for this employee'
    )
    total_amount = fields.Monetary('Total Amount', compute='_compute_total', store=True)
    advance_amount = fields.Monetary('Settlement Amount', related='total_advance_amount', readonly=True,
                                     help='Total amount being settled from advances')
    refund_amount = fields.Monetary('Refund to Company', compute='_compute_refund', store=True)
    additional_payment = fields.Monetary('Additional Payment to Employee', compute='_compute_refund', store=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env.company)
    move_id = fields.Many2one('account.move', 'Journal Entry', readonly=True, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled')
    ], default='draft', tracking=True)

    settlement_type = fields.Selection([
        ('with_advance', 'Settle with Advance'),
        ('without_advance', 'Bill Settlement')
    ], string='Settlement Type', default='with_advance', required=True, tracking=True,
       help='Choose whether to settle against an advance or settle bill directly without advance')

    settlement_mode = fields.Selection([
        ('partial', 'Partial Settlement'),
        ('full', 'Full Settlement'),
        ('return', 'Return Advance')
    ], string='Settlement Mode', default='partial', required=True, tracking=True,
       help='Partial: Only adjust bill amount and keep remaining balance. Full: Settle full advance amount with cash adjustment if needed. Return: Return unused advance without bill')

    notes = fields.Text('Notes')

    employee_advance_account_id = fields.Many2one('account.account', 'Employee Advance Account',
                                                  compute='_compute_advance_account', store=True)
    petty_cash_account_id = fields.Many2one('account.account', 'Petty Cash Account')

    # Tagged Bill for Settlement (Only one bill allowed)
    tagged_bill_id = fields.Many2one(
        'account.move',
        string='Tagged Bill',
        help='Bill tagged for settlement (only one bill per settlement)',
        domain="[('id', 'in', available_bill_ids)]"
    )

    # Available Bills (computed, not stored)
    available_bill_ids = fields.Many2many(
        'account.move',
        compute='_compute_available_bills',
        string='Available Bills',
        help='Bills available for tagging: same partner as employee, unpaid, and either spot order type or created from expense'
    )

    # Payment record
    payment_id = fields.Many2one('account.payment', 'Payment', readonly=True, copy=False)

    vessel_id = fields.Many2one(
        "account.analytic.account",
        string="Cost Center", required=True,
        domain="[('plan_id.name', 'in', ['Vessels', 'Cost Centers']), ('company_id', 'in', [False, company_id])]"
    )
    signed_settlement_document = fields.Binary(attachment=True, string='Signed Settlement Document')
    signed_settlement_document_name = fields.Char('Document Name')


    @api.depends('employee_id')
    def _compute_available_bills(self):
        """
        Compute bills available for tagging based on:
        1. Partner same as settlement employee
        2. Not paid (payment_state = 'not_paid')
        3. Posted state
        """
        for rec in self:
            related_partner = rec.employee_id.work_contact_id | rec.employee_id.user_id.partner_id
            if rec.employee_id and related_partner:
                # Base domain for bills
                domain = [
                    ('move_type', '=', 'in_invoice'),
                    ('partner_id', '=', related_partner.id),
                    ('payment_state', '=', 'not_paid'),
                    ('state', '=', 'posted')
                ]

                bills = self.env['account.move'].search(domain)

                rec.available_bill_ids = bills
            else:
                rec.available_bill_ids = False

    @api.depends('employee_id')
    def _compute_expense_lines(self):
        for rec in self:
            if rec.employee_id:
                # Fetch expenses from hr.expense for this employee
                expenses = self.env['hr.expense'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    # You can add more filters here if needed, e.g.:
                    ('state', '=', 'approved'),
                    # ('payment_mode', '=', 'own_account'),
                ])
                rec.line_ids = expenses
            else:
                rec.line_ids = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('petty.cash.settlement') or _('New')
        return super().create(vals_list)

    @api.depends('advance_line_ids', 'advance_line_ids.settled_amount')
    def _compute_advance_totals(self):
        """Compute total advance amount from all advance lines"""
        for rec in self:
            rec.total_advance_amount = sum(rec.advance_line_ids.mapped('settled_amount'))

    @api.depends('advance_line_ids', 'advance_line_ids.advance_id')
    def _compute_advance_id(self):
        """For backward compatibility: returns first advance if only one exists"""
        for rec in self:
            if len(rec.advance_line_ids) == 1:
                rec.advance_id = rec.advance_line_ids[0].advance_id
            else:
                rec.advance_id = False

    @api.depends('advance_line_ids', 'advance_line_ids.advance_id.journal_id', 'settlement_type')
    def _compute_advance_journal(self):
        """Get journal from first advance (they should all use same journal) for with_advance type.
        For without_advance type, journal must be manually selected."""
        for rec in self:
            if rec.settlement_type == 'with_advance':
                if rec.advance_line_ids:
                    rec.advance_journal_id = rec.advance_line_ids[0].advance_id.journal_id
                else:
                    rec.advance_journal_id = False
            # For 'without_advance', keep the manually set value (don't compute)

    @api.onchange('settlement_type')
    def _onchange_settlement_type(self):
        """Clear journal when switching to without_advance to force manual selection"""
        if self.settlement_type == 'without_advance':
            self.advance_journal_id = False

    @api.onchange('settlement_mode')
    def _onchange_settlement_mode(self):
        """When switching to full mode, set all advance lines to full balance.
        When switching to return mode, set all advance lines to full advance amount and clear tagged bill."""
        if self.settlement_mode == 'full':
            for line in self.advance_line_ids:
                if line.advance_id:
                    line.settled_amount = line.advance_id.balance
        elif self.settlement_mode == 'return':
            # Clear bill for return mode as no bill is needed
            self.tagged_bill_id = False
            # Set return amount to full advance amount (not just balance)
            for line in self.advance_line_ids:
                if line.advance_id:
                    line.settled_amount = line.advance_id.amount  # Full advance amount

    @api.depends('advance_line_ids', 'advance_line_ids.advance_id.employee_advance_account_id')
    def _compute_advance_account(self):
        """Get employee advance account from first advance (they should all use same account)"""
        for rec in self:
            if rec.advance_line_ids:
                rec.employee_advance_account_id = rec.advance_line_ids[0].advance_id.employee_advance_account_id
            else:
                rec.employee_advance_account_id = False

    @api.depends('tagged_bill_id', 'tagged_bill_id.amount_total')
    def _compute_total(self):
        for rec in self:
            rec.total_amount = rec.tagged_bill_id.amount_total if rec.tagged_bill_id else 0.0

    @api.depends('total_amount', 'advance_amount')
    def _compute_refund(self):
        for rec in self:
            difference = (rec.advance_amount or 0.0) - rec.total_amount
            if difference > 0:
                rec.refund_amount = difference
                rec.additional_payment = 0.0
            else:
                rec.refund_amount = 0.0
                rec.additional_payment = abs(difference)

    def _check_cashier(self):
        """Submitting a settlement requires at least the Cashier group."""
        if not self.env.user.has_group('petty_cash.group_petty_cash_cashier'):
            raise AccessError(_('Only a Petty Cash Cashier or Manager can process settlements.'))

    def _check_manager(self):
        """Posting a settlement (money movement) requires the Manager group."""
        if not self.env.user.has_group('petty_cash.group_petty_cash_manager'):
            raise AccessError(_('Only a Petty Cash Manager can post a settlement.'))

    @api.constrains('advance_line_ids')
    def _check_settled_amounts(self):
        """Settled amount per advance line must be positive and not exceed the
        advance balance, preventing over-settlement / negative journal entries."""
        for rec in self:
            for line in rec.advance_line_ids:
                if line.settled_amount < 0:
                    raise ValidationError(_('Settled amount cannot be negative.'))
                advance = line.advance_id
                if advance and rec.settlement_mode != 'return' \
                        and line.settled_amount > advance.amount + 0.01:
                    raise ValidationError(_(
                        'Settled amount (%(settled)s) for advance %(name)s cannot '
                        'exceed the advance amount (%(amount)s).'
                    ) % {
                        'settled': line.settled_amount,
                        'name': advance.name,
                        'amount': advance.amount,
                    })

    def action_submit(self):
        self._check_cashier()
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft settlements can be submitted.'))
        # Bill not required for return mode
        if self.settlement_mode != 'return' and not self.tagged_bill_id:
            raise UserError(_('Please tag a bill for settlement.'))

        # Advance lines only required for 'with_advance' settlement type
        if self.settlement_type == 'with_advance' and not self.advance_line_ids:
            raise UserError(_('Please add at least one advance to settle.'))

        self.state = 'submitted'


    def action_post(self):
        self._check_manager()
        for rec in self:
            if rec.state != 'submitted':
                raise UserError(_('Only submitted settlements can be posted.'))
            # Validate signed settlement document is attached
            if not rec.signed_settlement_document:
                raise UserError(_('Please attach a signed settlement document before posting.'))

            # Bill not required for return mode
            if rec.settlement_mode != 'return' and not rec.tagged_bill_id:
                raise UserError(_('Please tag a bill for settlement.'))

            # Validate advance lines only for 'with_advance' settlement type
            if rec.settlement_type == 'with_advance' and not rec.advance_line_ids:
                raise UserError(_('Please add at least one advance to settle.'))

            # Validate journal is selected for 'without_advance' settlement type
            if rec.settlement_type == 'without_advance' and not rec.advance_journal_id:
                raise UserError(_('Please select a journal for settlement.'))

            # Route to appropriate posting method based on settlement type and mode
            if rec.settlement_type == 'with_advance':
                if rec.settlement_mode == 'return':
                    rec._post_return_advance()
                else:
                    rec._post_with_advance()
            else:
                rec._post_without_advance()

    # ========== Helper Methods ==========

    def _get_employee_partner(self):
        """Get employee partner or raise error if not found"""
        related_partner = self.employee_id.work_contact_id | self.employee_id.user_id.partner_id
        if not related_partner:
            raise UserError(_('Employee must have a related user and partner.'))
        return related_partner

    def _get_analytic_distribution(self):
        """Get analytic distribution based on vessel_id"""
        if self.vessel_id:
            return {str(self.vessel_id.id): 100}
        return {}

    def _get_payable_account(self):
        """Get payable account from tagged bill"""
        if not self.tagged_bill_id:
            raise UserError(_('No tagged bill found.'))

        payable_account = self.tagged_bill_id.line_ids.filtered(
            lambda l: l.account_id.account_type == 'liability_payable'
        ).account_id

        if not payable_account:
            raise UserError(_('No payable account found in tagged bill.'))

        return payable_account

    def _get_cash_account(self):
        """Get cash/bank account from advance journal"""
        if not self.advance_journal_id:
            # Try to find a cash journal
            cash_journal = self.env['account.journal'].search([
                ('type', '=', 'cash'),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            if not cash_journal:
                raise UserError(_('Please configure a cash journal or select an advance journal.'))
            self.advance_journal_id = cash_journal.id

        cash_account = self.advance_journal_id.default_account_id
        if not cash_account:
            raise UserError(_('Journal must have a default account configured.'))

        return cash_account

    def _create_journal_line(self, name, account_id, debit, credit, partner_id, analytic_distribution=None):
        """Create a journal entry line with optional analytic distribution"""
        line_vals = {
            'name': name,
            'account_id': account_id,
            'debit': debit,
            'credit': credit,
            'partner_id': partner_id,
        }
        if analytic_distribution:
            line_vals['analytic_distribution'] = analytic_distribution
        return (0, 0, line_vals)

    def _create_and_post_journal_entry(self, move_lines, ref_suffix=''):
        """Create and post a journal entry with given lines"""
        move_vals = {
            'journal_id': self.advance_journal_id.id,
            'date': self.date,
            'ref': self.name + (f' - {ref_suffix}' if ref_suffix else ''),
            'line_ids': move_lines,
            'company_id': self.company_id.id,
        }

        # Posting is done sudo() because the petty-cash groups intentionally do
        # not carry full accounting rights; _check_manager() is the auth gate.
        move = self.env['account.move'].sudo().create(move_vals)
        move.action_post()
        return move

    def _create_and_post_payment(self, partner_id, amount, memo, move):
        """Create and post payment record"""
        payment_vals = {
            'partner_id': partner_id,
            'amount': amount,
            'journal_id': self.advance_journal_id.id,
            'date': self.date,
            'memo': memo,
            'payment_type': 'outbound',
            'settlement_id': self.id,
            'company_id': self.company_id.id,
        }

        payment = self.env['account.payment'].sudo().create(payment_vals)
        payment.write({'move_id': move.id})
        payment.action_post()
        return payment

    def _reconcile_bill_with_settlement(self, move):
        """Reconcile bill payable lines with settlement payable lines"""
        bill_payable_lines = self.tagged_bill_id.line_ids.filtered(
            lambda l: l.account_id.account_type == 'liability_payable' and not l.reconciled
        )
        settlement_payable_line = move.line_ids.filtered(
            lambda l: l.account_id.account_type == 'liability_payable'
        )

        if bill_payable_lines and settlement_payable_line:
            (bill_payable_lines + settlement_payable_line).sudo().reconcile()

    # ========== End Helper Methods ==========

    def _post_with_advance(self):
        """Post settlement with advance (existing logic)"""
        rec = self

        # Calculate amounts
        bill_amount = rec.tagged_bill_id.amount_total
        requested_advance_amount = rec.advance_amount

        # Determine actual settlement amount based on settlement mode
        if rec.settlement_mode == 'partial':
            # Partial: Only settle the bill amount, keep remaining balance
            # Adjust advance line amounts if needed
            rec._adjust_advance_lines(bill_amount, requested_advance_amount)
            actual_advance_settlement = min(bill_amount, rec.advance_amount)
            cash_adjustment_amount = 0.0  # No cash adjustment in partial mode
        else:
            # Full: Settle full advance amount, create cash adjustment if needed
            actual_advance_settlement = requested_advance_amount
            if actual_advance_settlement > bill_amount:
                cash_adjustment_amount = actual_advance_settlement - bill_amount
            else:
                cash_adjustment_amount = 0.0

        # Get common data
        employee_partner = rec._get_employee_partner()
        analytic_distribution = rec._get_analytic_distribution()
        payable_account = rec._get_payable_account()
        cash_account = rec._get_cash_account()

        # Build journal entry lines
        move_lines = []

        # 1. Credit employee advance account (clear advance)
        move_lines.append(rec._create_journal_line(
            name=f'Settlement: {rec.name} - Clear Advance',
            account_id=rec.employee_advance_account_id.id,
            debit=0.0,
            credit=actual_advance_settlement,
            partner_id=employee_partner.id,
            analytic_distribution=analytic_distribution
        ))

        # 2. Debit accounts payable (pay bill)
        move_lines.append(rec._create_journal_line(
            name=f'Settlement: {rec.name} - Pay Bill',
            account_id=payable_account.id,
            debit=bill_amount,
            credit=0.0,
            partner_id=employee_partner.id,
            analytic_distribution=analytic_distribution
        ))

        # 3. Handle cash adjustment for full settlement mode
        if rec.settlement_mode == 'full' and cash_adjustment_amount > 0.01:
            # Employee returns excess cash to company - Debit cash
            move_lines.append(rec._create_journal_line(
                name=f'Settlement: {rec.name} - Cash Adjustment (Full Settlement)',
                account_id=cash_account.id,
                debit=cash_adjustment_amount,
                credit=0.0,
                partner_id=employee_partner.id,
                analytic_distribution=analytic_distribution
            ))

        # 4. Handle additional payment if bill exceeds advance (both modes)
        if bill_amount > actual_advance_settlement:
            additional_payment = bill_amount - actual_advance_settlement
            # Company pays employee additional amount - Credit cash
            move_lines.append(rec._create_journal_line(
                name=f'Settlement: {rec.name} - Additional Payment to Employee',
                account_id=cash_account.id,
                debit=0.0,
                credit=additional_payment,
                partner_id=employee_partner.id,
                analytic_distribution=analytic_distribution
            ))

        # Create and post journal entry
        move = rec._create_and_post_journal_entry(move_lines)
        rec.move_id = move.id

        # Create and post payment
        payment = rec._create_and_post_payment(
            partner_id=employee_partner.id,
            amount=bill_amount,
            memo=f'Settlement: {rec.name}',
            move=move
        )
        rec.payment_id = payment.id

        # Reconcile bill with payment
        rec._reconcile_bill_with_settlement(move)

        # Set state to 'posted' BEFORE processing advances
        rec.state = 'posted'

        # Process advances based on settlement mode
        rec._process_advance_reconciliations(move)

    def _adjust_advance_lines(self, bill_amount, requested_advance_amount):
        """Adjust advance line amounts if bill is less than total requested advances"""
        if bill_amount < requested_advance_amount:
            remaining_to_settle = bill_amount
            lines_to_remove = []

            for adv_line in self.advance_line_ids:
                requested_settle = adv_line.settled_amount
                actual_settled = min(requested_settle, remaining_to_settle)
                remaining_to_settle -= actual_settled

                if actual_settled > 0:
                    adv_line.write({'settled_amount': actual_settled})
                else:
                    lines_to_remove.append(adv_line)

            # Remove lines that won't be settled
            for line in lines_to_remove:
                line.unlink()

    def _process_advance_reconciliations(self, move):
        """Process each advance and update their states"""
        for adv_line in self.advance_line_ids:
            advance = adv_line.advance_id

            # Reconcile this advance's payment with its portion of the settlement
            advance_move = advance.move_id
            if advance_move:
                advance_lines = advance_move.line_ids.filtered(
                    lambda l: l.account_id == self.employee_advance_account_id and not l.reconciled
                )
                settlement_advance_line = move.line_ids.filtered(
                    lambda l: l.account_id == self.employee_advance_account_id
                )

                if advance_lines and settlement_advance_line:
                    (advance_lines + settlement_advance_line).sudo().reconcile()

            # Update advance state based on settlement mode and remaining balance
            advance.invalidate_recordset(['settled_amount', 'balance'])
            advance._compute_settled()

            if self.settlement_mode == 'return':
                # Mark advance as returned and settled
                advance.write({
                    'state': 'settled',
                    'is_returned': True,
                    'return_move_id': move.id
                })
            elif self.settlement_mode == 'full':
                advance.write({'state': 'settled'})
            else:
                # For partial settlement mode, check the actual balance
                if advance.balance == 0:
                    advance.write({'state': 'settled'})
                elif advance.settled_amount > 0:
                    advance.write({'state': 'partially_settled'})

    def _post_without_advance(self):
        """Post settlement without advance (direct bill payment)"""
        rec = self

        bill_amount = rec.tagged_bill_id.amount_total

        # Get common data
        employee_partner = rec._get_employee_partner()
        analytic_distribution = rec._get_analytic_distribution()
        payable_account = rec._get_payable_account()
        cash_account = rec._get_cash_account()

        # Build journal entry lines
        move_lines = []

        # 1. Debit accounts payable (pay bill)
        move_lines.append(rec._create_journal_line(
            name=f'Settlement: {rec.name} - Pay Bill Directly',
            account_id=payable_account.id,
            debit=bill_amount,
            credit=0.0,
            partner_id=employee_partner.id,
            analytic_distribution=analytic_distribution
        ))

        # 2. Credit cash/bank account (payment made)
        move_lines.append(rec._create_journal_line(
            name=f'Settlement: {rec.name} - Direct Payment',
            account_id=cash_account.id,
            debit=0.0,
            credit=bill_amount,
            partner_id=employee_partner.id,
            analytic_distribution=analytic_distribution
        ))

        # Create and post journal entry
        move = rec._create_and_post_journal_entry(move_lines)
        rec.move_id = move.id

        # Create and post payment
        payment = rec._create_and_post_payment(
            partner_id=employee_partner.id,
            amount=bill_amount,
            memo=f'Direct Settlement: {rec.name}',
            move=move
        )
        rec.payment_id = payment.id

        # Reconcile bill with payment
        rec._reconcile_bill_with_settlement(move)

        # Set state to posted
        rec.state = 'posted'

    def _post_return_advance(self):
        """Post return of unused advance (opposite of advance payment)"""
        rec = self

        # Calculate total return amount
        return_amount = rec.advance_amount

        # Get common data
        employee_partner = rec._get_employee_partner()
        analytic_distribution = rec._get_analytic_distribution()
        cash_account = rec._get_cash_account()

        # Build journal entry lines (opposite of advance payment)
        move_lines = []

        # 1. Debit cash/bank account (money coming back to company)
        move_lines.append(rec._create_journal_line(
            name=f'Return Advance: {rec.name} - Cash Received',
            account_id=cash_account.id,
            debit=return_amount,
            credit=0.0,
            partner_id=employee_partner.id,
            analytic_distribution=analytic_distribution
        ))

        # 2. Credit employee advance account (clear the advance liability)
        move_lines.append(rec._create_journal_line(
            name=f'Return Advance: {rec.name} - Clear Advance',
            account_id=rec.employee_advance_account_id.id,
            debit=0.0,
            credit=return_amount,
            partner_id=employee_partner.id,
            analytic_distribution=analytic_distribution
        ))

        # Create and post journal entry
        move = rec._create_and_post_journal_entry(move_lines, ref_suffix='Return Advance')
        rec.move_id = move.id

        # Set state to 'posted' BEFORE processing advances
        rec.state = 'posted'

        # Process advances and mark them as settled
        rec._process_advance_reconciliations(move)

    def action_cancel(self):
        self._check_manager()
        for rec in self:
            if rec.move_id and rec.move_id.state == 'posted':
                rec.move_id.sudo().button_draft()
                rec.move_id.sudo().button_cancel()
            rec.state = 'cancelled'

    def action_draft(self):
        self.state = 'draft'

    def action_open_journal_entry(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Journal Entry',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.move_id.id,
            'target': 'current',
        }

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
