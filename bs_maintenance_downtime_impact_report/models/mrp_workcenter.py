from odoo import fields, models


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    # Community Edition has no maintenance<->mrp bridge at all (that link
    # only ships in the Enterprise `mrp_maintenance` module) - specs.md's
    # design note 1 assumed it already exists. Adding this one field here
    # keeps the whole module Community-compatible instead of pulling in an
    # Enterprise dependency for a single link field. See CHANGELOG.md.
    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center')


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    equipment_ids = fields.One2many('maintenance.equipment', 'workcenter_id', string='Equipment')
