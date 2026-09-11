from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    expiry_alert_days = fields.Integer(
        string='Expiry Alert (Days)',
        help="Flag lots of products in this category as near-expiry this many days "
             "before their expiration date. Leave at 0 to use the global default "
             "set in Inventory settings.")
