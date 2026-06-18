# -*- coding: utf-8 -*-
from odoo import api, fields, models


class KingdomManufacturer(models.Model):
    _name = 'kingdom.manufacturer'
    _description = 'Kingdom Manufacturer / Brand'
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
        help='Include this brand in the homepage manufacturers carousel.',
    )
    image = fields.Image(
        string='Logo',
        max_width=512,
        max_height=256,
    )
    website_url = fields.Char(
        string='Website URL',
        help='Destination when visitors click the brand on the homepage.',
    )

    @api.model
    def get_website_manufacturer_slides(self, per_slide=2):
        """Manufacturers grouped in pairs for the homepage carousel."""
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
