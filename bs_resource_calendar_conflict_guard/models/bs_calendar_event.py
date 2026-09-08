import json
from datetime import datetime, time, timedelta

import psycopg2

from odoo import _, api, fields, models
from odoo.exceptions import RedirectWarning, UserError
from odoo.sql_db import db_connect

# Fields whose change can affect whether an event conflicts with another booking.
# write() only re-runs the conflict guard when one of these actually changed, so a
# renamed/re-described event doesn't get needlessly re-checked.
_BS_CONFLICT_TRIGGER_FIELDS = {
    'start', 'stop', 'allday', 'start_date', 'stop_date',
    'partner_ids', 'bs_resource_ids', 'active', 'recurrence_id',
}


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

    def _bs_build_conflict_message(self, conflict, next_slot):
        other = conflict['conflicting_event']
        message = _(
            '%(resource)s is already booked for "%(event)s" from %(start)s to %(stop)s.',
            resource=conflict['label'], event=other.name,
            start=fields.Datetime.to_string(other.start), stop=fields.Datetime.to_string(other.stop),
        )
        if next_slot:
            message += ' ' + _('Next available slot: %s.', fields.Datetime.to_string(next_slot))
        return message

    def _bs_log_conflict(self, conflict, action_taken, event_id=None, durable=False):
        self.ensure_one()
        vals = {
            'event_id': self.id if event_id is None else event_id,
            'conflicting_event_id': conflict['conflicting_event'].id,
            'resource_type': conflict['resource_type'],
            'resource_ref': '%s,%s' % (conflict['resource_ref']._name, conflict['resource_ref'].id),
            'action_taken': action_taken,
            'overridden_by': self.env.user.id if action_taken == 'overridden' else False,
        }
        if not durable:
            return self.env['bs.calendar.conflict.log'].sudo().create(vals)
        # A 'blocked' log is written immediately before raising UserError/RedirectWarning,
        # and that exception rolls back the whole request transaction on the way out —
        # which would silently wipe this very audit entry along with it. Write it on a
        # separate connection/commit so it survives regardless of how the request ends.
        db_name = self.env.cr.dbname
        try:
            with db_connect(db_name).cursor() as new_cr:
                api.Environment(new_cr, self.env.uid, self.env.context)['bs.calendar.conflict.log'].sudo().create(vals)
        except psycopg2.Error:
            # Both events referenced above were created earlier in THIS SAME still-open
            # transaction (e.g. two conflicting events from one create_multi() call) and
            # so aren't visible yet to the separate connection — the FK insert fails.
            # Never let that sink the audit entry itself: retry unlinked from either event.
            fallback_vals = dict(vals, event_id=False, conflicting_event_id=False)
            with db_connect(db_name).cursor() as new_cr:
                api.Environment(new_cr, self.env.uid, self.env.context)['bs.calendar.conflict.log'].sudo().create(fallback_vals)

    @api.model_create_multi
    def create(self, vals_list):
        events = super().create(vals_list)
        if not self.env.context.get('bs_conflict_override'):
            events._bs_check_conflicts_on_save(vals_list=vals_list, mode='create')
        else:
            # Confirmed via the override wizard: log, never block.
            for event in events:
                for conflict in event._bs_find_conflicts(self.env['bs.calendar.conflict.config']._get_config()):
                    event._bs_log_conflict(conflict, 'overridden')
        return events

    def write(self, vals):
        need_check = bool(_BS_CONFLICT_TRIGGER_FIELDS & set(vals))
        res = super().write(vals)
        if need_check:
            if not self.env.context.get('bs_conflict_override'):
                self._bs_check_conflicts_on_save(vals_list=[vals], mode='write')
            else:
                config = self.env['bs.calendar.conflict.config']._get_config()
                for event in self:
                    for conflict in event._bs_find_conflicts(config):
                        event._bs_log_conflict(conflict, 'overridden')
        return res

    def _bs_check_conflicts_on_save(self, vals_list, mode):
        """Block on the first conflict found among ``self``, unless the current user can
        override — in which case redirect to the confirmation wizard instead of a hard
        block. Never silently bypasses: every blocked attempt is logged immediately, and
        an override is only ever logged once the wizard's explicit "Book Anyway" is
        clicked (see the wizard's action_book_anyway).
        """
        config = self.env['bs.calendar.conflict.config']._get_config()
        if not config.active:
            return
        can_override = self.env.user.has_group('bs_resource_calendar_conflict_guard.group_conflict_override')
        for index, event in enumerate(self):
            if not event.active:
                continue
            conflicts = event._bs_find_conflicts(config)
            if not conflicts:
                continue
            conflict = conflicts[0]
            next_slot = event._bs_suggest_next_slot(conflict['resource_type'], conflict['resource_ref'], config)
            message = event._bs_build_conflict_message(conflict, next_slot)
            if can_override:
                if mode == 'create':
                    payload = vals_list[index]
                    event_ids = []
                else:
                    payload = vals_list[0]
                    event_ids = self.ids
                action = self.env.ref('bs_resource_calendar_conflict_guard.action_bs_conflict_override_wizard')
                raise RedirectWarning(message, action.id, _('Review Conflict'), {
                    'default_mode': mode,
                    'default_event_ids': [(6, 0, event_ids)],
                    'default_vals_json': json.dumps(payload, default=str),
                    'default_conflict_summary': message,
                })
            # durable=True: this log must survive the UserError/RedirectWarning raised right
            # after it, which rolls back this whole request including the log write itself
            # unless it's committed on its own connection (see _bs_log_conflict).
            # event_id=False for 'create': the about-to-be-rolled-back new record never
            # persists, so there's nothing valid to link the log to.
            event._bs_log_conflict(conflict, 'blocked',
                                    event_id=False if mode == 'create' else event.id, durable=True)
            raise UserError(message)
