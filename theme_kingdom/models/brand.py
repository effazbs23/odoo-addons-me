# -*- coding: utf-8 -*-
from odoo import api, fields, models


class KingdomBrand(models.Model):
    """Storefront brand shown in the Brands carousel and shop filters."""
    _name = 'kingdom.brand'
    _inherit = ['kingdom.website.cache.mixin']
    _description = 'Kingdom Brand'
    _order = 'name, id'

    name = fields.Char(
        required=True,
        string='Name',
        help='Brand name shown when no logo image is uploaded.',
    )
    sequence = fields.Integer(
        default=10,
        help='Technical order field (hidden). Brands are ordered by name.',
    )
    active = fields.Boolean(default=True)
    show_on_homepage = fields.Boolean(
        string='Show on Homepage',
        default=True,
        help='Include this brand in the homepage brands carousel.',
    )
    image = fields.Image(
        string='Logo',
        max_width=512,
        max_height=256,
    )
    product_ids = fields.One2many(
        'product.template',
        'kingdom_brand_id',
        string='Product Templates',
    )
    product_count = fields.Integer(
        string='Products',
        compute='_compute_product_count',
    )
    website_url = fields.Char(
        string='Website URL',
        compute='_compute_website_url',
    )

    @api.depends('product_ids')
    def _compute_product_count(self):
        grouped = self.env['product.template']._read_group(
            [('kingdom_brand_id', 'in', self.ids)],
            ['kingdom_brand_id'],
            ['__count'],
        )
        counts = {brand.id: count for brand, count in grouped}
        for brand in self:
            brand.product_count = counts.get(brand.id, 0)

    @api.depends('name')
    def _compute_website_url(self):
        for brand in self:
            brand.website_url = brand.get_shop_url() if brand.id else '/brand'

    def action_view_products(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Products',
            'res_model': 'product.template',
            'view_mode': 'kanban,list,form',
            'domain': [('kingdom_brand_id', '=', self.id)],
            'context': {
                'default_kingdom_brand_id': self.id,
                'default_sale_ok': True,
            },
        }

    def get_shop_url(self):
        """Pretty brand shop URL: /brand/<slug-id>."""
        self.ensure_one()
        return f'/brand/{self.env["ir.http"]._slug(self)}'

    @api.model
    def get_website_brand_slides(self, per_slide=2):
        """Brands grouped in pairs for the homepage carousel."""
        brands = self.sudo().search(
            [('active', '=', True), ('show_on_homepage', '=', True)],
            order='name asc, id asc',
        )
        if not brands:
            return []
        slides = []
        batch = self.browse()
        for brand in brands:
            batch |= brand
            if len(batch) >= per_slide:
                slides.append(batch)
                batch = self.browse()
        if batch:
            slides.append(batch)
        return slides

    @api.model
    def get_shop_filter_brands(self, website=None):
        """Active brands for the shop sidebar filter.

        Prefer brands that have published products on the website; if none do,
        fall back to all active brands so the filter stays usable after setup.
        """
        website = website or self.env['website'].get_current_website()
        Product = self.env['product.template'].sudo()
        domain = [
            ('is_published', '=', True),
            ('sale_ok', '=', True),
            ('kingdom_brand_id', '!=', False),
        ]
        if website:
            domain = domain + website.website_domain()
        # Collect distinct brand ids without loading every product record.
        grouped = Product._read_group(
            domain,
            groupby=['kingdom_brand_id'],
            aggregates=['__count'],
        )
        brand_ids = [brand.id for brand, _count in grouped if brand]
        brand_domain = [('active', '=', True)]
        if brand_ids:
            brand_domain.append(('id', 'in', brand_ids))
        return self.sudo().search(
            brand_domain,
            order='name asc, id asc',
        )

    # Backwards-compatible alias used by older QWeb / website copies.
    @api.model
    def get_website_manufacturer_slides(self, per_slide=2):
        return self.get_website_brand_slides(per_slide=per_slide)
