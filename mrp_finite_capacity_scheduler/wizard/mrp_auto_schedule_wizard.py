from datetime import timedelta

from odoo import fields, models


class MrpAutoScheduleWizard(models.TransientModel):
    _name = 'mrp.auto.schedule.wizard'
    _description = 'Auto-schedule Work Orders'

    work_order_ids = fields.Many2many(
        'mrp.workorder', string='Work Orders to Schedule',
        domain=[('state', 'in', ('pending', 'ready', 'waiting')),
                ('workcenter_id', '!=', False)],
        default=lambda self: self._default_work_order_ids())

    def _default_work_order_ids(self):
        return self.env['mrp.workorder'].search([
            ('state', 'in', ('pending', 'ready', 'waiting')),
            ('workcenter_id', '!=', False),
            ('date_planned_start', '=', False),
        ])

    def action_auto_schedule(self):
        """Greedy first-fit heuristic: sort by MO due date, then place each
        work order in the earliest slot on its workcenter that does not
        overlap an already-scheduled work order. This is intentionally a
        simple heuristic, not an optimization solver (see specs.md)."""
        self.ensure_one()
        far_future = fields.Datetime.from_string('9999-12-31 00:00:00')
        workorders = self.work_order_ids.sorted(
            key=lambda wo: (wo.production_id.date_deadline or far_future, wo.id))

        now = fields.Datetime.now()
        next_free_slot = {}
        for workorder in workorders:
            workcenter = workorder.workcenter_id
            if not workcenter:
                continue
            duration = timedelta(minutes=workorder.duration_expected or 60.0)
            start = max(next_free_slot.get(workcenter.id, now), now)
            while True:
                conflict = self._find_next_conflict(workcenter, workorder, start, start + duration)
                if not conflict:
                    break
                start = conflict.date_planned_finished
            finish = start + duration
            workorder.write({
                'date_planned_start': start,
                'date_planned_finished': finish,
            })
            next_free_slot[workcenter.id] = finish
        return {'type': 'ir.actions.act_window_close'}

    def _find_next_conflict(self, workcenter, workorder, start, finish):
        return self.env['mrp.workorder'].search([
            ('workcenter_id', '=', workcenter.id),
            ('id', '!=', workorder.id),
            ('state', 'not in', ('done', 'cancel')),
            ('date_planned_start', '<', finish),
            ('date_planned_finished', '>', start),
        ], order='date_planned_finished', limit=1)
