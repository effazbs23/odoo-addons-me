from datetime import date
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestStageTaskTemplates(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = cls.env['res.users'].create({
            'name': 'PM Manager',
            'login': 'pm_manager_stage_template',
            'email': 'pm_manager_stage_template@example.com',
            'groups_id': [(6, 0, [cls.env.ref('project.group_project_manager').id])],
        })
        cls.assignee = cls.env['res.users'].create({
            'name': 'Task Assignee',
            'login': 'task_assignee_stage_template',
            'email': 'task_assignee_stage_template@example.com',
            'groups_id': [(6, 0, [cls.env.ref('project.group_project_user').id])],
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Acme Corp'})
        cls.project = cls.env['project.project'].create({
            'name': 'Onboarding Project',
            'user_id': cls.manager.id,
            'partner_id': cls.partner.id,
        })
        cls.task_stage_new = cls.env['project.task.type'].create({
            'name': 'New', 'project_ids': [(4, cls.project.id)],
        })
        cls.task_stage_qa = cls.env['project.task.type'].create({
            'name': 'QA', 'project_ids': [(4, cls.project.id)],
        })
        cls.task_stage_done = cls.env['project.task.type'].create({
            'name': 'Done', 'project_ids': [(4, cls.project.id)],
        })
        cls.project_stage_kickoff = cls.env['project.project.stage'].create({'name': 'Kickoff'})
        cls.source_task = cls.env['project.task'].create({
            'name': 'Source Task',
            'project_id': cls.project.id,
            'stage_id': cls.task_stage_new.id,
            'user_ids': [(6, 0, [cls.assignee.id])],
        })

    def _make_template(self, **vals):
        base = {
            'name': 'Generated Task',
            'trigger_level': 'task',
            'task_stage_id': self.task_stage_qa.id,
            'assignee_rule': 'unassigned',
            'deadline_offset_days': 0,
            'priority': '0',
            'refire_policy': 'always',
        }
        base.update(vals)
        return self.env['project.stage.task.template'].create(base)

    # -- Unit: assignee_rule resolution --

    def test_assignee_rule_fixed_user(self):
        self._make_template(assignee_rule='fixed_user', fixed_user_id=self.assignee.id)
        self.source_task.write({'stage_id': self.task_stage_qa.id})
        created = self.env['project.task'].search([('generated_from_template_id', '!=', False)])
        self.assertEqual(created.user_ids, self.assignee)

    def test_assignee_rule_project_manager(self):
        self._make_template(assignee_rule='project_manager')
        self.source_task.write({'stage_id': self.task_stage_qa.id})
        created = self.env['project.task'].search([('generated_from_template_id', '!=', False)])
        self.assertEqual(created.user_ids, self.manager)

    def test_assignee_rule_same_as_source(self):
        self._make_template(assignee_rule='same_as_source')
        self.source_task.write({'stage_id': self.task_stage_qa.id})
        created = self.env['project.task'].search([('generated_from_template_id', '!=', False)])
        self.assertEqual(created.user_ids, self.assignee)

    def test_assignee_rule_unassigned(self):
        self._make_template(assignee_rule='unassigned')
        self.source_task.write({'stage_id': self.task_stage_qa.id})
        created = self.env['project.task'].search([('generated_from_template_id', '!=', False)])
        self.assertFalse(created.user_ids)

    # -- Unit: deadline offset --

    def test_deadline_offset_zero_is_same_day(self):
        self._make_template(deadline_offset_days=0)
        self.source_task.write({'stage_id': self.task_stage_qa.id})
        created = self.env['project.task'].search([('generated_from_template_id', '!=', False)])
        self.assertEqual(created.date_deadline.date(), date.today())

    def test_deadline_offset_crosses_month_year_boundary(self):
        with patch('odoo.fields.Date.context_today', return_value=date(2026, 12, 30)):
            self._make_template(deadline_offset_days=5)
            self.source_task.write({'stage_id': self.task_stage_qa.id})
        created = self.env['project.task'].search([('generated_from_template_id', '!=', False)])
        self.assertEqual(created.date_deadline.date(), date(2027, 1, 4))

    # -- Unit: refire policy --

    def test_first_time_only_does_not_refire(self):
        self._make_template(refire_policy='first_time_only')
        self.source_task.write({'stage_id': self.task_stage_qa.id})
        self.source_task.write({'stage_id': self.task_stage_done.id})
        self.source_task.write({'stage_id': self.task_stage_qa.id})
        created = self.env['project.task'].search([('generated_from_template_id', '!=', False)])
        self.assertEqual(len(created), 1)

    def test_always_does_refire(self):
        self._make_template(refire_policy='always')
        self.source_task.write({'stage_id': self.task_stage_qa.id})
        self.source_task.write({'stage_id': self.task_stage_done.id})
        self.source_task.write({'stage_id': self.task_stage_qa.id})
        created = self.env['project.task'].search([('generated_from_template_id', '!=', False)])
        self.assertEqual(len(created), 2)

    def test_confirm_policy_queues_instead_of_creating(self):
        template = self._make_template(refire_policy='confirm')
        self.source_task.write({'stage_id': self.task_stage_qa.id})
        created = self.env['project.task'].search([('generated_from_template_id', '!=', False)])
        self.assertFalse(created)
        log = self.env['project.stage.task.template.log'].search([('template_id', '=', template.id)])
        self.assertEqual(len(log), 1)
        self.assertEqual(log.state, 'pending')

        wizard = self.env['project.stage.template.confirm.wizard'].with_context(
            default_log_ids=log.ids).create({})
        wizard.action_confirm()
        created = self.env['project.task'].search([('generated_from_template_id', '!=', False)])
        self.assertEqual(len(created), 1)
        self.assertEqual(log.state, 'created')

    # -- Integration: sequential stages produce cumulative task set --

    def test_sequential_stages_produce_cumulative_tasks(self):
        self._make_template(name='QA task', task_stage_id=self.task_stage_qa.id)
        self._make_template(name='Done task', task_stage_id=self.task_stage_done.id)
        self.source_task.write({'stage_id': self.task_stage_qa.id})
        self.source_task.write({'stage_id': self.task_stage_done.id})
        created = self.env['project.task'].search([('generated_from_template_id', '!=', False)])
        self.assertEqual(set(created.mapped('name')), {'QA task', 'Done task'})

    # -- Integration: bulk stage change on multiple tasks --

    def test_bulk_stage_change_fires_independently_per_record(self):
        self._make_template()
        other_task = self.env['project.task'].create({
            'name': 'Other Task', 'project_id': self.project.id, 'stage_id': self.task_stage_new.id,
        })
        (self.source_task | other_task).write({'stage_id': self.task_stage_qa.id})
        created = self.env['project.task'].search([('generated_from_template_id', '!=', False)])
        self.assertEqual(len(created), 2)

    def test_bulk_stage_change_skips_records_already_in_target_stage(self):
        self._make_template()
        already_in_qa = self.env['project.task'].create({
            'name': 'Already QA', 'project_id': self.project.id, 'stage_id': self.task_stage_qa.id,
        })
        (self.source_task | already_in_qa).write({'stage_id': self.task_stage_qa.id})
        created = self.env['project.task'].search([('generated_from_template_id', '!=', False)])
        self.assertEqual(len(created), 1)
        self.assertEqual(created.name, 'Generated Task')

    # -- Regression: a broken placeholder must not block the underlying write --

    def test_broken_placeholder_does_not_block_stage_write(self):
        self._make_template(name='Hello {{unknown_token}}')
        self.source_task.write({'stage_id': self.task_stage_qa.id})
        self.assertEqual(self.source_task.stage_id, self.task_stage_qa)
        created = self.env['project.task'].search([('generated_from_template_id', '!=', False)])
        self.assertEqual(created.name, 'Hello ')

    def test_assignee_resolution_exception_does_not_block_stage_write(self):
        self._make_template(assignee_rule='same_as_source')
        with patch(
            'odoo.addons.project_stage_task_templates.models.project_stage_task_template'
            '.ProjectStageTaskTemplate._resolve_assignee',
            side_effect=Exception('boom'),
        ):
            self.source_task.write({'stage_id': self.task_stage_qa.id})
        self.assertEqual(self.source_task.stage_id, self.task_stage_qa)

    # -- Placeholder rendering --

    def test_placeholder_renders_known_tokens(self):
        self._make_template(name='Kickoff call with {{partner_name}}')
        self.source_task.write({'stage_id': self.task_stage_qa.id})
        created = self.env['project.task'].search([('generated_from_template_id', '!=', False)])
        self.assertEqual(created.name, 'Kickoff call with Acme Corp')

    # -- Project-level trigger + per-project toggle --

    def test_project_level_trigger_creates_task_under_project(self):
        self._make_template(
            trigger_level='project', task_stage_id=False, project_stage_id=self.project_stage_kickoff.id)
        self.project.write({'stage_id': self.project_stage_kickoff.id})
        created = self.env['project.task'].search([('generated_from_template_id', '!=', False)])
        self.assertEqual(len(created), 1)
        self.assertEqual(created.project_id, self.project)

    def test_project_trigger_toggle_off_suppresses_firing(self):
        self._make_template(
            trigger_level='project', task_stage_id=False, project_stage_id=self.project_stage_kickoff.id)
        self.project.write({'stage_template_trigger_project': False})
        self.project.write({'stage_id': self.project_stage_kickoff.id})
        created = self.env['project.task'].search([('generated_from_template_id', '!=', False)])
        self.assertFalse(created)
