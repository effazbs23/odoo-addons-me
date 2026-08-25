from odoo import fields, models


class AutomotiveVehicleInspectionItem(models.Model):
    _name = 'automotive.vehicle.inspection.item'
    _description = 'Vehicle Inspection Belonging/Condition Item'

    inspection_id = fields.Many2one(
        'automotive.vehicle.inspection', required=True, ondelete='cascade', index=True,
    )
    description = fields.Char(
        required=True,
        help='e.g. "keys", "sunroof — pre-existing crack, noted at intake".',
    )
    quantity = fields.Integer(default=1)
    returned = fields.Boolean(
        string='Returned to Customer',
        help='Ticked at check-out to confirm this belonging was actually '
             'handed back — meaningless at check-in, where it is always '
             'left unset.',
    )
