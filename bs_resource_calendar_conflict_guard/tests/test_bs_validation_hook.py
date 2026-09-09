from odoo import api
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBsValidationHook(TransactionCase):
    """create()/write() hook tests for non-override users (hard block). The override
    ("Book Anyway") path is covered separately once the wizard exists.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env['bs.calendar.conflict.config']._get_config()
        cls.config.write({'check_employees': False, 'check_resources': True, 'buffer_minutes': 0})
        cls.room = cls.env['resource.resource'].create({'name': 'BS Hook Room', 'resource_type': 'material'})

    def _make_event(self, name, start, stop):
        return self.env['calendar.event'].create({
            'name': name, 'start': start, 'stop': stop,
            'bs_resource_ids': [(6, 0, self.room.ids)],
        })

    def test_create_conflict_is_blocked_with_clear_message(self):
        self._make_event('Client Demo', '2026-04-01 14:00:00', '2026-04-01 15:00:00')
        with self.assertRaises(UserError) as cm:
            self._make_event('Team Sync', '2026-04-01 14:30:00', '2026-04-01 15:30:00')
        message = str(cm.exception)
        self.assertIn('BS Hook Room', message)
        self.assertIn('Client Demo', message)
        self.assertIn('Next available slot', message)

    def _fresh_cursor_blocked_log_count(self):
        """The 'blocked' log is written on its own connection/commit specifically so
        it survives the UserError-triggered rollback of the main request transaction
        (see _bs_log_conflict's durable=True path) — which means it is invisible to
        self.env's own still-open transaction (REPEATABLE READ snapshot) no matter
        what. A genuinely separate cursor/transaction is the only way to observe it,
        exactly like a follow-up HTTP request would in production.
        """
        with self.registry.cursor() as cr2:
            env2 = api.Environment(cr2, self.env.uid, self.env.context)
            return env2['bs.calendar.conflict.log'].sudo().search_count([('action_taken', '=', 'blocked')])

    def test_blocked_attempt_is_logged(self):
        # NOTE: deliberately NOT using self.assertRaises() here. Odoo's BaseCase
        # overrides assertRaises to wrap the block in a savepoint that always rolls
        # back once the expected exception is raised (it exists to assert "this
        # failed operation had no side effects") — that would silently roll back
        # the very log entry we're trying to observe, since it's a side effect of
        # a raise) is intentional and audit history, not a leftover to discard.
        self._make_event('Existing', '2026-04-02 14:00:00', '2026-04-02 15:00:00')
        log_count_before = self._fresh_cursor_blocked_log_count()
        raised = False
        try:
            self._make_event('New', '2026-04-02 14:30:00', '2026-04-02 15:30:00')
        except UserError:
            raised = True
        self.assertTrue(raised, "Expected a UserError to be raised")
        log_count_after = self._fresh_cursor_blocked_log_count()
        self.assertEqual(log_count_after, log_count_before + 1)

    def test_non_conflicting_create_behaves_like_native_odoo(self):
        """Regression: no error, no log entry, when there is no overlap."""
        log_count_before = self.env['bs.calendar.conflict.log'].sudo().search_count([])
        self._make_event('Solo', '2026-04-03 09:00:00', '2026-04-03 10:00:00')
        log_count_after = self.env['bs.calendar.conflict.log'].sudo().search_count([])
        self.assertEqual(log_count_before, log_count_after)

    def test_write_without_relevant_field_change_not_rechecked(self):
        """Renaming an event can never create a real conflict — write() should not
        even bother running the guard when only irrelevant fields changed."""
        self._make_event('Existing', '2026-04-04 14:00:00', '2026-04-04 15:00:00')
        other = self._make_event('Other', '2026-04-04 16:00:00', '2026-04-04 17:00:00')
        # Renaming does not touch start/stop/resources -> must not raise even though
        # a naive "recheck on every write" would be harmless here anyway; this test
        # documents the intentional trigger-field optimization.
        other.write({'name': 'Other (renamed)'})
        self.assertEqual(other.name, 'Other (renamed)')

    def test_write_edit_without_conflict_succeeds(self):
        """End-to-end self-exclusion: editing an event's own time to a still-valid
        window must not raise, going through the real write() hook (not just the
        raw query as in test_bs_overlap)."""
        event = self._make_event('Movable', '2026-04-05 09:00:00', '2026-04-05 10:00:00')
        event.write({'start': '2026-04-05 09:30:00', 'stop': '2026-04-05 10:30:00'})
        self.assertEqual(event.start.strftime('%Y-%m-%d %H:%M:%S'), '2026-04-05 09:30:00')
