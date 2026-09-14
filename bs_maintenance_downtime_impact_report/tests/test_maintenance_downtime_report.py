from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMaintenanceDowntimeReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report_model = cls.env['maintenance.downtime.impact.report']
        cls.workcenter = cls.env['mrp.workcenter'].create({'name': 'WC Downtime Test', 'costs_hour': 50.0})
        cls.equipment = cls.env['maintenance.equipment'].create({
            'name': 'Press 1', 'workcenter_id': cls.workcenter.id,
        })
        cls.product = cls.env['product.product'].create({'name': 'Downtime Test Product', 'type': 'consu', 'is_storable': True})

    def _create_production(self, deadline, finished=None, state='confirmed'):
        production = self.env['mrp.production'].create({
            'product_id': self.product.id,
            'product_qty': 1,
            'product_uom_id': self.product.uom_id.id,
            'date_deadline': deadline,
        })
        production.date_start = deadline - timedelta(hours=2)
        if finished:
            production.date_finished = finished
        production.state = state
        return production

    def _create_workorder(self, production, start, finish=None):
        return self.env['mrp.workorder'].create({
            'name': 'Op 1', 'production_id': production.id, 'workcenter_id': self.workcenter.id,
            'date_start': start, 'date_finished': finish,
        })

    def _create_request(self, start, end):
        return self.env['maintenance.request'].create({
            'name': 'Downtime Test Request', 'equipment_id': self.equipment.id,
            'schedule_date': start, 'schedule_end': end,
        })

    def test_missed_due_date_flagged_when_finished_after_deadline(self):
        now = datetime(2026, 1, 10, 8, 0, 0)
        deadline = now
        production = self._create_production(deadline, finished=now + timedelta(hours=4))
        self._create_workorder(production, now - timedelta(hours=1), now + timedelta(hours=4))
        self._create_request(now, now + timedelta(hours=2))

        row = self.report_model.search([('production_id', '=', production.id)])
        self.assertTrue(row)
        self.assertTrue(row.missed_due_date)
        self.assertEqual(row.estimated_cost, 100.0)

    def test_on_time_production_not_flagged(self):
        now = datetime(2026, 1, 11, 8, 0, 0)
        deadline = now + timedelta(hours=6)
        production = self._create_production(deadline, finished=now + timedelta(hours=1))
        self._create_workorder(production, now - timedelta(hours=1), now + timedelta(hours=1))
        self._create_request(now, now + timedelta(hours=2))

        row = self.report_model.search([('production_id', '=', production.id)])
        self.assertTrue(row)
        self.assertFalse(row.missed_due_date)

    def test_get_summary_aggregates_across_rows(self):
        now = datetime(2026, 1, 12, 8, 0, 0)
        production = self._create_production(now, finished=now + timedelta(hours=3))
        self._create_workorder(production, now - timedelta(hours=1), now + timedelta(hours=3))
        self._create_request(now, now + timedelta(hours=2))

        summary = self.report_model.get_summary([('production_id', '=', production.id)])
        self.assertEqual(summary['affected_mo_count'], 1)
        self.assertEqual(summary['missed_due_date_count'], 1)
        self.assertEqual(summary['estimated_cost'], 100.0)

    def test_get_top_equipment_ranks_by_hours(self):
        now = datetime(2026, 1, 13, 8, 0, 0)
        production = self._create_production(now, finished=now + timedelta(hours=3))
        self._create_workorder(production, now - timedelta(hours=1), now + timedelta(hours=3))
        self._create_request(now, now + timedelta(hours=2))

        rows = self.report_model.get_top_equipment([('production_id', '=', production.id)])
        self.assertEqual(rows[0]['equipment'], self.equipment.display_name)
        self.assertEqual(rows[0]['hours'], 2.0)
