from odoo import fields, models


class AutomotiveWorkshopResource(models.Model):
    _name = 'automotive.workshop.resource'
    _description = 'Workshop Bay/Lift Capacity'
    _order = 'name'

    name = fields.Char(required=True, help='e.g. "Bay 1", "Lift 2"')
    resource_calendar_id = fields.Many2one(
        'resource.calendar', string='Working Hours', required=True,
        default=lambda self: self.env.company.resource_calendar_id,
        help='Opening hours and days off for this bay/lift, reused from '
             "Odoo's core resource.calendar.",
    )
    concurrent_capacity = fields.Integer(
        string='Concurrent Capacity', default=1,
        help='How many jobs this resource can run at the same time '
             '(usually 1 per physical bay).',
    )
    active = fields.Boolean(default=True)
