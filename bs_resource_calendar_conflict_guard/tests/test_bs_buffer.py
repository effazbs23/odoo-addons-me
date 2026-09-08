from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBsBuffer(TransactionCase):
    """Buffer-time tests (spec section 5 / 10): the second highest-priority place for a
    subtle logic bug per the build guardrails, after self-conflict-exclusion.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env['bs.calendar.conflict.config']._get_config()
        # active=False so fixture creation isn't blocked by the create() hook — these
        # tests call _bs_find_conflicts() directly (see test_bs_overlap.py for why).
        cls.config.write({'check_employees': False, 'check_resources': True, 'buffer_minutes': 15, 'active': False})
        cls.room = cls.env['resource.resource'].create({'name': 'BS Buffer Room', 'resource_type': 'material'})

    def _make_event(self, name, start, stop):
        return self.env['calendar.event'].create({
            'name': name, 'start': start, 'stop': stop,
            'bs_resource_ids': [(6, 0, self.room.ids)],
        })

    def test_gap_smaller_than_buffer_conflicts(self):
        """15-minute buffer, only a 10-minute gap between bookings -> must conflict."""
        self._make_event('A', '2026-02-02 10:00:00', '2026-02-02 11:00:00')
        b = self._make_event('B', '2026-02-02 11:10:00', '2026-02-02 12:00:00')
        conflicts = b._bs_find_conflicts(self.config)
        self.assertEqual(len(conflicts), 1)

    def test_gap_equal_to_buffer_no_conflict(self):
        """A gap of exactly the buffer amount is enough turnaround time -> no conflict."""
        self._make_event('A', '2026-02-03 10:00:00', '2026-02-03 11:00:00')
        b = self._make_event('B', '2026-02-03 11:15:00', '2026-02-03 12:00:00')
        conflicts = b._bs_find_conflicts(self.config)
        self.assertFalse(conflicts)

    def test_gap_larger_than_buffer_no_conflict(self):
        self._make_event('A', '2026-02-04 10:00:00', '2026-02-04 11:00:00')
        b = self._make_event('B', '2026-02-04 12:00:00', '2026-02-04 13:00:00')
        conflicts = b._bs_find_conflicts(self.config)
        self.assertFalse(conflicts)

    def test_buffer_symmetric_regardless_of_check_direction(self):
        """The buffer must apply the same way whichever event is being checked — a
        10-minute gap must be flagged whether we check the earlier or the later event.
        """
        a = self._make_event('A', '2026-02-05 10:00:00', '2026-02-05 11:00:00')
        b = self._make_event('B', '2026-02-05 11:10:00', '2026-02-05 12:00:00')
        self.assertTrue(a._bs_find_conflicts(self.config), "Checking the earlier event must also detect the conflict")
        self.assertTrue(b._bs_find_conflicts(self.config), "Checking the later event must detect the conflict")

    def test_zero_buffer_default_allows_back_to_back(self):
        """Buffer defaults to 0 (exact overlap only) so existing back-to-back schedules
        are not broken on install."""
        self.config.write({'buffer_minutes': 0})
        self._make_event('A', '2026-02-06 10:00:00', '2026-02-06 11:00:00')
        b = self._make_event('B', '2026-02-06 11:00:00', '2026-02-06 12:00:00')
        conflicts = b._bs_find_conflicts(self.config)
        self.assertFalse(conflicts)
