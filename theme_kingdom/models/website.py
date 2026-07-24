# -*- coding: utf-8 -*-
from odoo import models


class Website(models.Model):
    _inherit = 'website'

    def _kingdom_sudo(self, model_name):
        """Return a sudoed model recordset factory, or None if unavailable."""
        if model_name not in self.env:
            return None
        return self.env[model_name].sudo()

    def kingdom_featured_record(self):
        Featured = self._kingdom_sudo('featured.products')
        return Featured.search([], limit=1) if Featured else False

    def kingdom_featured_products(self, limit=12):
        record = self.kingdom_featured_record()
        if record:
            return record.get_website_products(limit=limit)
        return self.env['product.template'].sudo().search(
            [
                ('sale_ok', '=', True),
                ('is_published', '=', True),
            ],
            order='website_sequence desc, id desc',
            limit=limit,
        )

    def kingdom_bestsale_record(self):
        Bestsale = self._kingdom_sudo('bestsale.products')
        return Bestsale.search([], limit=1) if Bestsale else False

    def kingdom_bestsale_products(self, limit=12):
        record = self.kingdom_bestsale_record()
        if record:
            return record.get_website_products(limit=limit)
        return self.env['product.template'].sudo().search(
            [
                ('sale_ok', '=', True),
                ('is_published', '=', True),
            ],
            order='website_sequence desc, id desc',
            limit=limit,
        )

    def kingdom_active_deal(self):
        Deals = self._kingdom_sudo('kingdom.deals.of.day')
        return Deals.get_website_deal() if Deals else False

    def kingdom_preview_deal(self):
        Deals = self._kingdom_sudo('kingdom.deals.of.day')
        return Deals.get_preview_deal() if Deals else False

    def kingdom_dual_carousel_tabs(self, limit=2):
        Tab = self._kingdom_sudo('kingdom.product.tab')
        if not Tab:
            return False
        return Tab.get_website_dual_carousel_tabs(limit=limit)

    def kingdom_product_tab(self):
        return self._kingdom_sudo('kingdom.product.tab')

    def kingdom_should_redirect_coming_soon(self, user=None):
        """True when public (non-designer) visitors should see Coming Soon."""
        self.ensure_one()
        if not self.kingdom_coming_soon_enabled:
            return False
        user = user or self.env.user
        if user.has_group('website.group_website_designer'):
            return False
        return True
