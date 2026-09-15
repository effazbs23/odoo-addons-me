from datetime import timedelta

from odoo import api, fields, models

# Buffer under which an on-time work order is still flagged 'at risk',
# since a razor-thin schedule margin is one late shipment or one machine
# hiccup away from becoming an actual miss.
DUE_DATE_RISK_BUFFER_HOURS = 24


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    has_conflict = fields.Boolean(
        compute='_compute_has_conflict', store=True,
        string='Capacity Conflict',
        help='True when this work order overlaps another work order on the '
             'same workcenter, beyond the workcenter\'s configured capacity.')
    due_risk = fields.Selection([
        ('no_due', 'No Due Date'),
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('high_risk', 'High Risk'),
    ], compute='_compute_due_risk', store=True, string='Due-Date Risk')

    @api.depends('workcenter_id', 'date_planned_start', 'date_planned_finished', 'state')
    def _compute_has_conflict(self):
        for workorder in self:
            workorder.has_conflict = False
        by_workcenter = {}
        for workorder in self:
            if (workorder.workcenter_id and workorder.date_planned_start
                    and workorder.date_planned_finished
                    and workorder.state not in ('done', 'cancel')):
                by_workcenter.setdefault(workorder.workcenter_id.id, []).append(workorder)

        for workcenter_id, workorders in by_workcenter.items():
            others = self.env['mrp.workorder'].search([
                ('workcenter_id', '=', workcenter_id),
                ('state', 'not in', ('done', 'cancel')),
                ('date_planned_start', '!=', False),
                ('date_planned_finished', '!=', False),
            ])
            capacity = self.env['mrp.workcenter'].browse(workcenter_id).capacity or 1
            for workorder in workorders:
                overlapping = others.filtered(
                    lambda o: o.id != workorder.id
                    and o.date_planned_start < workorder.date_planned_finished
                    and o.date_planned_finished > workorder.date_planned_start
                )
                # Concurrently overlapping work orders (including itself)
                # beyond the workcenter's parallel capacity is a conflict.
                workorder.has_conflict = (len(overlapping) + 1) > capacity

    @api.depends('date_planned_finished', 'production_id.date_deadline', 'state')
    def _compute_due_risk(self):
        for workorder in self:
            deadline = workorder.production_id.date_deadline
            finished = workorder.date_planned_finished
            if workorder.state in ('done', 'cancel'):
                workorder.due_risk = 'on_track'
            elif not deadline or not finished:
                workorder.due_risk = 'no_due'
            elif finished > deadline:
                workorder.due_risk = 'high_risk'
            elif finished > deadline - timedelta(hours=DUE_DATE_RISK_BUFFER_HOURS):
                workorder.due_risk = 'at_risk'
            else:
                workorder.due_risk = 'on_track'
