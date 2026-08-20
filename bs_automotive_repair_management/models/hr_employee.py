from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    automotive_labor_ids = fields.One2many(
        'automotive.repair.order.labor', 'technician_id', string='Automotive Labor Lines',
    )
    automotive_total_hours = fields.Float(compute='_compute_automotive_stats')
    automotive_vehicle_count = fields.Integer(compute='_compute_automotive_stats')
    automotive_vehicle_ids = fields.Many2many(
        'automotive.vehicle', compute='_compute_automotive_stats',
        search='_search_automotive_vehicle_ids', string='Vehicles Worked On',
    )
    automotive_open_order_ids = fields.Many2many(
        'automotive.repair.order', compute='_compute_automotive_stats',
        string='Open Work Queue',
    )

    def _compute_automotive_stats(self):
        stats = self.env['automotive.repair.order.labor']._read_group(
            [('technician_id', 'in', self.ids)],
            ['technician_id'],
            ['hours:sum'],
        )
        hours_mapped = {employee.id: hours for employee, hours in stats}

        vehicles_by_employee = {}
        for line in self.env['automotive.repair.order.labor'].search(
            [('technician_id', 'in', self.ids), ('vehicle_id', '!=', False)]
        ):
            vehicles_by_employee.setdefault(line.technician_id.id, set()).add(line.vehicle_id.id)

        open_orders = self.env['automotive.repair.order'].search([
            '|',
                ('lead_technician_id', 'in', self.ids),
                ('labor_ids.technician_id', 'in', self.ids),
            ('state', 'not in', ('closed', 'cancelled')),
        ])

        for employee in self:
            employee.automotive_total_hours = hours_mapped.get(employee.id, 0.0)
            vehicle_ids = vehicles_by_employee.get(employee.id, set())
            employee.automotive_vehicle_count = len(vehicle_ids)
            employee.automotive_vehicle_ids = [(6, 0, list(vehicle_ids))]
            employee.automotive_open_order_ids = open_orders.filtered(
                lambda o, emp=employee: o.lead_technician_id == emp or emp in o.labor_ids.technician_id
            )

    def _search_automotive_vehicle_ids(self, operator, value):
        return [('automotive_labor_ids.vehicle_id', operator, value)]
