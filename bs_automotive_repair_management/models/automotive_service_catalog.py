from odoo import fields, models


class AutomotiveServiceCatalog(models.Model):
    _name = 'automotive.service.catalog'
    _description = 'Repair Service Catalog'
    _order = 'name'

    name = fields.Char(required=True)
    estimated_hours = fields.Float(string='Estimated Hours', required=True, default=1.0)
    default_hourly_rate = fields.Float(string='Default Hourly Rate')
    active = fields.Boolean(default=True)
