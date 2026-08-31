from odoo import models, fields, api, _


class ProjectStageTemplateConfirmWizard(models.TransientModel):
    _name = 'project.stage.template.confirm.wizard'
    _description = 'Confirm Pending Stage Template Tasks'

    line_ids = fields.One2many(
        'project.stage.template.confirm.wizard.line', 'wizard_id', string='Proposed Tasks')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        log_ids = self.env.context.get('default_log_ids') or []
        logs = self.env['project.stage.task.template.log'].browse(log_ids).filtered(lambda l: l.state == 'pending')
        res['line_ids'] = [(0, 0, {'log_id': log.id, 'selected': True}) for log in logs]
        return res

    def action_confirm(self):
        self.ensure_one()
        Template = self.env['project.stage.task.template']
        for line in self.line_ids.filtered('selected'):
            log = line.log_id
            record = log.source_record_ref
            if not record.exists():
                log.unlink()
                continue
            project = record if record._name == 'project.project' else record.project_id
            task = self.env['project.task'].create(log.template_id._build_task_vals(record, project))
            log.write({'state': 'created', 'created_task_id': task.id})
            task.message_post(body=_('Auto-generated from stage template "%(name)s" (confirmed).',
                                      name=log.template_id.name))
        # Anything left unselected is dismissed, not left dangling forever.
        self.line_ids.filtered(lambda l: not l.selected).mapped('log_id').unlink()
        return {'type': 'ir.actions.act_window_close'}


class ProjectStageTemplateConfirmWizardLine(models.TransientModel):
    _name = 'project.stage.template.confirm.wizard.line'
    _description = 'Proposed Task Line (Confirm Wizard)'

    wizard_id = fields.Many2one('project.stage.template.confirm.wizard', required=True, ondelete='cascade')
    log_id = fields.Many2one('project.stage.task.template.log', required=True, ondelete='cascade')
    selected = fields.Boolean(default=True)
    task_name = fields.Char(related='log_id.template_id.name', string='Task Title', readonly=True)
    source_record_name = fields.Char(compute='_compute_source_record_name', string='For')
    deadline_offset_days = fields.Integer(related='log_id.template_id.deadline_offset_days', readonly=True)

    @api.depends('log_id.source_record_ref')
    def _compute_source_record_name(self):
        for line in self:
            record = line.log_id.source_record_ref
            line.source_record_name = record.display_name if record else ''
