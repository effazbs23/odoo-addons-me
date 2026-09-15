from odoo import api, fields, models


class MultichannelStockBuffer(models.Model):
    _name = 'multichannel.stock.buffer'
    _description = 'Multichannel Reserved Stock Buffer'
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', required=True, index=True,
                                  string='Product', ondelete='cascade')
    warehouse_id = fields.Many2one('stock.warehouse', required=True, index=True,
                                    string='Warehouse', ondelete='cascade')
    buffer_qty = fields.Float(string='Reserved Buffer',
                               help='Quantity held back from online/POS sale to '
                                    'absorb timing gaps between channels.')
    on_hand = fields.Float(compute='_compute_on_hand', string='On Hand')
    buffer_percent = fields.Float(compute='_compute_buffer_percent', string='Buffer %')

    _sql_constraints = [
        ('product_warehouse_uniq', 'unique(product_id, warehouse_id)',
         'Only one reserved buffer is allowed per product and warehouse.'),
    ]

    @api.depends('product_id', 'warehouse_id')
    def _compute_on_hand(self):
        for buffer in self:
            if buffer.product_id and buffer.warehouse_id:
                buffer.on_hand = buffer.product_id.with_context(
                    warehouse=buffer.warehouse_id.id).qty_available
            else:
                buffer.on_hand = 0.0

    @api.depends('buffer_qty', 'on_hand')
    def _compute_buffer_percent(self):
        for buffer in self:
            buffer.buffer_percent = (buffer.buffer_qty / buffer.on_hand * 100.0) if buffer.on_hand else 0.0
