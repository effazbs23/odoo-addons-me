# -*- coding: utf-8 -*-
from odoo import api, fields, models


class KingdomManufacturer(models.Model):
    _name = 'kingdom.manufacturer'
    _inherit = ['kingdom.website.cache.mixin']
    _description = 'Kingdom Brand'
    _order = 'sequence, name, id'

    name = fields.Char(
        required=True,
        string='Name',
        help='Brand name shown when no logo image is uploaded.',
    )
    sequence = fields.Integer(default=10)
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
        'kingdom_manufacturer_id',
        string='Product Templates',
    )
    product_count = fields.Integer(
        string='Products',
        compute='_compute_product_count',
    )

    @api.depends('product_ids')
    def _compute_product_count(self):
        grouped = self.env['product.template']._read_group(
            [('kingdom_manufacturer_id', 'in', self.ids)],
            ['kingdom_manufacturer_id'],
            ['__count'],
        )
        counts = {manufacturer.id: count for manufacturer, count in grouped}
        for manufacturer in self:
            manufacturer.product_count = counts.get(manufacturer.id, 0)

    def action_view_products(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Products',
            'res_model': 'product.template',
            'view_mode': 'kanban,list,form',
            'domain': [('kingdom_manufacturer_id', '=', self.id)],
            'context': {
                'default_kingdom_manufacturer_id': self.id,
                'default_sale_ok': True,
            },
        }

    def get_shop_url(self):
        """Shop URL filtered to products of this brand."""
        self.ensure_one()
        return f'/shop?manufacturer={self.id}'

    @api.model
    def get_website_manufacturer_slides(self, per_slide=2):
        """Brands grouped in pairs for the homepage carousel."""
        manufacturers = self.sudo().search(
            [('active', '=', True), ('show_on_homepage', '=', True)],
            order='sequence asc, id asc',
        )
        if not manufacturers:
            return []
        slides = []
        batch = self.browse()
        for manufacturer in manufacturers:
            batch |= manufacturer
            if len(batch) >= per_slide:
                slides.append(batch)
                batch = self.browse()
        if batch:
            slides.append(batch)
        return slides
