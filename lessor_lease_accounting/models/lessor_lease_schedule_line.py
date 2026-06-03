# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from markupsafe import Markup

import logging
_logger = logging.getLogger(__name__)


class LessorLeaseScheduleLine(models.Model):
    _inherit = 'lessor.lease.schedule.line'

    # ===== Payment Collection Fields =====
    is_collected = fields.Boolean(
        string='Payment Collected',
        default=False,
        help="Indicates if payment has been collected for this installment"
    )

    payment_state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('in_process', 'In Process'),
            ('posted', 'Posted'),
            ('sent', 'Sent'),
            ('reconciled', 'Reconciled'),
            ('paid', 'Paid'),
            ('cancelled', 'Cancelled'),
            ('canceled', 'Cancelled'),  # US spelling variant
        ],
        string='Payment State',
        compute='_compute_payment_state',
        store=True,
        help="State of the payment entry"
    )

    accounting_processed = fields.Boolean(
        string='Accounting Processed',
        default=False,
        help="Indicates if VAT and Interest recognition entries have been created"
    )

    vat_move_id = fields.Many2one(
        'account.move',
        string='VAT Recognition Entry',
        readonly=True,
        help="VAT recognition journal entry for this period"
    )

    interest_move_id = fields.Many2one(
        'account.move',
        string='Interest Recognition Entry',
        readonly=True,
        help="Interest recognition journal entry for this period"
    )

    @api.depends('payment_id', 'payment_id.state')
    def _compute_payment_state(self):
        """Compute payment state from linked payment"""
        for record in self:
            if record.payment_id:
                record.payment_state = record.payment_id.state
            else:
                record.payment_state = False

    # ===== Payment Collection Action =====
    def action_collect_payment(self):
        """
        Open payment registration wizard for direct collection

        Creates a direct payment entry that:
        Dr. Cash/Bank (from payment journal)
            Cr. Hire Purchase Receivable (113104)

        This matches the client's expected entry for monthly collections.
        No invoice is involved in this flow.

        Supports both single and multiple schedule line selection for batch collection.
        """
        # Validation: Check if all lines belong to the same contract
        contracts = self.mapped('contract_id')
        if len(contracts) > 1:
            raise UserError(_(
                'Cannot collect payments for multiple contracts at once.\n\n'
                'Please select schedule lines from the same contract.'
            ))

        contract = contracts[0]

        # Validation: Accounting method must be set
        if not contract.accounting_method:
            raise UserError(_(
                'Accounting method must be set on contract before collecting payments.\n\n'
                'Please set the accounting method on contract %s.'
            ) % contract.name)

        # Validation: Filter out already collected lines (with active payments)
        # Handle both 'cancelled' and 'canceled' spellings
        already_collected = self.filtered(
            lambda l: l.is_collected and l.payment_id and l.payment_id.state not in ['cancelled', 'canceled']
        )
        if already_collected:
            months = ', '.join(str(l.month) for l in already_collected)
            raise UserError(_(
                'Payment has already been collected for Month(s): %s\n\n'
                'Please deselect these lines and try again.'
            ) % months)

        # Validation: Filter out future payment dates
        today = fields.Date.context_today(self)
        future_payments = self.filtered(lambda l: l.payment_date > today)
        if future_payments:
            months = ', '.join('Month %s (%s)' % (l.month, l.payment_date) for l in future_payments)
            raise UserError(_(
                'Cannot collect payment for future installments:\n%s\n\n'
                'Today: %s'
            ) % (months, today))

        # Get Hire Purchase Receivable account for Gross Method
        if contract.accounting_method == 'gross':
            receivable_account = contract._get_account('hire_purchase_receivable_account_id')
        else:
            # Net Method: Use regular receivable account
            receivable_account = contract._get_account('lease_receivable_account_id')

        # Calculate total amount from all selected lines
        total_amount = sum(self.mapped('gross_payment'))

        # Create title showing which months are being collected
        if len(self) == 1:
            title = _('Register Payment - Month %s') % self.month
        else:
            months = ', '.join(str(l.month) for l in self)
            title = _('Register Payment - Months %s') % months

        # Return action to open Customer Payments form (account.payment)
        # This is the standard Odoo payment form, not the invoice register wizard
        # We pass the receivable account in context so the payment knows where to credit
        # NOTE: Payment journal (Bank/Cash) is selected by user in the form
        return {
            'name': title,
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_payment_type': 'inbound',
                'default_partner_type': 'customer',
                'default_partner_id': contract.lessee_id.id,
                'default_amount': total_amount,
                'default_payment_date': self[0].payment_date,  # Use earliest payment date
                # Don't pre-set journal - user selects in form (Bank, Cash, etc.)
                # Custom context to indicate this is a lease payment collection
                'lease_payment_collection': True,
                'lease_receivable_account_id': receivable_account.id,
                'lease_schedule_line_ids': self.ids,  # Store selected line IDs
            },
        }

    def action_smart_payment_button(self):
        """
        Smart button that handles both viewing existing payment and creating new payment

        - If payment exists (any state except cancelled): View the payment in same window
        - If payment_id is set but record doesn't exist (deleted): Clear payment_id and create new
        - If no payment exists: Open new payment form
        """
        self.ensure_one()

        # Check if there's an existing payment (not cancelled - handle both spellings)
        # Also check if payment record actually exists (in case it was deleted)
        if self.payment_id.exists() and self.payment_id.state not in ['cancelled', 'canceled']:
            # Payment exists - view it directly in same window
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'res_id': self.payment_id.id,
                'view_mode': 'form',
                'target': 'current',  # Open in same window, not dialog
                'context': self.env.context,
            }
        else:
            # Clear payment_id if it was set but payment no longer exists
            if self.payment_id and not self.payment_id.exists():
                self.write({'payment_id': False})

            # No payment or cancelled - create new one
            return self.action_collect_payment()

    def action_view_payment(self):
        """View the payment entry for this schedule line"""
        self.ensure_one()

        if not self.payment_id:
            raise UserError(_('No payment exists for Month %s.') % self.month)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'res_id': self.payment_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_vat_move(self):
        """View the VAT recognition entry"""
        self.ensure_one()

        if not self.vat_move_id:
            raise UserError(_('No VAT recognition entry exists for Month %s.') % self.month)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.vat_move_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_interest_move(self):
        """View the Interest recognition entry"""
        self.ensure_one()

        if not self.interest_move_id:
            raise UserError(_('No Interest recognition entry exists for Month %s.') % self.month)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.interest_move_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _mark_as_collected(self, payment):
        """
        Mark schedule line as collected after successful payment

        Note: payment_id is already set when payment is created (in create override)
        This method only marks is_collected=True and posts the chatter message

        Args:
            payment: account.payment record
        """
        self.ensure_one()

        # Only mark as collected - payment_id is already set
        self.write({'is_collected': True})

        # Post message on contract
        message = Markup("<p>%s</p>") % _(
            'Payment collected for Month %s: %s'
        ) % (self.month, payment._get_html_link())
        self.contract_id.message_post(body=message)

        _logger.info(
            'Marked schedule line %s (Month %s) as collected. Payment: %s',
            self.id, self.month, payment.name
        )

    def _mark_accounting_processed(self, vat_move=None, interest_move=None):
        """
        Mark schedule line as accounting processed

        Args:
            vat_move: VAT recognition journal entry
            interest_move: Interest recognition journal entry
        """
        self.ensure_one()

        vals = {'accounting_processed': True}

        if vat_move:
            vals['vat_move_id'] = vat_move.id
        if interest_move:
            vals['interest_move_id'] = interest_move.id

        self.write(vals)

        _logger.info(
            'Marked schedule line %s (Month %s) as accounting processed',
            self.id, self.month
        )
