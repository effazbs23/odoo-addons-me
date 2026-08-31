from odoo import models, fields


class ProjectStageTaskTemplateLog(models.Model):
    _name = 'project.stage.task.template.log'
    _description = 'Project Stage Task Template Firing Log'
    _order = 'create_date desc'

    template_id = fields.Many2one(
        'project.stage.task.template', string='Template', required=True,
        ondelete='cascade', index=True)
    source_record_ref = fields.Reference(
        selection=[('project.project', 'Project'), ('project.task', 'Task')],
        string='Trigger Record', required=True)
    created_task_id = fields.Many2one('project.task', string='Created Task', ondelete='set null')
    state = fields.Selection([
        ('pending', 'Pending Confirmation'),
        ('created', 'Created'),
    ], required=True, default='created', index=True,
        help="'Pending Confirmation' rows exist for refire_policy='confirm' "
             "templates until a human confirms or dismisses them via the "
             "Pending Template Confirmations wizard.")

    def action_confirm_selected(self):
        """Open the confirm wizard pre-filled with these pending log rows."""
        pending = self.filtered(lambda log: log.state == 'pending')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirm Template Tasks',
            'res_model': 'project.stage.template.confirm.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_log_ids': pending.ids},
        }
