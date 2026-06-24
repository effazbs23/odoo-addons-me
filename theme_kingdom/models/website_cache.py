# -*- coding: utf-8 -*-
from odoo import api, models


class KingdomWebsiteCacheMixin(models.AbstractModel):
    _name = 'kingdom.website.cache.mixin'
    _description = 'Invalidate website page cache when Kingdom snippet data changes'

    def _invalidate_kingdom_website_cache(self):
        self.env.registry.clear_cache('templates')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._invalidate_kingdom_website_cache()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._invalidate_kingdom_website_cache()
        return res

    def unlink(self):
        res = super().unlink()
        self._invalidate_kingdom_website_cache()
        return res
