from datetime import timedelta

from odoo import api, fields, models

# Default lifetime of a soft hold before it is auto-expired by the cron, used
# only when the `multichannel_overselling_guard.reservation_timeout_minutes`
# ir.config_parameter has not been set.
DEFAULT_RESERVATION_TIMEOUT_MINUTES = 15


class StockSoftReservation(models.Model):
    _name = 'stock.soft.reservation'
    _description = 'Multichannel Soft Stock Reservation'
    _order = 'create_date desc'

    product_id = fields.Many2one('product.product', required=True, index=True,
                                  string='Product', ondelete='cascade')
    warehouse_id = fields.Many2one('stock.warehouse', required=True, index=True,
                                    string='Warehouse', ondelete='cascade')
    quantity = fields.Float(required=True, string='Quantity')
    channel = fields.Selection([
        ('pos', 'POS'),
        ('website', 'eCommerce'),
        ('b2b', 'B2B'),
        ('other', 'Other'),
    ], required=True, string='Channel')
    res_model = fields.Char(string='Origin Model',
                             help='Technical model of the order this soft hold '
                                  'originates from (e.g. sale.order, pos.order).')
    res_id = fields.Integer(string='Origin Record ID')
    origin_display_name = fields.Char(compute='_compute_origin_display_name',
                                       string='Origin')
    state = fields.Selection([
        ('active', 'Active'),
        ('confirmed', 'Confirmed'),
        ('expired', 'Expired'),
        ('released', 'Released'),
    ], required=True, default='active', index=True, string='Status')
    expires_at = fields.Datetime(string='Reserved Until')

    @api.model_create_multi
    def create(self, vals_list):
        timeout_minutes = self._get_reservation_timeout_minutes()
        now = fields.Datetime.now()
        for vals in vals_list:
            if not vals.get('expires_at'):
                vals['expires_at'] = now + timedelta(minutes=timeout_minutes)
        return super().create(vals_list)

    @api.model
    def _get_reservation_timeout_minutes(self):
        param = self.env['ir.config_parameter'].sudo().get_param(
            'multichannel_overselling_guard.reservation_timeout_minutes')
        try:
            return int(param) if param else DEFAULT_RESERVATION_TIMEOUT_MINUTES
        except ValueError:
            return DEFAULT_RESERVATION_TIMEOUT_MINUTES

    @api.depends('res_model', 'res_id')
    def _compute_origin_display_name(self):
        for reservation in self:
            name = False
            if reservation.res_model and reservation.res_id:
                record = self.env[reservation.res_model].browse(reservation.res_id).exists()
                if record:
                    name = record.display_name
            reservation.origin_display_name = name or ''

    def action_open_origin(self):
        """Open whichever sale.order/pos.order record this soft hold came from."""
        self.ensure_one()
        if not (self.res_model and self.res_id):
            return False
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.res_model,
            'res_id': self.res_id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_release(self):
        self.write({'state': 'released'})

    def action_confirm(self):
        """Called once the originating order is actually confirmed: the real
        stock reservation now exists via core Odoo (sale/stock reservation,
        POS payment), so this soft hold should stop being counted as an
        active reservation. The record is kept, not deleted, for audit and
        for the 'Reserved' figure in the Sellable Now report."""
        self.write({'state': 'confirmed'})

    @api.model
    def _get_active_reserved_qty(self, product_id, warehouse_id):
        """Sum of quantity currently held (state='active', not yet expired)
        for one product at one warehouse, across all channels."""
        if hasattr(product_id, 'id'):
            product_id = product_id.id
        if hasattr(warehouse_id, 'id'):
            warehouse_id = warehouse_id.id
        reservations = self.search([
            ('product_id', '=', product_id),
            ('warehouse_id', '=', warehouse_id),
            ('state', '=', 'active'),
            ('expires_at', '>', fields.Datetime.now()),
        ])
        return sum(reservations.mapped('quantity'))

    @api.model
    def _sync_soft_reservation(self, product_id, warehouse_id, channel, quantity, res_model, res_id):
        """Create or update the single active soft hold for one order's
        (res_model, res_id) + product, so re-syncing an order that changed
        its quantity updates the existing hold instead of piling up rows.
        A quantity of zero or less releases the hold instead of writing 0.
        """
        existing = self.search([
            ('res_model', '=', res_model),
            ('res_id', '=', res_id),
            ('product_id', '=', product_id),
            ('state', '=', 'active'),
        ], limit=1)
        if quantity <= 0:
            existing.action_release()
            return existing
        if existing:
            existing.write({'quantity': quantity, 'warehouse_id': warehouse_id})
            return existing
        return self.create({
            'product_id': product_id,
            'warehouse_id': warehouse_id,
            'quantity': quantity,
            'channel': channel,
            'res_model': res_model,
            'res_id': res_id,
        })

    @api.model
    def _cron_expire_soft_reservations(self):
        expired = self.search([
            ('state', '=', 'active'),
            ('expires_at', '<', fields.Datetime.now()),
        ])
        expired.write({'state': 'expired'})
