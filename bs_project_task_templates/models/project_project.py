from odoo import models, fields


class ProjectProject(models.Model):
    _inherit = 'project.project'

    stage_template_trigger_project = fields.Boolean(
        string='Fire Templates on Project Stage Change', default=True,
        help="When enabled, stage task templates defined for a Project Stage "
             "auto-create their checklist tasks when this project enters that stage.")
    stage_template_trigger_task = fields.Boolean(
        string='Fire Templates on Task Stage Change', default=True,
        help="When enabled, stage task templates defined for a Task Stage "
             "auto-create their checklist tasks when a task in this project enters that stage.")

    def write(self, vals):
        old_stage_by_id = {project.id: project.stage_id for project in self} if 'stage_id' in vals else {}
        result = super().write(vals)
        if 'stage_id' in vals:
            self.env['project.stage.task.template']._process_stage_change(
                'project',
                self.filtered(lambda p: p.stage_template_trigger_project),
                old_stage_by_id,
                self.env['project.project.stage'].browse(vals.get('stage_id')),
            )
        return result
