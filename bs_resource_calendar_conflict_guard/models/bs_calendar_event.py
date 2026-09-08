from datetime import datetime, time, timedelta

from odoo import fields, models


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    # calendar.event has no native link to resource.resource (verified against
    # /addons/calendar in this 19.0 codebase — no reference anywhere in that module).
    # This module owns the linking convention: which meeting rooms/equipment a given
    # event books.
    bs_resource_ids = fields.Many2many(
        'resource.resource', 'bs_calendar_event_resource_rel', 'event_id', 'resource_id',
        string='Booked Resources',
        help='Meeting rooms / equipment booked for this event. Checked for double-booking '
             'by the Conflict Guard when the "Check Resources" setting is enabled.')

    def _bs_get_check_window(self):
        """Return the (start, stop) datetime window used for conflict-checking this event.

        EDGE CASE (spec section 9): all-day events. Odoo core stores an all-day event's
        start/stop as 8:00-18:00 of the date, not midnight-to-midnight (see
        calendar_event._inverse_dates in odoo/addons/calendar) — using those values as-is
        would only block an 8am-6pm window, not "the whole day". We instead treat an
        all-day event as blocking the full calendar day(s), 00:00 of start_date through
        00:00 of the day after stop_date.
        PROVISIONAL DECISION pending explicit human sign-off (flagged as an open question) —
        see context.md. Isolated here so it is a one-line change if the human prefers the
        literal 8:00-18:00 window instead.
        """
        self.ensure_one()
        if self.allday and self.start_date and self.stop_date:
            start = datetime.combine(self.start_date, time.min)
            stop = datetime.combine(self.stop_date, time.min) + timedelta(days=1)
            return start, stop
        return self.start, self.stop

    def _bs_overlaps(self, other, buffer_minutes=0):
        """True if this event's buffered window overlaps ``other``'s window.

        Buffer is applied to THIS event's window only (both before and after), not to
        ``other``'s. This is symmetric in effect across the whole system: every event is
        checked with its own window widened by the buffer, so a required gap of
        `buffer_minutes` between any two bookings is enforced no matter which one is
        being saved.
        """
        self_start, self_stop = self._bs_get_check_window()
        other_start, other_stop = other._bs_get_check_window()
        buf = timedelta(minutes=buffer_minutes or 0)
        return (self_start - buf) < other_stop and (self_stop + buf) > other_start

    def _bs_relevant_partners(self):
        """Attendees (spec 4.1: 'Employees') = event partners tied to an internal
        (non-share) user. hr.employee is intentionally not used — this module depends
        only on calendar/resource, not hr.
        """
        self.ensure_one()
        return self.partner_ids.filtered(lambda p: any(not u.share for u in p.user_ids))

    def _bs_candidate_events(self, domain, buffer_minutes):
        """Coarse DB-level prefilter, then precise overlap decided in Python.

        # ponytail: loose date-range prefilter (whole extra day of slack each side to
        # absorb the all-day 8:00-18:00 storage quirk) rather than a tight SQL overlap
        # filter, since exact overlap depends on _bs_get_check_window() per candidate
        # (all-day vs timed). Fine at v1's expected per-resource event volumes; if a
        # single resource ever accumulates thousands of events, replace with raw SQL.
        """
        self_start, self_stop = self._bs_get_check_window()
        buf = timedelta(minutes=buffer_minutes or 0)
        slack = timedelta(days=1)
        return self.env['calendar.event'].search(domain + [
            ('start', '<', self_stop + buf + slack),
            ('stop', '>', self_start - buf - slack),
        ])

    def _bs_find_conflicts(self, config):
        """Return a list of conflicts for this single event against existing bookings.

        Each item: {'resource_type', 'label', 'resource_ref', 'conflicting_event'}.
        Self-conflict exclusion: candidates always exclude ``self.id`` — this is what
        stops an event from flagging a conflict against its own prior state during a
        write() (the single most likely correctness bug in this module, per the build
        guardrails).
        Cancelled events: ``search()`` domains implicitly exclude inactive (cancelled)
        events since 'active' is a standard field — no extra domain term needed.
        Recurring events: each occurrence is a separate calendar.event row, and this
        method is always called once per row (see _bs_check_conflicts), so each
        occurrence is checked independently, per spec section 9.
        Multi-resource events: resources are checked one at a time in the loops below,
        so the first conflict found names the ONE specific resource responsible, not a
        vague "somewhere in this booking" message.
        """
        self.ensure_one()
        conflicts = []
        buffer_minutes = config.buffer_minutes or 0

        if config.check_employees:
            for partner in self._bs_relevant_partners():
                candidates = self._bs_candidate_events(
                    [('partner_ids', 'in', partner.id), ('id', '!=', self.id)], buffer_minutes)
                for candidate in candidates:
                    # EDGE CASE: a declined attendee is not an active booking for that
                    # person, even though the event itself is still active.
                    attendee = candidate.attendee_ids.filtered(lambda a: a.partner_id == partner)
                    if attendee and attendee[0].state == 'declined':
                        continue
                    if self._bs_overlaps(candidate, buffer_minutes):
                        conflicts.append({
                            'resource_type': 'employee',
                            'label': partner.name,
                            'resource_ref': partner,
                            'conflicting_event': candidate,
                        })
                        break

        if config.check_resources:
            for resource in self.bs_resource_ids:
                candidates = self._bs_candidate_events(
                    [('bs_resource_ids', 'in', resource.id), ('id', '!=', self.id)], buffer_minutes)
                for candidate in candidates:
                    if self._bs_overlaps(candidate, buffer_minutes):
                        conflicts.append({
                            'resource_type': 'resource',
                            'label': resource.name,
                            'resource_ref': resource,
                            'conflicting_event': candidate,
                        })
                        break

        return conflicts

    def _bs_suggest_next_slot(self, resource_type, resource_ref, config, search_days=14):
        """Scan forward from this event's requested start, against ``resource_ref``'s
        existing bookings, for the next open window of at least this event's duration.

        Returns a start datetime, or None if nothing opens up within ``search_days``.
        """
        self.ensure_one()
        self_start, self_stop = self._bs_get_check_window()
        duration = self_stop - self_start
        buf = timedelta(minutes=config.buffer_minutes or 0)
        horizon_end = self_start + timedelta(days=search_days)

        if resource_type == 'employee':
            domain = [('partner_ids', 'in', resource_ref.id)]
        else:
            domain = [('bs_resource_ids', 'in', resource_ref.id)]
        bookings = self.env['calendar.event'].search(
            domain + [('id', '!=', self.id), ('start', '<', horizon_end)], order='start asc')

        busy = []
        for booking in bookings:
            if resource_type == 'employee':
                # EDGE CASE: a declined attendee is not an active booking for that person.
                attendee = booking.attendee_ids.filtered(lambda a: a.partner_id == resource_ref)
                if attendee and attendee[0].state == 'declined':
                    continue
            b_start, b_stop = booking._bs_get_check_window()
            b_start, b_stop = b_start - buf, b_stop + buf
            if b_stop <= self_start:
                continue
            busy.append((b_start, b_stop))
        busy.sort()

        candidate = self_start
        for b_start, b_stop in busy:
            if candidate + duration <= b_start:
                return candidate
            if b_stop > candidate:
                candidate = b_stop
        if candidate <= horizon_end:
            return candidate
        return None
