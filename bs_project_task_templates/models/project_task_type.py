from odoo import models, fields


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    stage_task_template_count = fields.Integer(compute='_compute_stage_task_template_count')

    def _compute_stage_task_template_count(self):
        count_by_stage = dict(self.env['project.stage.task.template']._read_group(
            [('task_stage_id', 'in', self.ids)], ['task_stage_id'], ['__count']))
        for stage in self:
            stage.stage_task_template_count = count_by_stage.get(stage, 0)

    def action_view_stage_task_templates(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Task Templates',
            'res_model': 'project.stage.task.template',
            'view_mode': 'list,form',
            'domain': [('trigger_level', '=', 'task'), ('task_stage_id', '=', self.id)],
            'context': {'default_trigger_level': 'task', 'default_task_stage_id': self.id},
        }
