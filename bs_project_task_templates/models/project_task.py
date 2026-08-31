from odoo import models, fields


class ProjectTask(models.Model):
    _inherit = 'project.task'

    generated_from_template_id = fields.Many2one(
        'project.stage.task.template', string='Generated From Template',
        readonly=True, copy=False,
        help="Set when this task was auto-created by a stage template. "
             "Used to show the 'Auto-generated' badge.")

    def write(self, vals):
        old_stage_by_id = {task.id: task.stage_id for task in self} if 'stage_id' in vals else {}
        result = super().write(vals)
        if 'stage_id' in vals:
            self.env['project.stage.task.template']._process_stage_change(
                'task',
                self.filtered(lambda t: t.project_id.stage_template_trigger_task),
                old_stage_by_id,
                self.env['project.task.type'].browse(vals.get('stage_id')),
            )
        return result
