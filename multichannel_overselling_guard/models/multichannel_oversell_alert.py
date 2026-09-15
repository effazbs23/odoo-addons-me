from odoo import api, fields, models


class MultichannelOversellAlert(models.Model):
    _name = 'multichannel.oversell.alert'
    _description = 'Multichannel Oversell Alert'
    _order = 'create_date desc'

    product_id = fields.Many2one('product.product', required=True, string='Product')
    channel = fields.Selection([
        ('pos', 'POS'),
        ('website', 'eCommerce'),
        ('b2b', 'B2B'),
        ('other', 'Other'),
    ], required=True, string='Channel')
    sale_order_id = fields.Many2one('sale.order', string='Sales Order')
    pos_order_id = fields.Many2one('pos.order', string='POS Order')
    requested_qty = fields.Float(string='Requested Qty')
    available_qty = fields.Float(string='Available to Promise')
    oversell_qty = fields.Float(compute='_compute_oversell_qty', store=True, string='Oversell Qty')
    state = fields.Selection([
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
    ], required=True, default='pending', index=True, string='Status')
    note = fields.Text(string='Note')

    @api.depends('requested_qty', 'available_qty')
    def _compute_oversell_qty(self):
        for alert in self:
            diff = alert.requested_qty - alert.available_qty
            alert.oversell_qty = diff if diff > 0 else 0.0

    def action_mark_reviewed(self):
        self.write({'state': 'reviewed'})

    def action_view_order(self):
        """Open whichever of sale_order_id/pos_order_id is set on this alert."""
        self.ensure_one()
        if self.sale_order_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'res_id': self.sale_order_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        if self.pos_order_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'pos.order',
                'res_id': self.pos_order_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return False

    @api.model
    def _check_and_flag_oversell(self, product, warehouse, channel, requested_qty,
                                  sale_order=None, pos_order=None):
        """Safety-net oversell check shared by the sale.order and pos.order
        confirmation hooks (design note 4: defense in depth, not the primary
        mechanism -- the soft reservation is). Deliberately factored out as
        its own model method, testable in isolation with contrived
        quantities, without needing a full website/POS checkout flow.

        Only ever *creates an alert*; it never blocks or reverses the order.
        Returns the created alert record, or an empty recordset when the
        product's category doesn't have the guard enabled or nothing was
        oversold.
        """
        if not product or not warehouse:
            return self.browse()
        category = product.categ_id
        if not category or not category._is_overselling_guard_enabled():
            return self.browse()

        warehouse_id = warehouse.id if hasattr(warehouse, 'id') else warehouse
        on_hand = product.with_context(warehouse=warehouse_id).qty_available
        buffer_qty = product._get_reserved_buffer_qty(warehouse_id)
        other_reserved = self.env['stock.soft.reservation']._get_active_reserved_qty(
            product.id, warehouse_id)
        available_qty = on_hand - buffer_qty - other_reserved

        if (requested_qty - available_qty) <= 0:
            return self.browse()

        return self.create({
            'product_id': product.id,
            'channel': channel or 'other',
            'sale_order_id': sale_order.id if sale_order else False,
            'pos_order_id': pos_order.id if pos_order else False,
            'requested_qty': requested_qty,
            'available_qty': available_qty,
            'state': 'pending',
        })
