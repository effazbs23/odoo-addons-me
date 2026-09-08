from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBsEdgeCases(TransactionCase):
    """Every edge case named in spec section 9, each traceable to one test here."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env['bs.calendar.conflict.config']._get_config()
        # active=False: most of these tests call _bs_find_conflicts()/_bs_suggest_next_slot()
        # directly rather than going through the create()/write() hook (see
        # test_bs_overlap.py for why this is necessary).
        cls.config.write({'check_employees': True, 'check_resources': True, 'buffer_minutes': 0, 'active': False})
        cls.room_a = cls.env['resource.resource'].create({'name': 'BS Edge Room A', 'resource_type': 'material'})
        cls.room_b = cls.env['resource.resource'].create({'name': 'BS Edge Room B', 'resource_type': 'material'})
        cls.internal_user = cls.env['res.users'].create({
            'name': 'BS Edge Test User', 'login': 'bs_edge_test_user', 'email': 'bs_edge_test_user@example.com',
        })

    def _make_event(self, name, start, stop, resources=None, partners=None):
        return self.env['calendar.event'].create({
            'name': name, 'start': start, 'stop': stop,
            'bs_resource_ids': [(6, 0, (resources or self.env['resource.resource']).ids)],
            'partner_ids': [(6, 0, (partners or self.env['res.partner']).ids)],
        })

    def _make_allday_event(self, name, date_str, resources=None):
        # Deliberately NOT passing start/stop: allday's start_date/stop_date are
        # store=True/inverse fields — Odoo's own _inverse_dates() derives start/stop
        # (8:00-18:00 of the date) from them, same as the real calendar UI would.
        return self.env['calendar.event'].create({
            'name': name, 'allday': True, 'start_date': date_str, 'stop_date': date_str,
            'bs_resource_ids': [(6, 0, (resources or self.env['resource.resource']).ids)],
        })

    # EDGE CASE: all-day events block the entire calendar day for the resource, not
    # just Odoo's internal 8:00-18:00 storage window (provisional decision, see
    # context.md / final report — flagged for human sign-off).
    def test_allday_event_blocks_whole_day(self):
        allday_event = self._make_allday_event('Room Reserved All Day', '2026-06-01', resources=self.room_a)
        early_meeting = self._make_event(
            'Early Meeting', '2026-06-01 07:00:00', '2026-06-01 07:30:00', resources=self.room_a)
        late_meeting = self._make_event(
            'Late Meeting', '2026-06-01 20:00:00', '2026-06-01 20:30:00', resources=self.room_a)
        self.assertTrue(early_meeting._bs_find_conflicts(self.config),
                         "7am meeting should conflict with an all-day booking that same day")
        self.assertTrue(late_meeting._bs_find_conflicts(self.config),
                         "8pm meeting should conflict with an all-day booking that same day")
        self.assertEqual(
            early_meeting._bs_find_conflicts(self.config)[0]['conflicting_event'], allday_event)

    def test_allday_event_does_not_leak_into_next_day(self):
        self._make_allday_event('Room Reserved All Day', '2026-06-02', resources=self.room_a)
        next_day_meeting = self._make_event(
            'Next Day Meeting', '2026-06-03 09:00:00', '2026-06-03 10:00:00', resources=self.room_a)
        self.assertFalse(next_day_meeting._bs_find_conflicts(self.config))

    # EDGE CASE: multi-resource events with only one specific conflicting resource —
    # the conflict (and its message) must name that one resource, not "somewhere".
    def test_multi_resource_names_the_specific_conflicting_one(self):
        self._make_event('Existing A', '2026-06-04 10:00:00', '2026-06-04 11:00:00', resources=self.room_a)
        both_rooms = self.room_a | self.room_b
        booking = self._make_event(
            'New Booking', '2026-06-04 10:30:00', '2026-06-04 11:30:00', resources=both_rooms)
        conflicts = booking._bs_find_conflicts(self.config)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['label'], 'BS Edge Room A')

    def test_multi_resource_end_to_end_message_names_specific_resource(self):
        """Same case, but through the real create() hook, checking the actual
        UserError message text a user would see."""
        self.config.write({'active': True})
        self._make_event('Existing A', '2026-06-05 10:00:00', '2026-06-05 11:00:00', resources=self.room_a)
        both_rooms = self.room_a | self.room_b
        with self.assertRaises(UserError) as cm:
            self._make_event('New Booking', '2026-06-05 10:30:00', '2026-06-05 11:30:00', resources=both_rooms)
        self.assertIn('BS Edge Room A', str(cm.exception))
        self.config.write({'active': False})

    # EDGE CASE: a cancelled (archived) event must not count as an active booking.
    def test_cancelled_event_excluded_from_conflicts(self):
        cancelled = self._make_event(
            'Will Be Cancelled', '2026-06-06 10:00:00', '2026-06-06 11:00:00', resources=self.room_a)
        cancelled.write({'active': False})
        new_booking = self._make_event(
            'New Booking', '2026-06-06 10:30:00', '2026-06-06 11:30:00', resources=self.room_a)
        self.assertFalse(new_booking._bs_find_conflicts(self.config))

    # EDGE CASE: a declined attendee is not an active booking for that specific person.
    def test_declined_attendee_excluded_from_conflicts(self):
        partner = self.internal_user.partner_id
        existing = self._make_event(
            'Interview A', '2026-06-07 09:00:00', '2026-06-07 10:00:00', partners=partner)
        existing.attendee_ids.filtered(lambda a: a.partner_id == partner).write({'state': 'declined'})
        new_booking = self._make_event(
            'Interview B', '2026-06-07 09:30:00', '2026-06-07 10:30:00', partners=partner)
        self.assertFalse(new_booking._bs_find_conflicts(self.config))

    def test_declined_attendee_excluded_from_next_slot(self):
        partner = self.internal_user.partner_id
        existing = self._make_event(
            'Interview A', '2026-06-08 09:00:00', '2026-06-08 10:00:00', partners=partner)
        existing.attendee_ids.filtered(lambda a: a.partner_id == partner).write({'state': 'declined'})
        wanted = self._make_event(
            'Interview B', '2026-06-08 09:00:00', '2026-06-08 09:30:00', partners=partner)
        slot = wanted._bs_suggest_next_slot('employee', partner, self.config)
        self.assertEqual(slot.strftime('%Y-%m-%d %H:%M:%S'), '2026-06-08 09:00:00')

    # EDGE CASE: recurring events — each occurrence is checked independently. A
    # conflict on one occurrence must not implicate a different, non-conflicting one.
    def test_recurring_occurrences_checked_independently(self):
        recurrence = self.env['calendar.recurrence'].create({'name': 'Weekly Sync'})
        blocking_event = self._make_event(
            'Blocking Event', '2026-06-09 10:00:00', '2026-06-09 11:00:00', resources=self.room_a)
        occurrence_1 = self._make_event(
            'Weekly Sync', '2026-06-09 10:30:00', '2026-06-09 11:30:00', resources=self.room_a)
        occurrence_1.recurrence_id = recurrence
        occurrence_2 = self._make_event(
            'Weekly Sync', '2026-06-16 10:30:00', '2026-06-16 11:30:00', resources=self.room_a)
        occurrence_2.recurrence_id = recurrence

        conflicts_1 = occurrence_1._bs_find_conflicts(self.config)
        conflicts_2 = occurrence_2._bs_find_conflicts(self.config)
        self.assertTrue(conflicts_1, "First occurrence overlaps the blocking event")
        self.assertEqual(conflicts_1[0]['conflicting_event'], blocking_event)
        self.assertFalse(conflicts_2, "Second occurrence, a week later, has no conflict of its own")
