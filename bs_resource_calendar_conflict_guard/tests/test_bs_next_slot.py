from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBsNextSlot(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env['bs.calendar.conflict.config']._get_config()
        # active=False so fixture creation isn't blocked by the create() hook — these
        # tests call _bs_suggest_next_slot() directly (see test_bs_overlap.py for why).
        cls.config.write({'check_employees': False, 'check_resources': True, 'buffer_minutes': 0, 'active': False})
        cls.room = cls.env['resource.resource'].create({'name': 'BS Slot Room', 'resource_type': 'material'})

    def _make_event(self, name, start, stop):
        return self.env['calendar.event'].create({
            'name': name, 'start': start, 'stop': stop,
            'bs_resource_ids': [(6, 0, self.room.ids)],
        })

    def test_next_slot_after_single_booking(self):
        self._make_event('Existing', '2026-03-02 10:00:00', '2026-03-02 11:00:00')
        wanted = self._make_event('Wanted', '2026-03-02 10:30:00', '2026-03-02 11:30:00')
        slot = wanted._bs_suggest_next_slot('resource', self.room, self.config)
        self.assertEqual(slot.strftime('%Y-%m-%d %H:%M:%S'), '2026-03-02 11:00:00')

    def test_next_slot_skips_over_several_bookings(self):
        self._make_event('A', '2026-03-03 09:00:00', '2026-03-03 10:00:00')
        self._make_event('B', '2026-03-03 10:00:00', '2026-03-03 11:00:00')
        self._make_event('C', '2026-03-03 11:00:00', '2026-03-03 12:30:00')
        wanted = self._make_event('Wanted', '2026-03-03 09:15:00', '2026-03-03 10:15:00')
        slot = wanted._bs_suggest_next_slot('resource', self.room, self.config)
        # first gap of >= 1h (the requested duration) is right after C ends at 12:30
        self.assertEqual(slot.strftime('%Y-%m-%d %H:%M:%S'), '2026-03-03 12:30:00')

    def test_next_slot_finds_gap_between_bookings(self):
        self._make_event('A', '2026-03-04 09:00:00', '2026-03-04 10:00:00')
        self._make_event('B', '2026-03-04 12:00:00', '2026-03-04 13:00:00')
        wanted = self._make_event('Wanted', '2026-03-04 09:15:00', '2026-03-04 09:45:00')
        # 30-minute request: the 09:00-10:00 booking blocks it, but 10:00-12:00 gap (2h)
        # is plenty for a 30-minute meeting.
        slot = wanted._bs_suggest_next_slot('resource', self.room, self.config)
        self.assertEqual(slot.strftime('%Y-%m-%d %H:%M:%S'), '2026-03-04 10:00:00')
