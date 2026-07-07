from odoo import api, models, fields


class ProductPublicCategory(models.Model):
    _inherit = ['product.public.category', 'kingdom.website.cache.mixin']

    show_in_homepage = fields.Boolean(
        string='Show in Homepage',
        default=False,
    )

    @api.model
    def kingdom_get_header_roots(self):
        """Root eCommerce categories for the Kingdom header (public-safe)."""
        return self.sudo().search(
            [('parent_id', '=', False)],
            order='sequence, name, id',
        )

    @api.model
    def get_homepage_featured_categories(self, limit=8):
        """Root categories flagged for the Featured Categories snippet."""
        return self.sudo().search(
            [
                ('parent_id', '=', False),
                ('show_in_homepage', '=', True),
            ],
            order='sequence, name, id',
            limit=limit,
        )

    def kingdom_get_header_children(self):
        """Direct child categories for a header menu item (public-safe)."""
        self.ensure_one()
        return self.sudo().child_id

    def write(self, vals):
        res = super().write(vals)
        if 'show_in_homepage' in vals:
            self._invalidate_kingdom_website_cache()
        return res

