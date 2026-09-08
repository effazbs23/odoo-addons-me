from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    bs_conflict_config_id = fields.Many2one(
        'bs.calendar.conflict.config', string='Conflict Guard Config',
        compute='_compute_bs_conflict_config_id')
    bs_conflict_active = fields.Boolean(
        related='bs_conflict_config_id.active', readonly=False,
        string='Enable Booking Conflict Guard')
    bs_conflict_check_employees = fields.Boolean(
        related='bs_conflict_config_id.check_employees', readonly=False,
        string='Check Employees')
    bs_conflict_check_resources = fields.Boolean(
        related='bs_conflict_config_id.check_resources', readonly=False,
        string='Check Resources')
    bs_conflict_buffer_minutes = fields.Integer(
        related='bs_conflict_config_id.buffer_minutes', readonly=False,
        string='Buffer (minutes)')

    def _compute_bs_conflict_config_id(self):
        config = self.env['bs.calendar.conflict.config']._get_config()
        for rec in self:
            rec.bs_conflict_config_id = config
