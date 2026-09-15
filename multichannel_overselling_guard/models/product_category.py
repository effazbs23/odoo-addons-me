from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    overselling_guard_enabled = fields.Boolean(
        string='Overselling Guard Enabled', default=False,
        help='Apply the multichannel overselling guard (reserved buffer + '
             'soft reservations) to products in this category, e.g. '
             'fast-moving or limited-stock SKUs. Left off by default so the '
             'guard is opt-in per category, not applied to every product.')
    default_reserved_buffer_qty = fields.Float(
        string='Default Reserved Buffer',
        help='Fallback reserved buffer quantity for products in this category '
             'that have no explicit Reserved Buffer configuration line.')

    def _is_overselling_guard_enabled(self):
        """Whether the guard should apply, climbing to the parent category
        when this category has not enabled it itself.

        NOTE (documented deviation): `overselling_guard_enabled` is a plain
        Boolean, so it has no distinct "not set" state -- False is used both
        for "explicitly disabled" and "not configured". This method treats
        False as "not configured" and keeps climbing, mirroring the
        recursive-lookup pattern core Odoo uses for category-inherited
        settings. The tradeoff: a category cannot explicitly opt back OUT of
        guarding once an ancestor has it enabled. A tri-state field would
        remove this ambiguity in a v2.
        """
        category = self
        while category:
            if category.overselling_guard_enabled:
                return True
            category = category.parent_id
        return False

    def _get_effective_default_buffer_qty(self):
        """Same climb-to-parent fallback as `_is_overselling_guard_enabled`,
        for the default buffer quantity: the first non-zero value found
        walking up the category tree, or 0.0 if none is set anywhere."""
        category = self
        while category:
            if category.default_reserved_buffer_qty:
                return category.default_reserved_buffer_qty
            category = category.parent_id
        return 0.0
