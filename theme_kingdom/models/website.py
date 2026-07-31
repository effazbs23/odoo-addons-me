# -*- coding: utf-8 -*-
from odoo import models


class Website(models.Model):
    _inherit = 'website'

    def _kingdom_model(self, model_name):
        """Return sudoed model env, or None if the model is not installed."""
        if model_name not in self.env:
            return None
        return self.env[model_name].sudo()

    def kingdom_featured_record(self):
        Featured = self._kingdom_model('featured.products')
        if Featured is None:
            return self.env['featured.products']
        return Featured.get_website_featured_record()

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
        Bestsale = self._kingdom_model('bestsale.products')
        if Bestsale is None:
            return self.env['bestsale.products']
        return Bestsale.get_website_bestsale_record()

    def kingdom_bestsale_products(self, limit=12):
        record = self.kingdom_bestsale_record()
        if record:
            return record.get_website_products(limit=limit)
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

    def kingdom_active_deal(self):
        Deals = self._kingdom_model('kingdom.deals.of.day')
        if Deals is None:
            return self.env['kingdom.deals.of.day']
        return Deals.get_website_deal()

    def kingdom_preview_deal(self):
        Deals = self._kingdom_model('kingdom.deals.of.day')
        if Deals is None:
            return self.env['kingdom.deals.of.day']
        return Deals.get_preview_deal()

    def kingdom_dual_carousel_tabs(self, limit=2):
        Tab = self._kingdom_model('kingdom.product.tab')
        if Tab is None:
            return self.env['kingdom.product.tab']
        return Tab.get_website_dual_carousel_tabs(limit=limit)

    def kingdom_dynamic_tabs(self, limit=8):
        Tab = self._kingdom_model('kingdom.product.tab')
        if Tab is None:
            return self.env['kingdom.product.tab']
        return Tab.get_dynamic_tabs(limit=limit)

    def kingdom_manufacturer_slides(self, per_slide=2):
        Manufacturer = self._kingdom_model('kingdom.manufacturer')
        if Manufacturer is None:
            return []
        return Manufacturer.get_website_manufacturer_slides(per_slide=per_slide)

    def kingdom_product_tab(self):
        Tab = self._kingdom_model('kingdom.product.tab')
        return Tab if Tab is not None else self.env['kingdom.product.tab']

    def kingdom_should_redirect_coming_soon(self, user=None):
        """True when public (non-designer) visitors must stay on Coming Soon."""
        self.ensure_one()
        if not self.kingdom_coming_soon_enabled:
            return False
        user = user or self.env.user
        if user.has_group('website.group_website_designer'):
            return False
        return True
