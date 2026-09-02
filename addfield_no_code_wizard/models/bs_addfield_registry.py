from odoo import api, fields, models


class BsAddfieldRegistry(models.Model):
    _name = 'bs.addfield.registry'
    _description = 'Custom Fields Added (Add-a-Field Wizard Registry)'
    _order = 'create_date desc'
    _rec_name = 'field_id'

    target_model_id = fields.Many2one(
        'ir.model', string='Model', required=True, ondelete='cascade', readonly=True)
    field_id = fields.Many2one(
        'ir.model.fields', string='Field', required=True, ondelete='cascade', readonly=True)
    view_id = fields.Many2one(
        'ir.ui.view', string='View Inheritance', required=True, ondelete='cascade', readonly=True)
    automation_id = fields.Many2one(
        'base.automation', string='Notification Automation', ondelete='set null', readonly=True)
    created_by_wizard = fields.Boolean(default=True, readonly=True)
    has_data = fields.Boolean(
        string='Has Data', compute='_compute_has_data',
        help="Whether any record on the target model currently has a non-empty value for this field.")

    @api.depends('target_model_id', 'field_id')
    def _compute_has_data(self):
        for record in self:
            if not record.field_id or not record.target_model_id.model:
                record.has_data = False
                continue
            Target = record.env[record.target_model_id.model].sudo()
            record.has_data = bool(
                Target.search_count([(record.field_id.name, '!=', False)], limit=1))

    def action_open_remove_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Remove Field',
            'res_model': 'bs.addfield.remove.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_registry_id': self.id},
        }
