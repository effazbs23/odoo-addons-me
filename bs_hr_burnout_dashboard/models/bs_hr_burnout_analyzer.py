from odoo import models, fields, api
from datetime import timedelta


class BsHrEmployee(models.Model):
    _inherit = 'hr.employee'

    bs_burnout_index = fields.Float(string='BS Burnout Index (%)', compute='_compute_bs_burnout_index', store=False)
    total_overtime = fields.Float(string='BS Overtime (30d, hours)', compute='_compute_bs_burnout_index', store=False)
    bs_overdue_task_count = fields.Integer(string='BS Overdue Tasks', compute='_compute_bs_burnout_index', store=False)

    def _compute_bs_burnout_index(self):
        thirty_days_ago = fields.Date.today() - timedelta(days=30)
        for employee in self:
            ts_entries = self.env['account.analytic.line'].search([
                ('employee_id', '=', employee.id), ('date', '>=', thirty_days_ago)
            ])
            total_hours = sum(ts_entries.mapped('unit_amount'))

            overtime_factor = max(0, (total_hours - 160) * 2.5)

            overdue_tasks = self.env['project.task'].search_count([
                ('user_ids', 'in', employee.user_id.ids),
                ('date_deadline', '<', fields.Date.today()),
                ('is_closed', '=', False)
            ])
            task_delay_factor = min(40, overdue_tasks * 8)

            employee.total_overtime = round(max(0, total_hours - 160))
            employee.bs_overdue_task_count = overdue_tasks
            employee.bs_burnout_index = round(min(100, overtime_factor + task_delay_factor))
