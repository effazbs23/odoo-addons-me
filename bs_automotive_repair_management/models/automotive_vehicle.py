from odoo import _, api, fields, models


class AutomotiveVehicle(models.Model):
    _name = 'automotive.vehicle'
    _description = 'Customer Vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'automotive.deletion.request.mixin']
    _rec_name = 'display_name'
    _rec_names_search = ['license_plate', 'manufacturer', 'model', 'vin']
    _order = 'license_plate'

    partner_id = fields.Many2one(
        'res.partner', string='Owner', required=True, tracking=True,
        index=True,
    )
    manufacturer = fields.Char(required=True)
    model = fields.Char(required=True)
    year = fields.Char()
    vin = fields.Char(string='VIN')
    license_plate = fields.Char(required=True, tracking=True)
    color = fields.Char()
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company,
        help='Leave empty to share this vehicle across all companies. Set to scope it '
             'to a single company, mirroring automotive.repair.order (§multi-company).',
    )
    fuel_type = fields.Selection([
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
        ('lpg_cng', 'LPG/CNG'),
        ('other', 'Other'),
    ], default='petrol')
    current_mileage = fields.Integer(string='Current Mileage')

    repair_order_ids = fields.One2many(
        'automotive.repair.order', 'vehicle_id', string='Repair Orders',
    )
    repair_order_count = fields.Integer(compute='_compute_repair_order_count')
    history_ids = fields.One2many(
        'automotive.vehicle.history', 'vehicle_id', string='History',
    )

    display_name = fields.Char(compute='_compute_display_name', store=True)

    _license_plate_unique = models.Constraint(
        'unique(license_plate)',
        'A vehicle with this License Plate / Chassis No already exists.',
    )

    @api.depends('manufacturer', 'model', 'license_plate')
    def _compute_display_name(self):
        for vehicle in self:
            parts = [p for p in (vehicle.manufacturer, vehicle.model) if p]
            label = ' '.join(parts)
            if vehicle.license_plate:
                label = f'{label} — {vehicle.license_plate}' if label else vehicle.license_plate
            vehicle.display_name = label or _('New Vehicle')

    def _compute_repair_order_count(self):
        counts = self.env['automotive.repair.order']._read_group(
            [('vehicle_id', 'in', self.ids)], ['vehicle_id'], ['__count'],
        )
        mapped = {vehicle.id: count for vehicle, count in counts}
        for vehicle in self:
            vehicle.repair_order_count = mapped.get(vehicle.id, 0)
