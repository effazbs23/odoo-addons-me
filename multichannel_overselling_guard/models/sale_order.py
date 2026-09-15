from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_multichannel_channel(self):
        """Which channel this order counts as under this module's channel
        definition. Website orders are unambiguous (`website_id` is set by
        website_sale). For anything else, this module treats an order
        created by a portal user (no internal login, `share` is True) as a
        self-service B2B order -- a documented heuristic, since Odoo has no
        single flag meaning "this is a B2B portal order". Orders entered
        directly by internal sales staff are not treated as a soft-reserved
        channel: their stock commitment goes through core's own reservation
        at confirmation, same as before this module existed.
        """
        self.ensure_one()
        if self.website_id:
            return 'website'
        if self.create_uid and self.create_uid.share:
            return 'b2b'
        return False

    def _graduate_multichannel_soft_reservations(self):
        """Move this order's own active soft holds to 'confirmed' so they
        stop being double-counted against the real stock reservation core
        Odoo now holds for it (per the design: the hold graduates into a
        real reservation rather than being released/vanishing)."""
        self.ensure_one()
        reservations = self.env['stock.soft.reservation'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', self.id),
            ('state', '=', 'active'),
        ])
        reservations.action_confirm()

    def _check_multichannel_oversell(self):
        """Safety-net check (design note 4): run *after* this order's own
        soft holds have graduated to 'confirmed', so the active-reservation
        total used here reflects only what other channels/orders still have
        open -- exactly what this order was competing against."""
        self.ensure_one()
        warehouse = self.warehouse_id
        if not warehouse:
            return
        Alert = self.env['multichannel.oversell.alert']
        channel = self._get_multichannel_channel() or 'other'
        for line in self.order_line:
            product = line.product_id
            if not product:
                continue
            Alert._check_and_flag_oversell(
                product=product,
                warehouse=warehouse,
                channel=channel,
                requested_qty=line.product_uom_qty,
                sale_order=self,
            )

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            order._graduate_multichannel_soft_reservations()
            order._check_multichannel_oversell()
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._sync_multichannel_soft_reservation()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if 'product_uom_qty' in vals or 'product_id' in vals:
            self._sync_multichannel_soft_reservation()
        return res

    def _sync_multichannel_soft_reservation(self):
        """Put/refresh a soft hold for this line while its order is still
        draft/sent (design note 1 + 2: the soft hold is what makes an
        in-progress website/B2B cart visible to the other channels' checks
        before it is ever confirmed)."""
        SoftReservation = self.env['stock.soft.reservation']
        for line in self:
            order = line.order_id
            if order.state not in ('draft', 'sent'):
                continue
            product = line.product_id
            if not product:
                continue
            category = product.categ_id
            if not category or not category._is_overselling_guard_enabled():
                continue
            channel = order._get_multichannel_channel()
            if not channel:
                continue
            warehouse = order.warehouse_id
            if not warehouse:
                continue
            SoftReservation._sync_soft_reservation(
                product_id=product.id,
                warehouse_id=warehouse.id,
                channel=channel,
                quantity=line.product_uom_qty,
                res_model='sale.order',
                res_id=order.id,
            )
