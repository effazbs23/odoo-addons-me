from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    warranty_months = fields.Integer(
        string='Default Warranty (Months)',
        help='Default warranty duration applied to repair order part lines '
             'using this product. Leave 0 to require manual entry per line.',
    )
