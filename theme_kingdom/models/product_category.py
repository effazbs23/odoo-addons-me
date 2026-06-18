from odoo import models, fields


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    show_in_homepage = fields.Boolean(
        string='Show in Homepage',
        default=False,
    )
