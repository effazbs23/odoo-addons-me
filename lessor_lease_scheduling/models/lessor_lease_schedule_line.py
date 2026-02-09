# -*- coding: utf-8 -*-
from odoo import models, fields, api


class LessorLeaseScheduleLine(models.Model):
    _name = 'lessor.lease.schedule.line'
    _description = 'Lessor Lease Schedule Line'
    _order = 'contract_id, month'

    name = fields.Char(
        compute="_compute_name",
        index=True,
        store=True,
        readonly=True
    )

    contract_id = fields.Many2one(
        'lessor.lease.contract',
        string='Contract',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='contract_id.company_id',
        store=True,
        index=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='contract_id.currency_id',
        store=True
    )
    
    month = fields.Integer(
        string='Month',
        required=True,
        help="Sequential month number"
    )
    
    payment_date = fields.Date(
        string='Payment Date',
        required=True,
        help="Date of installment payment"
    )
    
    opening_npv = fields.Monetary(
        string='Opening NPV',
        currency_field='currency_id',
        help="Net Present Value at start of period"
    )
    
    interest = fields.Monetary(
        string='Interest',
        currency_field='currency_id',
        help="Finance income for the period"
    )
    
    principal = fields.Monetary(
        string='Principal',
        currency_field='currency_id',
        help="Principal repayment for the period"
    )
    
    closing_npv = fields.Monetary(
        string='Closing NPV',
        currency_field='currency_id',
        help="Net Present Value at end of period"
    )
    
    net_payment = fields.Monetary(
        string='Net Payment',
        currency_field='currency_id',
        help="Monthly installment amount (excluding VAT)"
    )
    
    vat = fields.Monetary(
        string='VAT',
        currency_field='currency_id',
        help="VAT amount for the period"
    )
    
    gross_payment = fields.Monetary(
        string='Gross Payment',
        currency_field='currency_id',
        help="Total payment including VAT"
    )
    
    # Accounting tracking fields
    is_invoiced = fields.Boolean(
        string='Is Invoiced',
        default=False,
        help="Indicates if this line has been invoiced"
    )
    
    is_paid = fields.Boolean(
        string='Is Paid',
        compute='_compute_is_paid',
        store=True,
        help="Indicates if this line has been paid"
    )
    
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        help="Related invoice"
    )
    
    payment_id = fields.Many2one(
        'account.payment',
        string='Payment',
        help="Related payment"
    )
    
    move_id = fields.Many2one(
        'account.move',
        string='Journal Entry',
        help="Related accounting journal entry"
    )
    
    @api.depends('invoice_id.payment_state')
    def _compute_is_paid(self):
        """Update is_paid based on invoice payment state"""
        for record in self:
            if record.invoice_id:
                record.is_paid = record.invoice_id.payment_state in ['paid', 'in_payment']
            else:
                record.is_paid = False
    
    @api.depends('payment_date', 'contract_id', 'gross_payment', 'month')
    def _compute_name(self):
        """
        Compute display name for schedule lines
        Format: "Payment Date - Contract Name - Month X ($Amount)"
        Example: "2025-12-10 - LLC/00138 - Month 1 ($3,940.00)"
        """
        for record in self:
            if record.payment_date and record.contract_id:
                # Format: "YYYY-MM-DD - Contract - Month X ($Amount)"
                record.name = '%s - %s - ($%s)' % (
                    record.payment_date.strftime('%Y-%m-%d'),
                    record.contract_id.name or 'Draft',
                    '{:,.2f}'.format(record.gross_payment)
                )
            else:
                record.name = 'Month %s' % (record.month or '?')
