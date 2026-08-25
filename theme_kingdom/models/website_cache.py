# -*- coding: utf-8 -*-
from odoo import api, fields, models


class KingdomWebsiteCacheMixin(models.AbstractModel):
    _name = 'kingdom.website.cache.mixin'
    _description = 'Invalidate website page cache when Kingdom snippet data changes'

    def _invalidate_kingdom_website_cache(self):
        """Bump homepage write_date so website page cache refreshes.

        Do NOT call registry.clear_cache('templates') here — that nukes the
        global QWeb compile cache on every brand/tab/deal/category write and
        makes the next public page hit much slower.
        """
        if 'website.page' not in self.env:
            return
        pages = self.env['website.page'].sudo().search([
            ('url', 'in', ('/', '/home')),
        ])
        if pages:
            pages.write({'write_date': fields.Datetime.now()})

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
