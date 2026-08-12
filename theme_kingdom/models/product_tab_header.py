# -*- coding: utf-8 -*-

from odoo import api, fields, models


class KingdomProductTabHeader(models.Model):
    _inherit = 'kingdom.product.tab'

    show_in_header_menu = fields.Boolean(
        string='Header menu',
        default=False,
        help='Show as a top link in the website header (synced to Website → Configuration → Menus).',
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_header_menus()
        return records

    def write(self, vals):
        res = super().write(vals)
        sync_fields = {
            'name', 'active', 'show_in_header_menu', 'sequence',
            'tab_type', 'feature_url', 'category_id',
        }
        if sync_fields.intersection(vals):
            self._sync_header_menus()
        return res

    def unlink(self):
        menus = self.env['website.menu'].sudo().search([
            ('kingdom_product_tab_id', 'in', self.ids),
        ])
        res = super().unlink()
        menus.unlink()
        return res

    def _sync_header_menus(self):
        """Create or update website header menus linked to Product Tabs."""
        Menu = self.env['website.menu'].sudo()
        websites = self.env['website'].search([])
        tabs = self.sudo().search([])

        for website in websites:
            root = website.menu_id
            if not root:
                continue
            for tab in tabs:
                menu = Menu.search([
                    ('website_id', '=', website.id),
                    ('kingdom_product_tab_id', '=', tab.id),
                ], limit=1)
                if tab.active and tab.show_in_header_menu:
                    # Write menu labels in the website default language so
                    # existing translations (e.g. Arabic) are not overwritten.
                    lang = website.default_lang_id.code
                    vals = {
                        'name': tab.with_context(lang=lang).name,
                        'url': tab.get_menu_url(),
                        'parent_id': root.id,
                        'website_id': website.id,
                        'sequence': tab.sequence,
                        'kingdom_product_tab_id': tab.id,
                    }
                    if menu:
                        menu.with_context(lang=lang).write(vals)
                    else:
                        Menu.with_context(lang=lang).create(vals)
                elif menu:
                    menu.unlink()
