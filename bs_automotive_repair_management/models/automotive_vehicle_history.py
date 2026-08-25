from odoo import fields, models


class AutomotiveVehicleHistory(models.Model):
    _name = 'automotive.vehicle.history'
    _description = 'Vehicle Service History'
    _order = 'date desc'

    vehicle_id = fields.Many2one('automotive.vehicle', required=True, ondelete='cascade', index=True)
    repair_order_id = fields.Many2one('automotive.repair.order', required=True, ondelete='cascade')
    date = fields.Date(required=True)
    summary = fields.Char()
    total_amount = fields.Monetary(currency_field='currency_id')
    currency_id = fields.Many2one(related='repair_order_id.currency_id')
