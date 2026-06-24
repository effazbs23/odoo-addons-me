from odoo import api, models, fields


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

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

    def kingdom_get_header_children(self):
        """Direct child categories for a header menu item (public-safe)."""
        self.ensure_one()
        return self.sudo().child_id

    def write(self, vals):
        res = super().write(vals)
        if 'show_in_homepage' in vals:
            self.env.registry.clear_cache('templates')
        return res
