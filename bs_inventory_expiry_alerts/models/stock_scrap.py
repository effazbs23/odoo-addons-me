from odoo import api, fields, models


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    is_expiry_writeoff = fields.Boolean(
        string='Expiry Write-off',
        help="Set when this scrap was created from the Expiry Write-off Assistant, "
             "so it can be tracked separately in the scrapped-value report.")
    expiry_writeoff_value = fields.Monetary(
        string='Scrapped Value', currency_field='company_currency_id',
        compute='_compute_expiry_writeoff_value', store=True)
    company_currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')

    @api.depends('scrap_qty', 'product_id.standard_price')
    def _compute_expiry_writeoff_value(self):
        for scrap in self:
            scrap.expiry_writeoff_value = scrap.scrap_qty * scrap.product_id.standard_price
