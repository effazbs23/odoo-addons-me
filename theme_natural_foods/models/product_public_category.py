# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.fields import Domain


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    show_in_main_nav = fields.Boolean(
        string="Show in main navigation",
        default=False,
        help="When enabled, this category is listed in the website header category menu "
        "(desktop bar and mobile shop submenu) for this website.",
    )

    @api.model
    def natural_foods_navbar_categories(self, website=None):
        """Recordset of eCommerce categories to render in the theme navbar."""
        website = website or self.env['website'].get_current_website()
        if not website:
            return self.browse()
        domain = (
            website.website_domain()
            & Domain('show_in_main_nav', '=', True)
            & Domain('has_published_products', '=', True)
        )
        return self.sudo().search(domain, order='sequence, id')
