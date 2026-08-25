from odoo import api, models, fields


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    show_in_homepage = fields.Boolean(
        string='Show in Homepage',
        default=False,
    )

    @api.model
    def kingdom_get_header_roots(self):
        """Root eCommerce categories for the Kingdom header (public-safe).

        Prefetches two levels of children so the mega-menu QWeb walk does not
        N+1 query on every page.
        """
        roots = self.sudo().search(
            [('parent_id', '=', False)],
            order='sequence, name, id',
        )
        # Warm the ORM cache for child / grandchild records.
        roots.mapped('child_id.child_id')
        return roots

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
        return self.child_id
