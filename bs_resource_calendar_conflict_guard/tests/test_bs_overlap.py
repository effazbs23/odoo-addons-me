from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBsOverlap(TransactionCase):
    """Core overlap-query tests. The self-conflict-exclusion test is the mandatory,
    highest-priority one per the build guardrails — it must pass before anything else
    is built on top of this query.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env['bs.calendar.conflict.config']._get_config()
        # active=False: these tests call _bs_find_conflicts() directly to test the query
        # itself, deliberately creating overlapping fixtures — active=False keeps the
        # create()/write() hook from blocking that fixture setup. (_bs_find_conflicts()
        # does not consult config.active, only check_employees/check_resources/buffer.)
        cls.config.write({'check_employees': True, 'check_resources': True, 'buffer_minutes': 0, 'active': False})

        cls.internal_user = cls.env['res.users'].create({
            'name': 'BS Conflict Test User',
            'login': 'bs_conflict_test_user',
            'email': 'bs_conflict_test_user@example.com',
        })
        cls.room = cls.env['resource.resource'].create({
            'name': 'BS Test Room',
            'resource_type': 'material',
        })

    def _make_event(self, name, start, stop, partners=None, resources=None):
        return self.env['calendar.event'].create({
            'name': name,
            'start': start,
            'stop': stop,
            'partner_ids': [(6, 0, (partners or self.env['res.partner']).ids)],
            'bs_resource_ids': [(6, 0, (resources or self.env['resource.resource']).ids)],
        })

    def test_self_exclusion_on_write(self):
        """The single most likely correctness bug: an event must never conflict with
        its own prior state when edited. A naive query (without excluding self.id)
        would always find "a conflict" here since the event trivially overlaps itself.
        """
        event = self._make_event(
            'Solo Meeting', '2026-01-05 10:00:00', '2026-01-05 11:00:00',
            resources=self.room)
        event.write({'name': 'Solo Meeting (renamed)'})
        conflicts = event._bs_find_conflicts(self.config)
        self.assertFalse(conflicts, "Event must not conflict with its own prior state on write()")

    def test_resource_overlap_detected(self):
        first = self._make_event(
            'Room Booking A', '2026-01-06 10:00:00', '2026-01-06 11:00:00', resources=self.room)
        second = self._make_event(
            'Room Booking B', '2026-01-06 10:30:00', '2026-01-06 11:30:00', resources=self.room)
        conflicts = second._bs_find_conflicts(self.config)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['resource_type'], 'resource')
        self.assertEqual(conflicts[0]['conflicting_event'], first)

    def test_resource_adjacent_no_buffer_no_conflict(self):
        """Back-to-back bookings (stop == next start) with buffer=0 must NOT conflict."""
        self._make_event('Room Booking A', '2026-01-07 10:00:00', '2026-01-07 11:00:00', resources=self.room)
        second = self._make_event('Room Booking B', '2026-01-07 11:00:00', '2026-01-07 12:00:00', resources=self.room)
        conflicts = second._bs_find_conflicts(self.config)
        self.assertFalse(conflicts)

    def test_employee_overlap_detected(self):
        partner = self.internal_user.partner_id
        first = self._make_event(
            'Interview A', '2026-01-08 09:00:00', '2026-01-08 10:00:00', partners=partner)
        second = self._make_event(
            'Interview B', '2026-01-08 09:30:00', '2026-01-08 10:30:00', partners=partner)
        conflicts = second._bs_find_conflicts(self.config)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['resource_type'], 'employee')
        self.assertEqual(conflicts[0]['conflicting_event'], first)

    def test_non_overlapping_events_no_conflict(self):
        self._make_event('Room Booking A', '2026-01-09 09:00:00', '2026-01-09 10:00:00', resources=self.room)
        second = self._make_event('Room Booking B', '2026-01-09 14:00:00', '2026-01-09 15:00:00', resources=self.room)
        conflicts = second._bs_find_conflicts(self.config)
        self.assertFalse(conflicts)
