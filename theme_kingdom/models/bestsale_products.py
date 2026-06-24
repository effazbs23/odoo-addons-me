# -*- coding: utf-8 -*-
from odoo import api, fields, models


class BestsaleProducts(models.Model):
    _name = 'bestsale.products'
    _inherit = ['kingdom.website.cache.mixin']
    _description = 'Best Sale Products'

    name = fields.Char(
        required=True,
        string='Name',
        default='Best Sale',
        help='Section title shown on the homepage.',
    )
    product_tmpl_ids = fields.Many2many(
        'product.template',
        string='Best Sale Products',
        domain="[('sale_ok', '=', True), ('is_published', '=', True)]",
        help='Choose products for the best sale carousel.',
    )

    @api.model
    def get_website_bestsale_record(self):
        """Best sale configuration shown on the homepage."""
        return self.sudo().search([], limit=1)

    def get_website_products(self, limit=12):
        """Published products for the best sale carousel."""
        self.ensure_one()
        products = self.product_tmpl_ids.filtered(
            lambda p: p.sale_ok and p.is_published
        )
        if products:
            return products[:limit]

        ProductTemplate = self.env['product.template'].sudo()
        candidates = ProductTemplate.search(
            [
                ('sale_ok', '=', True),
                ('is_published', '=', True),
            ],
            order='website_sequence desc, id desc',
        )
        on_sale = candidates.filtered(
            lambda p: p.compare_list_price
            and p.compare_list_price > p._get_contextual_price()
        )
        if on_sale:
            return on_sale[:limit]
        return candidates[:limit]
