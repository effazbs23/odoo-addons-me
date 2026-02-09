# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # Store linked schedule lines directly on payment (persists without context)
    lease_schedule_line_ids = fields.Many2many(
        'lessor.lease.schedule.line',
        'lease_payment_schedule_line_rel',
        'payment_id',
        'schedule_line_id',
        string='Lease Schedule Lines',
        help='Schedule lines associated with this lease payment collection'
    )

    def create(self, vals):
        """
        Override to link schedule lines to payment immediately on creation
        This ensures draft payments are traceable back to their schedule lines
        """
        # Check if this is a lease payment collection
        schedule_line_ids = self.env.context.get('lease_schedule_line_ids')
        if schedule_line_ids:
            # Create the payment
            payment = super(AccountPayment, self).create(vals)

            # Link schedule lines to this payment via Many2many field (persists without context)
            schedule_lines = self.env['lessor.lease.schedule.line'].browse(schedule_line_ids)
            if schedule_lines.exists():
                payment.write({'lease_schedule_line_ids': [(6, 0, schedule_line_ids)]})

                # Also set payment_id on schedule lines (backward link)
                schedule_lines.write({'payment_id': payment.id})

                # Manually recompute payment_state to ensure UI updates immediately
                schedule_lines._compute_payment_state()

                _logger.info(
                    'Linked %d schedule line(s) to draft payment %s (state: %s)',
                    len(schedule_lines), payment.name, payment.state
                )

            return payment

        # Standard Odoo behavior for regular payments
        return super(AccountPayment, self).create(vals)

    def _create_payment_entry(self, amount):
        """
        Override to create custom journal entry for lease payment collections

        For regular payments: Use standard Odoo behavior
        For lease payment collections: Create custom entry that credits
        Hire Purchase Receivable (113104) instead of Accounts Receivable

        Expected journal entry for lease payment:
            Dr. Cash/Bank (from payment journal)
                Cr. Hire Purchase Receivable (113104)
        """
        self.ensure_one()

        # Check if this is a lease payment collection
        # Use stored field instead of context (context is lost when payment is reopened)
        if self.lease_schedule_line_ids.exists():
            return self._create_lease_payment_entry(amount)

        # Standard Odoo behavior for regular payments
        return super()._create_payment_entry(amount)

    def _create_lease_payment_entry(self, amount):
        """
        Create custom payment entry for lease payment collection

        Creates a direct cash receipt that credits Hire Purchase Receivable:
            Dr. Cash/Bank (from payment journal's default debit account)
                Cr. Hire Purchase Receivable (113104)

        This matches the client's expected entry for monthly collections.
        No invoice or accounts receivable involved.

        Args:
            amount: Payment amount (float)

        Returns:
            account.move: Created journal entry
        """
        self.ensure_one()

        # Get schedule lines from stored field (persists without context)
        # This is more reliable than context which is lost when payment form is reopened
        schedule_lines = self.lease_schedule_line_ids
        if not schedule_lines.exists():
            # Fallback to context for backward compatibility
            schedule_line_ids = self.env.context.get('lease_schedule_line_ids')
            if schedule_line_ids:
                schedule_lines = self.env['lessor.lease.schedule.line'].browse(schedule_line_ids)
            if not schedule_lines.exists():
                raise UserError(_(
                    'Schedule lines not found for this lease payment.\n\n'
                    'Please ensure payment is created from the lease schedule line '
                    'using the "Collect Payment" button.'
                ))

        # Get the first schedule line and contract
        schedule_line = schedule_lines[0]
        contract = schedule_line.contract_id

        # Get receivable account from contract configuration based on accounting method
        if contract.accounting_method == 'gross':
            receivable_account = contract._get_account('hire_purchase_receivable_account_id')
        else:
            # Net Method: Use regular lease receivable account
            receivable_account = contract._get_account('lease_receivable_account_id')

        _logger.info(
            'Using receivable account %s for lease payment (method: %s)',
            receivable_account.code, contract.accounting_method
        )

        # Get cash/bank account from payment journal
        # For inbound payments, the debit account is the journal's default account
        liquidity_account = self.journal_id.default_account_id
        if not liquidity_account:
            raise UserError(_(
                'No default account configured for payment journal "%s".\n\n'
                'Please configure a default account for this journal.'
            ) % self.journal_id.name)

        # Create description based on number of months
        if len(schedule_lines) == 1:
            ref_description = _('Lease Payment - %s - Month %s') % (contract.name, schedule_line.month)
            line_name = _('Lease Payment - Month %s') % schedule_line.month
        else:
            months = ', '.join(str(l.month) for l in schedule_lines)
            ref_description = _('Lease Payment - %s - Months %s') % (contract.name, months)
            line_name = _('Lease Payment - Months %s') % months

        # Prepare journal entry
        move_vals = {
            'move_type': 'entry',
            'date': self.date,
            'ref': ref_description,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'line_ids': [
                # Dr. Cash/Bank
                (0, 0, {
                    'name': line_name,
                    'account_id': liquidity_account.id,
                    'debit': abs(amount),
                    'credit': 0.0,
                    'partner_id': self.partner_id.id,
                }),
                # Cr. Hire Purchase Receivable (or Lease Receivable for Net Method)
                (0, 0, {
                    'name': _('Hire Purchase Receivable - %s') % line_name,
                    'account_id': receivable_account.id,
                    'debit': 0.0,
                    'credit': abs(amount),
                    'partner_id': self.partner_id.id,
                }),
            ],
        }

        # Create the journal entry
        move = self.env['account.move'].create(move_vals)

        _logger.info(
            'Created lease payment entry %s for %d schedule line(s). '
            'Dr. %s / Cr. %s = %.2f',
            move.name, len(schedule_lines), liquidity_account.code, receivable_account.code, abs(amount)
        )

        return move

    def action_post(self):
        """
        Override to handle lease payment collections differently

        For lease payments: Create custom entry before posting, then mark schedule lines as collected
        For regular payments: Use standard Odoo behavior
        """
        # Check if this is a lease payment collection (using stored field)
        if self.lease_schedule_line_ids.exists():
            # Create custom lease payment entry
            custom_move = self._create_lease_payment_entry(self.amount)
            self.move_id = custom_move.id

            # Mark schedule lines as collected
            schedule_lines = self.lease_schedule_line_ids
            schedule_lines._compute_payment_state()
            for schedule_line in schedule_lines:
                schedule_line._mark_as_collected(self)
            return super().action_post()

        # Standard Odoo behavior for regular payments
        return super().action_post()
