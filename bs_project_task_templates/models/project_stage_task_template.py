import logging
import re
from datetime import datetime, timedelta

from odoo import models, fields, api, _, Command
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)
PLACEHOLDER_RE = re.compile(r'{{\s*(\w+)\s*}}')


class ProjectStageTaskTemplate(models.Model):
    _name = 'project.stage.task.template'
    _description = 'Project Stage Task Template'
    _order = 'sequence, id'

    name = fields.Char(
        string='Task Title', required=True,
        help="Supports placeholder tokens, e.g. Kickoff call with {{partner_name}}.")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company,
        help="Leave empty to make this template apply across every company. "
             "Set it to scope firing to one company's projects/tasks only.")

    trigger_level = fields.Selection([
        ('project', 'Project Stage'),
        ('task', 'Task Stage'),
    ], required=True, default='task',
        help="Whether this template fires when a PROJECT enters the stage, "
             "or when a TASK enters the stage.")
    # Odoo keeps separate stage models for projects (project.project.stage)
    # and tasks (project.task.type) -- only one of the two is used, matching
    # trigger_level.
    task_stage_id = fields.Many2one('project.task.type', string='Task Stage', index=True)
    project_stage_id = fields.Many2one('project.project.stage', string='Project Stage', index=True)

    description = fields.Text(help="Copied to the created task's description.")

    assignee_rule = fields.Selection([
        ('fixed_user', 'Fixed User'),
        ('project_manager', 'Project Manager'),
        ('same_as_source', "Same as Triggering Record's Assignee(s)"),
        ('unassigned', 'Unassigned'),
    ], required=True, default='unassigned')
    fixed_user_id = fields.Many2one('res.users', string='Fixed Assignee')

    deadline_offset_days = fields.Integer(
        string='Deadline Offset (days)', default=0,
        help="Days after stage entry. 0 = same day.")

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], default='0', required=True)
    tag_ids = fields.Many2many('project.tags', string='Tags')

    refire_policy = fields.Selection([
        ('always', 'Always'),
        ('first_time_only', 'Only First Time'),
        ('confirm', 'Confirm Before Creating'),
    ], required=True, default='first_time_only')

    log_ids = fields.One2many('project.stage.task.template.log', 'template_id', string='Firing Log')

    @api.constrains('trigger_level', 'task_stage_id', 'project_stage_id')
    def _check_stage_matches_trigger_level(self):
        for template in self:
            if template.trigger_level == 'task' and not template.task_stage_id:
                raise ValidationError(_("Pick a Task Stage for a task-level template."))
            if template.trigger_level == 'project' and not template.project_stage_id:
                raise ValidationError(_("Pick a Project Stage for a project-level template."))

    @api.constrains('assignee_rule', 'fixed_user_id')
    def _check_fixed_user_set(self):
        for template in self:
            if template.assignee_rule == 'fixed_user' and not template.fixed_user_id:
                raise ValidationError(_("Pick a Fixed Assignee when the assignee rule is 'Fixed User'."))

    @api.constrains('deadline_offset_days')
    def _check_deadline_offset_not_negative(self):
        for template in self:
            if template.deadline_offset_days < 0:
                raise ValidationError(_("Deadline Offset (days) can't be negative."))

    @api.onchange('trigger_level')
    def _onchange_trigger_level(self):
        self.task_stage_id = False
        self.project_stage_id = False

    # -- Automation entry point, called from project.project / project.task write() overrides --

    @api.model
    def _process_stage_change(self, trigger_level, records, old_stage_by_id, new_stage):
        """`records` just had their stage_id written to `new_stage` (project.project
        or project.task). `old_stage_by_id`: {record.id: previous stage record},
        captured before the write -- used to skip rows that were already in that
        stage (edge case: bulk write over a mixed selection, spec section 9)."""
        if not new_stage:
            return
        changed = records.filtered(lambda r: old_stage_by_id.get(r.id) != new_stage)
        if not changed:
            return
        stage_field = 'task_stage_id' if trigger_level == 'task' else 'project_stage_id'
        templates = self.search([('trigger_level', '=', trigger_level), (stage_field, '=', new_stage.id)])
        if not templates:
            return
        for template in templates:
            template._fire_for_records(changed)

    def _fire_for_records(self, records):
        """Batched: fires this one template across every changed record at
        once (a bulk stage-change edit can be hundreds of records) -- one
        create() call for the resulting tasks and one for their log rows,
        instead of one create() per record.

        Runs the log/task creation sudo(): whoever triggered the stage
        write (a plain project.group_project_user dragging a kanban card,
        typically) is never meant to have direct create rights on the log
        table (it's system-only, never hand-created by a user), so this is
        automation running as the system, not user data entry -- the
        record/project itself the user already had access to."""
        self.ensure_one()
        Log = self.env['project.stage.task.template.log'].sudo()

        pairs = []
        for record in records:
            project = record if record._name == 'project.project' else record.project_id
            if project:
                pairs.append((record, project))
        if not pairs:
            return

        if self.refire_policy == 'first_time_only':
            refs = ['%s,%s' % (record._name, record.id) for record, _project in pairs]
            already_fired = {
                '%s,%s' % (log.source_record_ref._name, log.source_record_ref.id)
                for log in Log.search([('template_id', '=', self.id), ('source_record_ref', 'in', refs)])
                if log.source_record_ref
            }
            pairs = [pair for pair in pairs if ('%s,%s' % (pair[0]._name, pair[0].id)) not in already_fired]
            if not pairs:
                return

        if self.refire_policy == 'confirm':
            Log.create([{
                'template_id': self.id,
                'source_record_ref': '%s,%s' % (record._name, record.id),
                'state': 'pending',
                'company_id': project.company_id.id,
            } for record, project in pairs])
            for record, _project in pairs:
                record.message_post(body=_(
                    "Template task \"%(name)s\" is pending confirmation (stage template set to "
                    "'Confirm Before Creating'). Review it under Project ▸ Tasks ▸ "
                    "Pending Template Confirmations.", name=self.name))
            return

        tasks = self.env['project.task'].sudo().create(
            [self._build_task_vals(record, project) for record, project in pairs])
        Log.create([{
            'template_id': self.id,
            'source_record_ref': '%s,%s' % (record._name, record.id),
            'created_task_id': task.id,
            'state': 'created',
            'company_id': project.company_id.id,
        } for (record, project), task in zip(pairs, tasks)])
        for task in tasks:
            task.message_post(body=_('Auto-generated from stage template "%(name)s".', name=self.name))

    def _build_task_vals(self, record, project):
        self.ensure_one()
        return {
            'name': self._render_placeholders(self.name, record),
            'description': self._render_placeholders(self.description, record) if self.description else False,
            'project_id': project.id,
            'user_ids': [Command.set(self._resolve_assignee(record).ids)],
            'date_deadline': self._compute_deadline(),
            'priority': self.priority,
            'tag_ids': [Command.set(self.tag_ids.ids)],
            'generated_from_template_id': self.id,
        }

    def _resolve_assignee(self, record):
        """Edge case (spec section 9): any resolution failure, or a rule with
        no natural answer for this record type, falls back to unassigned --
        a template glitch must never block the underlying stage write."""
        self.ensure_one()
        try:
            return self._resolve_assignee_raw(record)
        except Exception:
            _logger.warning("Assignee resolution failed for template %s on %s,%s, using unassigned.",
                             self.id, record._name, record.id, exc_info=True)
        return self.env['res.users']

    def _resolve_assignee_raw(self, record):
        self.ensure_one()
        if self.assignee_rule == 'fixed_user':
            return self.fixed_user_id
        if self.assignee_rule == 'project_manager':
            project = record if record._name == 'project.project' else record.project_id
            return project.user_id
        if self.assignee_rule == 'same_as_source' and record._name == 'project.task':
            return record.user_ids
        return self.env['res.users']

    def _compute_deadline(self):
        self.ensure_one()
        deadline_date = fields.Date.context_today(self) + timedelta(days=self.deadline_offset_days)
        return datetime.combine(deadline_date, datetime.min.time())

    def _render_placeholders(self, text, record):
        """Edge case (spec section 9): an unknown placeholder token renders as
        empty string with a logged warning, never a crash."""
        self.ensure_one()
        if not text:
            return text
        project = record if record._name == 'project.project' else record.project_id
        values = {
            'partner_name': project.partner_id.name if project and project.partner_id else '',
            'project_name': project.name if project else '',
            'record_name': record.display_name or '',
            'stage_name': (record.stage_id.name if 'stage_id' in record._fields and record.stage_id else ''),
        }

        def replace(match):
            token = match.group(1)
            if token not in values:
                _logger.warning("Unknown placeholder {{%s}} in template %s, rendering empty.", token, self.id)
                return ''
            return values[token]

        return PLACEHOLDER_RE.sub(replace, text)
