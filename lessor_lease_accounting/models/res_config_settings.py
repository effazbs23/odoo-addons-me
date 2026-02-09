# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # ===== Gross Method (Hire-Purchase) Accounts =====
    lessor_hire_purchase_receivable_account_id = fields.Many2one(
        'account.account',
        string='Hire Purchase Receivable Account',
        domain="[('account_type', '=', 'asset_current')]",
        config_parameter='lessor_lease_accounting.hire_purchase_receivable_account_id',
        help="Asset account for total future receivables (Gross Method)"
    )
    
    lessor_lease_sales_revenue_account_id = fields.Many2one(
        'account.account',
        string='Lease Sales Revenue Account',
        domain="[('account_type', '=', 'income')]",
        config_parameter='lessor_lease_accounting.lease_sales_revenue_account_id',
        help="Revenue account for net sales (Gross Method)"
    )
    
    lessor_deferred_interest_account_id = fields.Many2one(
        'account.account',
        string='Deferred Interest Account',
        domain="[('account_type', '=', 'liability_current')]",
        config_parameter='lessor_lease_accounting.deferred_interest_account_id',
        help="Liability account for unearned interest (Gross Method)"
    )
    
    lessor_undue_output_vat_account_id = fields.Many2one(
        'account.account',
        string='Undue Output VAT Account',
        domain="[('account_type', '=', 'liability_current')]",
        config_parameter='lessor_lease_accounting.undue_output_vat_account_id',
        help="Liability account for future VAT on installments (Gross Method)"
    )
    
    lessor_output_vat_account_id = fields.Many2one(
        'account.account',
        string='Output VAT Payable Account',
        domain="[('account_type', '=', 'liability_current')]",
        config_parameter='lessor_lease_accounting.output_vat_account_id',
        help="Liability account for recognized VAT (Gross Method)"
    )
    
    lessor_cost_of_goods_sold_account_id = fields.Many2one(
        'account.account',
        string='Cost of Goods Sold Account',
        domain="[('account_type', '=', 'expense_direct_cost')]",
        config_parameter='lessor_lease_accounting.cost_of_goods_sold_account_id',
        help="Cost of Revenue account for asset cost - appears before Gross Profit (Both Methods)"
    )
    
    lessor_asset_for_sale_account_id = fields.Many2one(
        'account.account',
        string='Asset for Sale Account',
        domain="[('account_type', 'in', ['asset_fixed', 'asset_current'])]",
        config_parameter='lessor_lease_accounting.asset_for_sale_account_id',
        help="Asset account to derecognize (Both Methods)"
    )
    
    lessor_interest_income_account_id = fields.Many2one(
        'account.account',
        string='Interest Income Account',
        domain="[('account_type', '=', 'income_other')]",
        config_parameter='lessor_lease_accounting.interest_income_account_id',
        help="Revenue account for finance income (Both Methods)"
    )

    lessor_lease_vat_rate_id = fields.Many2one(
        'account.tax',
        string='VAT Tax',
        domain=[('type_tax_use', '=', 'sale')],
        config_parameter='lessor_lease_accounting.lease_vat_rate_id',
        help="Applicable VAT rate"
    )

    lessor_lease_journal_id = fields.Many2one(
        'account.journal',
        string='Lessor Lease Journal',
        domain=[('type', '=', 'general')],
        config_parameter='lessor_lease_accounting.lease_journal_id',
        help='Lessor lease journal for managing your journal entries under same journal'
    )
    
    # ===== Net Method (IFRS 16) Accounts =====
    lessor_lease_receivable_account_id = fields.Many2one(
        'account.account',
        string='Lease Receivable Account (Net)',
        domain="[('account_type', '=', 'asset_receivable')]",
        config_parameter='lessor_lease_accounting.lease_receivable_account_id',
        help="Asset account for PV of lease payments (Net Method)"
    )
    
    lessor_finance_income_account_id = fields.Many2one(
        'account.account',
        string='Finance Income Account',
        domain="[('account_type', '=', 'income_other')]",
        config_parameter='lessor_lease_accounting.finance_income_account_id',
        help="Revenue account for interest (Net Method)"
    )
    
    lessor_gain_loss_disposal_account_id = fields.Many2one(
        'account.account',
        string='Gain/Loss on Disposal Account',
        domain="[('account_type', 'in', ['income_other', 'expense'])]",
        config_parameter='lessor_lease_accounting.gain_loss_disposal_account_id',
        help="Account for gain/loss on asset disposal (Net Method)"
    )
    
    # ===== Down Payment Invoice Account =====
    lessor_down_payment_revenue_account_id = fields.Many2one(
        'account.account',
        string='Down Payment Revenue Account',
        domain="[('account_type', '=', 'income')]",
        config_parameter='lessor_lease_accounting.down_payment_revenue_account_id',
        help="Revenue account for down payment invoices"
    )
