# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from markupsafe import Markup
import math
from datetime import date


class LessorLeaseContract(models.Model):
    _name = 'lessor.lease.contract'
    _description = 'Lessor Lease Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc, id desc'
    _rec_name = 'name'

    # ===== Basic Information =====
    name = fields.Char(
        string='Contract Number',
        required=True,
        copy=False,
        readonly=True,
        default='New',
        tracking=True
    )
    
    lessee_id = fields.Many2one(
        'res.partner',
        string='Lessee',
        required=True,
        domain=[('customer_rank', '>', 0)],
        tracking=True,
        help="The customer who is leasing the asset"
    )
    
    asset_name = fields.Char(
        string='Asset',
        required=True,
        tracking=True,
        help="The underlying asset being leased"
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        tracking=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        tracking=True
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, copy=False)
    
    # ===== Financial Parameters =====
    cost_price = fields.Monetary(
        string='Cost Price',
        required=True,
        currency_field='currency_id',
        tracking=True,
        help="Cost of the asset being leased"
    )
    
    total_gross_amount = fields.Monetary(
        string='Total Gross Amount (Inc. VAT)',
        required=True,
        currency_field='currency_id',
        tracking=True,
        help="Total sale price including VAT"
    )
    
    down_payment_percent = fields.Float(
        string='Down Payment (%)',
        required=True,
        default=20.0,
        tracking=True,
        help="Percentage of down payment"
    )
    
    annual_interest_rate = fields.Float(
        string='Annual Interest Rate (%)',
        required=True,
        default=12.0,
        tracking=True,
        help="Nominal annual interest rate"
    )
    
    term_months = fields.Integer(
        string='Term (Months)',
        required=True,
        tracking=True,
        help="Lease duration in months"
    )
    
    start_date = fields.Date(
        string='Start Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        help="Lease commencement date"
    )
    
    end_date = fields.Date(
        string='End Date',
        compute='_compute_end_date',
        store=True,
        readonly=True,
        tracking=True,
        help="Lease end date"
    )

    vat_rate_id = fields.Many2one(
        'account.tax',
        string='VAT Rate',
        required=True,
        domain=[('type_tax_use', '=', 'sale')],
        tracking=True,
        help="Applicable VAT rate"
    )

    accounting_method = fields.Selection([
        ('net', 'Net Method (IFRS 16)'),
        ('gross', 'Gross Method (Hire-Purchase)'),
    ], string='Accounting Method', required=True, default='gross', tracking=True,
       help="Net Method: IFRS 16 standard lease accounting\n"
            "Gross Method: Hire-purchase accounting with deferred interest")
    
    # ===== Calculated Fields =====
    down_payment_amount = fields.Monetary(
        string='Down Payment Amount',
        compute='_compute_down_payment_amount',
        store=True,
        currency_field='currency_id',
        help="Calculated down payment amount"
    )
    
    total_net_amount = fields.Monetary(
        string='Total Net Amount',
        compute='_compute_net_amounts',
        store=True,
        currency_field='currency_id',
        help="Total amount excluding VAT"
    )
    
    gross_asset_value_financed = fields.Monetary(
        string='Gross Asset Value Financed',
        compute='_compute_gross_asset_value_financed',
        store=True,
        currency_field='currency_id',
        help="Amount financed after down payment (excluding VAT)"
    )
    
    monthly_interest_rate = fields.Float(
        string='Monthly Interest Rate',
        compute='_compute_monthly_interest_rate',
        store=True,
        digits=(12, 6),
        help="Calculated monthly interest rate"
    )
    
    monthly_installment = fields.Monetary(
        string='Monthly Installment',
        compute='_compute_monthly_installment',
        store=True,
        currency_field='currency_id',
        help="Monthly payment amount (PMT calculation with ROUNDUP)"
    )
    
    total_vat = fields.Monetary(
        string='Total VAT',
        compute='_compute_total_vat',
        store=True,
        currency_field='currency_id',
        help="Total VAT amount"
    )
    
    margin = fields.Monetary(
        string='Margin',
        compute='_compute_margin',
        store=True,
        currency_field='currency_id',
        help="Profit margin (Net Sales - Cost)"
    )
    
    margin_percent = fields.Float(
        string='Margin %',
        compute='_compute_margin',
        store=True,
        digits=(12, 2),
        help="Profit margin percentage"
    )
    
    outstanding_balance = fields.Monetary(
        string='Outstanding Balance',
        compute='_compute_outstanding_balance',
        store=True,
        currency_field='currency_id',
        help="Total future payments (Monthly Installment × Term Months)"
    )
    
    # ===== Related Schedule Lines =====
    schedule_line_ids = fields.One2many(
        'lessor.lease.schedule.line',
        'contract_id',
        string='Schedule Lines',
        help="Amortization schedule lines"
    )
    
    schedule_line_count = fields.Integer(
        string='Schedule Line Count',
        compute='_compute_schedule_line_count',
        help="Number of schedule lines"
    )
    
    # ===== Computed Fields =====
    @api.depends('total_gross_amount', 'down_payment_percent')
    def _compute_down_payment_amount(self):
        for record in self:
            record.down_payment_amount = record.total_gross_amount * (record.down_payment_percent / 100.0)
    
    @api.depends('total_gross_amount', 'down_payment_amount', 'vat_rate_id')
    def _compute_net_amounts(self):
        for record in self:
            vat_rate = record.vat_rate_id.amount if record.vat_rate_id else 0.0
            vat_divisor = 1 + (vat_rate / 100.0)
            record.total_net_amount = record.total_gross_amount / vat_divisor if vat_divisor else 0
    
    @api.depends('total_gross_amount', 'down_payment_amount')
    def _compute_gross_asset_value_financed(self):
        """
        Calculate Gross Asset Value Financed
        
        Uses Thai market standard: Total Gross Amount - Down Payment (GROSS - GROSS)
        Note: This includes VAT in the financed amount, which is common practice
        in Thailand's hire-purchase market.
        """
        for record in self:
            record.gross_asset_value_financed = record.total_gross_amount - record.down_payment_amount
    
    @api.depends('annual_interest_rate')
    def _compute_monthly_interest_rate(self):
        for record in self:
            if record.annual_interest_rate:
                record.monthly_interest_rate = (1 + record.annual_interest_rate / 100.0) ** (1.0 / 12.0) - 1
            else:
                record.monthly_interest_rate = 0.0
    
    @api.depends('gross_asset_value_financed', 'monthly_interest_rate', 'term_months')
    def _compute_monthly_installment(self):
        """
        Calculate monthly installment using PMT formula with ROUNDUP
        Excel PMT formula: PMT = PV × (r × (1 + r)^n) / ((1 + r)^n - 1)
        Then ROUNDUP to whole number (Thai market standard)
        """
        for record in self:
            if record.gross_asset_value_financed and record.monthly_interest_rate and record.term_months:
                pv = record.gross_asset_value_financed
                r = record.monthly_interest_rate
                n = record.term_months
                
                # PMT calculation
                pmt = pv * (r * (1 + r)**n) / ((1 + r)**n - 1)
                
                # ROUNDUP to whole number (Thai market standard)
                record.monthly_installment = math.ceil(pmt)
            else:
                record.monthly_installment = 0.0
    
    @api.depends('start_date', 'term_months')
    def _compute_end_date(self):
        for record in self:
            if record.start_date and record.term_months:
                record.end_date = record.start_date + relativedelta(months=record.term_months)
            else:
                record.end_date = False
    

    @api.depends('total_gross_amount', 'total_net_amount')
    def _compute_total_vat(self):
        for record in self:
            record.total_vat = record.total_gross_amount - record.total_net_amount
    
    @api.depends('total_net_amount', 'cost_price')
    def _compute_margin(self):
        for record in self:
            # Margin = Total Net Amount - Cost Price
            record.margin = record.total_net_amount - record.cost_price
            # Margin % = (1 - Cost/Net) × 100 = ((Net - Cost) / Net) × 100
            if record.total_net_amount:
                record.margin_percent = (record.margin / record.total_net_amount) * 100.0
            else:
                record.margin_percent = 0.0
    
    @api.depends('schedule_line_ids')
    def _compute_schedule_line_count(self):
        for record in self:
            record.schedule_line_count = len(record.schedule_line_ids)
    
    @api.depends('monthly_installment', 'term_months')
    def _compute_outstanding_balance(self):
        for record in self:
            record.outstanding_balance = record.monthly_installment * record.term_months
    
    # ===== Constraints =====
    @api.constrains('down_payment_percent')
    def _check_down_payment_percent(self):
        for record in self:
            if not 0 <= record.down_payment_percent <= 100:
                raise ValidationError(_('Down payment percentage must be between 0 and 100.'))
    
    @api.constrains('annual_interest_rate')
    def _check_annual_interest_rate(self):
        for record in self:
            if record.annual_interest_rate < 0:
                raise ValidationError(_('Annual interest rate cannot be negative.'))
    
    @api.constrains('term_months')
    def _check_term_months(self):
        for record in self:
            if record.term_months <= 0:
                raise ValidationError(_('Term months must be greater than zero.'))
    
    @api.constrains('cost_price', 'total_gross_amount')
    def _check_amounts(self):
        for record in self:
            if record.cost_price < 0:
                raise ValidationError(_('Cost price cannot be negative.'))
            if record.total_gross_amount <= 0:
                raise ValidationError(_('Total gross amount must be greater than zero.'))
    
    # ===== CRUD Methods =====
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('lessor.lease.contract') or 'New'
        return super(LessorLeaseContract, self).create(vals_list)
    
    def unlink(self):
        """Only allow deletion of draft contracts"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_(
                    'Cannot delete contract %s in %s state. '
                    'Only draft contracts can be deleted.'
                ) % (record.name, record.state))
        return super(LessorLeaseContract, self).unlink()
    
    # ===== Action Methods =====
    def action_confirm(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft contracts can be confirmed.'))
            
            # Inform user about down payment status
            if not record.down_payment_percent or record.down_payment_percent == 0:
                message = Markup("<p><strong>ℹ️ Full Financing (0% Down Payment)</strong><br/>"
                                "This contract has no down payment requirement. "
                                "The full amount will be financed.<br/>"
                                "You can activate the contract immediately after confirmation.</p>")
                record.message_post(body=message)
            else:
                message = Markup("<p><strong>⚠️ Down Payment Required</strong><br/>"
                                "Down payment: %s%% (%s %s)<br/>"
                                "Please create the down payment invoice before activating the contract.</p>") % (
                    record.down_payment_percent,
                    '{:,.2f}'.format(record.down_payment_amount),
                    record.currency_id.name
                )
                record.message_post(body=message)
            
            record.state = 'confirmed'
            record._generate_schedule()
    
    def action_activate(self):
        for record in self:
            if record.state != 'confirmed':
                raise UserError(_('Only confirmed contracts can be activated.'))
            
            # Check for down payment invoice if required
            if record.down_payment_percent and record.down_payment_percent > 0:
                if not record.down_payment_invoice_id:
                    raise UserError(_(
                        'Cannot activate contract: Down payment invoice must be created first.\n\n'
                        'Down payment: %s%% (%s %s)\n\n'
                        'Please create the down payment invoice before activating the contract.'
                    ) % (
                        record.down_payment_percent,
                        '{:,.2f}'.format(record.down_payment_amount),
                        record.currency_id.name
                    ))
                
                # Optional: Check if invoice is posted
                if record.down_payment_invoice_id.state == 'draft':
                    raise UserError(_(
                        'Cannot activate contract: Down payment invoice is still in draft state.\n\n'
                        'Please post the down payment invoice before activating:\n%s'
                    ) % record.down_payment_invoice_id.name)
            
            record.state = 'active'
    
    def action_close(self):
        for record in self:
            if record.state not in ['confirmed', 'active']:
                raise UserError(_('Only confirmed or active contracts can be closed.'))
            
            # Check if all schedule lines are processed (REQUIRED)
            unprocessed_lines = record.schedule_line_ids.filtered(
                lambda l: not l.is_invoiced
            )
            
            if unprocessed_lines:
                remaining_months = ', '.join([str(l.month) for l in unprocessed_lines[:10]])
                if len(unprocessed_lines) > 10:
                    remaining_months += '...'
                
                raise UserError(_(
                    'Cannot close contract: %d schedule line(s) not yet processed.\n\n'
                    'Remaining months: %s\n\n'
                    'Please wait for all monthly installments to be processed by the cron job, '
                    'or manually process them before closing the contract.\n\n'
                    'Note: If the contract was terminated early, use "Cancel" instead of "Close".'
                ) % (len(unprocessed_lines), remaining_months))
            
            # Warn about unpaid invoices (but allow closing - STANDARD PRACTICE)
            unpaid_invoices = record.schedule_line_ids.mapped('invoice_id').filtered(
                lambda inv: inv and inv.state == 'posted' and 
                inv.payment_state not in ['paid', 'in_payment']
            )
            
            if unpaid_invoices:
                message = Markup(
                    "<p><strong>⚠️ Contract Closed with Unpaid Invoices</strong><br/>"
                    "%d invoice(s) are still unpaid (Total: %s %s).<br/>"
                    "Please continue collection efforts for outstanding payments.</p>"
                ) % (
                    len(unpaid_invoices),
                    '{:,.2f}'.format(sum(unpaid_invoices.mapped('amount_residual'))),
                    record.currency_id.name
                )
                record.message_post(body=message)
            else:
                # All paid - success message
                message = Markup(
                    "<p><strong>✅ Contract Closed Successfully</strong><br/>"
                    "All %d installments have been processed and paid.<br/>"
                    "Contract completed normally.</p>"
                ) % len(record.schedule_line_ids)
                record.message_post(body=message)
            
            record.state = 'closed'
    
    def action_cancel(self):
        for record in self:
            if record.state not in ['draft', 'confirmed']:
                raise UserError(_('Only draft or confirmed contracts can be cancelled.'))
            record.state = 'cancelled'
    
    def action_set_to_draft(self):
        for record in self:
            record.state = 'draft'
            # Clear schedule lines when reverting to draft
            record.schedule_line_ids.unlink()
    
    def action_view_schedule(self):
        self.ensure_one()
        return {
            'name': _('Amortization Schedule'),
            'type': 'ir.actions.act_window',
            'res_model': 'lessor.lease.schedule.line',
            'view_mode': 'list,form',
            'domain': [('contract_id', '=', self.id)],
            'context': {'default_contract_id': self.id},
        }
    
    # ===== Schedule Generation =====
    def _generate_schedule(self):
        """
        Generate amortization schedule lines
        Thai Market Method: Uses NET amounts for amortization
        Opening NPV = Present Value of net payment stream
        Matches client's Excel model exactly with proper rounding
        """
        self.ensure_one()
        
        # Clear existing schedule lines
        self.schedule_line_ids.unlink()
        
        if not self.monthly_installment or not self.term_months:
            return
        
        monthly_rate = self.monthly_interest_rate
        vat_rate = self.vat_rate_id.amount if self.vat_rate_id else 0.0
        months = self.term_months
        
        # CRITICAL FIX: Gross payment is the monthly_installment
        # Net payment is calculated from gross
        gross_payment = self.monthly_installment
        net_payment = gross_payment / (1 + vat_rate / 100.0)
        vat_amount = gross_payment - net_payment
        
        # CRITICAL FIX: Opening NPV is the PRESENT VALUE of net payment stream
        # PV = PMT × [(1+r)^n - 1] / [r(1+r)^n]
        factor = (1 + monthly_rate) ** months
        opening_npv = net_payment * (factor - 1) / (monthly_rate * factor)
        
        schedule_lines = []
        current_npv = opening_npv
        
        for month in range(1, self.term_months + 1):
            # Calculate interest on NET balance
            interest = current_npv * monthly_rate
            
            # Calculate principal repayment from NET payment
            principal_repayment = net_payment - interest
            
            # Calculate closing balance
            closing_npv = current_npv - principal_repayment
            
            # Handle final month adjustment (rounding correction)
            if month == self.term_months:
                # Adjust principal to close out exactly
                principal_repayment = current_npv
                interest = net_payment - principal_repayment
                closing_npv = 0.00
            
            # Payment date
            payment_date = self.start_date + relativedelta(months=month - 1)
            
            # Create schedule line
            schedule_lines.append((0, 0, {
                'contract_id': self.id,
                'month': month,
                'payment_date': payment_date,
                'opening_npv': round(current_npv, 2),
                'interest': round(interest, 2),
                'principal': round(principal_repayment, 2),
                'closing_npv': round(closing_npv, 2),
                'net_payment': round(net_payment, 2),
                'vat': round(vat_amount, 2),
                'gross_payment': round(gross_payment, 2),
            }))
            
            # Update opening balance for next month
            current_npv = closing_npv
        
        # Create all schedule lines
        self.schedule_line_ids = schedule_lines
