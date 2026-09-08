from odoo.exceptions import AccessError, RedirectWarning, UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBsOverrideFlow(TransactionCase):
    """Override ("Book Anyway") flow: never a silent bypass — must redirect to the
    wizard, and only ever log/apply once the wizard's button is explicitly clicked.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env['bs.calendar.conflict.config']._get_config()
        cls.config.write({'check_employees': False, 'check_resources': True, 'buffer_minutes': 0, 'active': True})
        cls.room = cls.env['resource.resource'].create({'name': 'BS Override Room', 'resource_type': 'material'})
        override_group = cls.env.ref('bs_resource_calendar_conflict_guard.group_conflict_override')
        cls.override_user = cls.env['res.users'].create({
            'name': 'BS Override User', 'login': 'bs_override_user', 'email': 'bs_override_user@example.com',
            'group_ids': [(4, override_group.id)],
        })

    def _make_event(self, env, name, start, stop):
        return env['calendar.event'].create({
            'name': name, 'start': start, 'stop': stop,
            'bs_resource_ids': [(6, 0, self.room.ids)],
        })

    def test_override_user_gets_redirect_not_hard_block(self):
        self._make_event(self.env, 'Existing', '2026-05-01 10:00:00', '2026-05-01 11:00:00')
        override_env = self.env(user=self.override_user)
        with self.assertRaises(RedirectWarning):
            self._make_event(override_env, 'New', '2026-05-01 10:30:00', '2026-05-01 11:30:00')

    def test_book_anyway_creates_event_and_logs_overridden(self):
        self._make_event(self.env, 'Existing', '2026-05-02 10:00:00', '2026-05-02 11:00:00')
        override_env = self.env(user=self.override_user)
        try:
            self._make_event(override_env, 'New', '2026-05-02 10:30:00', '2026-05-02 11:30:00')
            self.fail('Expected a RedirectWarning')
        except RedirectWarning as e:
            action_id, _button_text, extra_context = e.args[1], e.args[2], e.args[3]

        wizard = override_env['bs.conflict.override.wizard'].with_context(**extra_context).create({})
        self.assertEqual(wizard.mode, 'create')

        event_count_before = self.env['calendar.event'].search_count(
            [('name', '=', 'New'), ('start', '=', '2026-05-02 10:30:00')])
        wizard.action_book_anyway()
        event_count_after = self.env['calendar.event'].search_count(
            [('name', '=', 'New'), ('start', '=', '2026-05-02 10:30:00')])
        self.assertEqual(event_count_after, event_count_before + 1)

        last_log = self.env['bs.calendar.conflict.log'].sudo().search([], order='id desc', limit=1)
        self.assertEqual(last_log.action_taken, 'overridden')
        self.assertEqual(last_log.overridden_by, self.override_user)

    def test_book_anyway_on_write_applies_to_all_targeted_events(self):
        self._make_event(self.env, 'Existing', '2026-05-03 10:00:00', '2026-05-03 11:00:00')
        movable = self._make_event(self.env, 'Movable', '2026-05-03 15:00:00', '2026-05-03 16:00:00')
        override_env = self.env(user=self.override_user)
        movable_as_override_user = override_env['calendar.event'].browse(movable.id)
        try:
            movable_as_override_user.write({'start': '2026-05-03 10:30:00', 'stop': '2026-05-03 11:30:00'})
            self.fail('Expected a RedirectWarning')
        except RedirectWarning as e:
            extra_context = e.args[3]

        wizard = override_env['bs.conflict.override.wizard'].with_context(**extra_context).create({})
        self.assertEqual(wizard.mode, 'write')
        self.assertIn(movable.id, wizard.event_ids.ids)
        wizard.action_book_anyway()
        self.assertEqual(movable.start.strftime('%Y-%m-%d %H:%M:%S'), '2026-05-03 10:30:00')

    def test_non_override_user_cannot_confirm_wizard_directly(self):
        """Defense in depth: even if a wizard record exists, action_book_anyway itself
        re-checks the override group rather than trusting that the record was reached
        legitimately."""
        wizard = self.env['bs.conflict.override.wizard'].sudo().create({
            'mode': 'create', 'vals_json': '{}', 'conflict_summary': 'test',
        })
        plain_user = self.env['res.users'].create({
            'name': 'BS Plain User', 'login': 'bs_plain_user', 'email': 'bs_plain_user@example.com',
        })
        with self.assertRaises(AccessError):
            wizard.with_user(plain_user).action_book_anyway()

    def test_non_override_user_never_silently_bypassed(self):
        """Regression guard: a non-override user must still get the hard UserError
        block, never a wizard redirect."""
        self._make_event(self.env, 'Existing', '2026-05-04 10:00:00', '2026-05-04 11:00:00')
        with self.assertRaises(UserError):
            self._make_event(self.env, 'New', '2026-05-04 10:30:00', '2026-05-04 11:30:00')
