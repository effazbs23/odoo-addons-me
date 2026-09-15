from datetime import timedelta

from odoo import api, fields, models


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    capacity_per_day = fields.Float(
        compute='_compute_capacity_per_day', string='Capacity (h/day)',
        help='Average hours/day this workcenter is available for, based on '
             'its working calendar and its concurrent-unit capacity.')
    utilization_pct = fields.Float(
        compute='_compute_utilization_pct', string='Utilization (This Week) %')

    @api.depends('resource_calendar_id', 'resource_calendar_id.attendance_ids')
    def _compute_capacity_per_day(self):
        for workcenter in self:
            calendar = workcenter.resource_calendar_id
            hours_per_day = 0.0
            if calendar:
                attendances = calendar.attendance_ids.filtered(
                    lambda att: not att.date_from and not att.date_to)
                per_day = {}
                for attendance in attendances:
                    per_day.setdefault(attendance.dayofweek, 0.0)
                    per_day[attendance.dayofweek] += (
                        attendance.hour_to - attendance.hour_from)
                if per_day:
                    hours_per_day = sum(per_day.values()) / len(per_day)
            concurrent_capacity = getattr(workcenter, 'capacity', 1.0) or 1.0
            workcenter.capacity_per_day = hours_per_day * concurrent_capacity

    @api.depends()
    def _compute_utilization_pct(self):
        Workorder = self.env['mrp.workorder']
        now = fields.Datetime.now()
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)

        for workcenter in self:
            workorders = Workorder.search([
                ('workcenter_id', '=', workcenter.id),
                ('date_planned_start', '<', week_end),
                ('date_planned_finished', '>', week_start),
                ('state', 'not in', ('cancel',)),
            ])
            scheduled_hours = 0.0
            for wo in workorders:
                start = max(wo.date_planned_start, week_start)
                stop = min(wo.date_planned_finished, week_end)
                if stop > start:
                    scheduled_hours += (stop - start).total_seconds() / 3600.0
            available_hours = workcenter.capacity_per_day * 7
            workcenter.utilization_pct = (
                min(scheduled_hours / available_hours * 100.0, 100.0)
                if available_hours else 0.0)
