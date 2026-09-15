from odoo import api, models

# States a POS order can be synced to the backend in that this module treats
# as "final" (payment/settlement already happened at the register).
POS_FINAL_STATES = ('paid', 'done', 'invoiced')


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _get_multichannel_warehouse(self):
        self.ensure_one()
        # UNVERIFIED in this environment (no vendored core `point_of_sale`
        # source to confirm against): assumes `pos.config.picking_type_id`
        # resolves to a `stock.picking.type` with a `warehouse_id`, which is
        # the standard Odoo POS <-> stock link. Verify against the target
        # instance before relying on this in production.
        return self.config_id.picking_type_id.warehouse_id if self.config_id else False

    def _sync_multichannel_soft_reservations(self):
        """Create/refresh soft holds for this order's lines.

        Deviation, documented per design note 3: this piggybacks on Odoo's
        existing POS order sync from the register to the backend (create()/
        write() on `pos.order`) rather than a true live per-keystroke POS
        Owl JS hook. In standard POS flows an order is usually only synced
        to the backend around payment/closing, not while the cart is still
        being built at the register -- so, honestly, the soft hold this
        creates mostly overlaps with the order becoming final rather than
        pre-empting it during cart-building. Implementing the latter needs a
        POS frontend (Owl) patch and a live browser/POS session to build and
        test against, which is not available in this environment; flagged
        here as the v2 item.
        """
        SoftReservation = self.env['stock.soft.reservation']
        for order in self:
            if order.state == 'cancel':
                continue
            warehouse = order._get_multichannel_warehouse()
            if not warehouse:
                continue
            qty_by_product = {}
            for line in order.lines:
                product = line.product_id
                if not product:
                    continue
                category = product.categ_id
                if not category or not category._is_overselling_guard_enabled():
                    continue
                qty_by_product[product.id] = qty_by_product.get(product.id, 0.0) + line.qty
            for product_id, qty in qty_by_product.items():
                SoftReservation._sync_soft_reservation(
                    product_id=product_id,
                    warehouse_id=warehouse.id,
                    channel='pos',
                    quantity=qty,
                    res_model='pos.order',
                    res_id=order.id,
                )

    def _graduate_multichannel_soft_reservations(self):
        self.ensure_one()
        reservations = self.env['stock.soft.reservation'].search([
            ('res_model', '=', 'pos.order'),
            ('res_id', '=', self.id),
            ('state', '=', 'active'),
        ])
        reservations.action_confirm()

    def _check_multichannel_oversell(self):
        """Safety-net check (design note 4), run once the order becomes
        final and its own soft holds have graduated to 'confirmed'."""
        self.ensure_one()
        warehouse = self._get_multichannel_warehouse()
        if not warehouse:
            return
        Alert = self.env['multichannel.oversell.alert']
        qty_by_product = {}
        for line in self.lines:
            product = line.product_id
            if not product:
                continue
            qty_by_product[product] = qty_by_product.get(product, 0.0) + line.qty
        for product, qty in qty_by_product.items():
            Alert._check_and_flag_oversell(
                product=product,
                warehouse=warehouse,
                channel='pos',
                requested_qty=qty,
                pos_order=self,
            )

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._sync_multichannel_soft_reservations()
        for order in orders:
            if order.state in POS_FINAL_STATES:
                order._graduate_multichannel_soft_reservations()
                order._check_multichannel_oversell()
        return orders

    def write(self, vals):
        # UNVERIFIED/conservative hook (design note 3 + spec item 6): with no
        # live POS session to confirm the exact core method that finalizes an
        # order (e.g. `_process_order`), this keys off `write()` seeing the
        # `state` field transition into a final state instead, which is the
        # most conservative, always-present hook available.
        previous_states = {order.id: order.state for order in self}
        res = super().write(vals)
        if 'lines' in vals or 'state' in vals:
            self._sync_multichannel_soft_reservations()
        if 'state' in vals:
            for order in self:
                if previous_states.get(order.id) not in POS_FINAL_STATES and order.state in POS_FINAL_STATES:
                    order._graduate_multichannel_soft_reservations()
                    order._check_multichannel_oversell()
        return res
