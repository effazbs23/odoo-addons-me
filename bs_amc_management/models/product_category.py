from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    amc_provision_account_id = fields.Many2one(
        'account.account', company_dependent=True,
        string='AMC Provision Account',
        domain="[('account_type', 'not in', "
               "('asset_receivable', 'asset_cash', 'liability_credit_card', 'off_balance'))]",
        help='Credited by the monthly AMC provision entries and debited by the AMC vendor '
             'bills for products in this category.')
