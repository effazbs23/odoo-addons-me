from odoo import fields, models


class BsTraceabilityExportLog(models.Model):
    _name = 'bs.traceability.export.log'
    _description = 'Traceability Export Log'
    _order = 'create_date desc'

    lot_id = fields.Many2one('stock.lot', string='Lot/Serial', required=True, index=True)
    direction = fields.Selection([
        ('backward', 'Backward'),
        ('forward', 'Forward'),
        ('both', 'Both'),
    ], required=True, default='both')
    exported_by = fields.Many2one('res.users', string='Exported By', required=True, default=lambda self: self.env.user)
