# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.http import request


class ProductWishlist(models.Model):
    _inherit = 'product.wishlist'

    @api.model
    def current(self):
        """Avoid crash when request has no website (builder / render_public_asset)."""
        try:
            website = getattr(request, 'website', None)
        except RuntimeError:
            website = None
        if website is None:
            return self.browse()
        return super().current()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def kingdom_is_in_wishlist(self):
        """QWeb-safe wishlist check (no request.website required)."""
        self.ensure_one()
        try:
            if getattr(request, 'website', None) is None:
                return False
        except RuntimeError:
            return False
        return self._is_in_wishlist()
