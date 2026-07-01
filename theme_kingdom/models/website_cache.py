# -*- coding: utf-8 -*-
from odoo import api, fields, models


class KingdomWebsiteCacheMixin(models.AbstractModel):
    _name = 'kingdom.website.cache.mixin'
    _description = 'Invalidate website page cache when Kingdom snippet data changes'

    def _invalidate_kingdom_website_cache(self):
        self.env.registry.clear_cache('templates')
        if 'website.page' in self.env:
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
