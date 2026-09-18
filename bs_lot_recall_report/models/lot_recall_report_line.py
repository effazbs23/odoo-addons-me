from odoo import fields, models


class LotRecallReportLine(models.Model):
    _name = 'lot.recall.report.line'
    _description = 'Lot Recall Report Line'
    _order = 'direction, delivery_date desc, id'

    report_id = fields.Many2one(
        'lot.recall.report', string='Recall Report',
        required=True, ondelete='cascade', index=True)
    lot_id = fields.Many2one(
        'stock.lot', string='Traced Lot/Serial', required=True, index=True,
        help='The lot/serial number this line was generated for. Useful '
             'when a report covers several lots at once (batch mode).')
    direction = fields.Selection([
        ('forward', 'Forward'),
        ('backward', 'Backward'),
    ], required=True, index=True)
    source_type = fields.Selection([
        ('sale', 'Customer Delivery'),
        ('purchase', 'Vendor Receipt'),
        ('manufacturing', 'Manufacturing Order'),
    ], required=True)
    partner_id = fields.Many2one(
        'res.partner', string='Partner',
        help='Customer (forward trace) or vendor (backward trace).')
    sale_order_id = fields.Many2one('sale.order', string='Sales Order')
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    production_id = fields.Many2one('mrp.production', string='Manufacturing Order')
    delivery_id = fields.Many2one(
        'stock.picking', string='Delivery / Receipt',
        help='The outgoing delivery (forward trace) or incoming receipt '
             '(backward trace) transfer.')
    component_lot_id = fields.Many2one(
        'stock.lot', string='Component Lot/Serial',
        help='For manufacturing rows, the raw material lot/serial consumed '
             'to produce the traced lot.')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Quantity', digits='Product Unit of Measure')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    delivery_date = fields.Datetime(string='Date')
