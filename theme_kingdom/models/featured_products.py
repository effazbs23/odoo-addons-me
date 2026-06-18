# -*- coding: utf-8 -*-
from odoo import api, fields, models


class FeaturedProducts(models.Model):
    _name = 'featured.products'
    _description = 'Featured Products'

    name = fields.Char(
        required=True,
        string='Name',
        help='Name of the category.',
    )
    product_tmpl_ids = fields.Many2many(
        'product.template',
        string='Featured Products',
        domain="[('sale_ok', '=', True), ('is_published', '=', True)]",
        help='Choose featured products',
    )

    @api.model
    def get_website_featured_record(self):
        """Featured products configuration shown on the homepage."""
        return self.sudo().search([], limit=1)

    def get_website_products(self, limit=12):
        """Published products for the featured carousel."""
        self.ensure_one()
        products = self.product_tmpl_ids.filtered(
            lambda p: p.sale_ok and p.is_published
        )
        if products:
            return products[:limit]
        return self.env['product.template'].sudo().search(
            [
                ('sale_ok', '=', True),
                ('is_published', '=', True),
            ],
            order='website_sequence desc, id desc',
            limit=limit,
        )
