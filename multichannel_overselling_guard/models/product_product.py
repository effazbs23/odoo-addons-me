from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_reserved_buffer_qty(self, warehouse_id):
        """Explicit `multichannel.stock.buffer` row for this product and
        warehouse if one exists, otherwise the product's effective category
        default (climbing to parent categories)."""
        self.ensure_one()
        if hasattr(warehouse_id, 'id'):
            warehouse_id = warehouse_id.id
        buffer = self.env['multichannel.stock.buffer'].search([
            ('product_id', '=', self.id),
            ('warehouse_id', '=', warehouse_id),
        ], limit=1)
        if buffer:
            return buffer.buffer_qty
        return self.categ_id._get_effective_default_buffer_qty() if self.categ_id else 0.0

    def get_sellable_now(self, warehouse_id):
        """What is actually sellable right now for this product at this
        warehouse, across every channel.

        Guarding is opt-in per product category (feature 5): when the
        product's effective category setting has the guard disabled, this
        behaves like a plain product and simply returns on-hand quantity.
        When enabled, it returns on-hand minus the configured reserved
        buffer minus any still-active soft reservations from other channels.

        `warehouse_id` may be passed as either an int id or a
        `stock.warehouse` recordset.
        """
        self.ensure_one()
        if hasattr(warehouse_id, 'id'):
            warehouse_id = warehouse_id.id
        on_hand = self.with_context(warehouse=warehouse_id).qty_available
        if not self.categ_id or not self.categ_id._is_overselling_guard_enabled():
            return on_hand
        buffer_qty = self._get_reserved_buffer_qty(warehouse_id)
        reserved_qty = self.env['stock.soft.reservation']._get_active_reserved_qty(
            self.id, warehouse_id)
        return on_hand - buffer_qty - reserved_qty
