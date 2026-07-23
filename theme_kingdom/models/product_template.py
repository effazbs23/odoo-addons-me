# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.fields import Domain


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    kingdom_manufacturer_id = fields.Many2one(
        'kingdom.manufacturer',
        string='Manufacturer',
        index=True,
        ondelete='set null',
        help='Brand/manufacturer assigned to this product. Used when filtering the shop by manufacturer.',
    )

    def _search_get_detail(self, website, order, options):
        result = super()._search_get_detail(website, order, options)
        manufacturer_id = options.get('kingdom_manufacturer_id')
        if manufacturer_id:
            result['base_domain'].append([('kingdom_manufacturer_id', '=', int(manufacturer_id))])
        return result

    def kingdom_get_related_products(self, limit=12):
        """Products for the product page related block.

        Uses manually configured alternatives when set; otherwise falls back to
        other published products in the same eCommerce categories.
        """
        self.ensure_one()
        alternatives = self._get_website_alternative_product()
        if alternatives:
            return alternatives[:limit]

        if not self.public_categ_ids:
            return self.env['product.template']

        website = self.env['website'].get_current_website()
        domain = website.sale_product_domain() & Domain([
            ('id', '!=', self.id),
            ('public_categ_ids', 'child_of', self.public_categ_ids.ids),
        ])
        return self.env['product.template'].search(
            domain,
            limit=limit,
            order='website_sequence desc, id desc',
        )
