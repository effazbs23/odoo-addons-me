from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMrpFiniteCapacityScheduler(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.workcenter = cls.env['mrp.workcenter'].create({
            'name': 'Test Workcenter',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Scheduler Test Product',
            'type': 'consu',
            'is_storable': True,
        })

    def _create_production(self, deadline=False):
        return self.env['mrp.production'].create({
            'product_id': self.product.id,
            'product_uom_id': self.product.uom_id.id,
            'product_qty': 1.0,
            'date_deadline': deadline,
        })

    def _create_workorder(self, production, workcenter, start, finish):
        return self.env['mrp.workorder'].create({
            'name': 'Test WO',
            'production_id': production.id,
            'workcenter_id': workcenter.id,
            'product_uom_id': self.product.uom_id.id,
            'date_start': start,
            'date_finished': finish,
        })

    def test_overlapping_workorders_flagged(self):
        production = self._create_production()
        now = fields.Datetime.now()
        wo1 = self._create_workorder(
            production, self.workcenter, now, now + timedelta(hours=2))
        wo2 = self._create_workorder(
            production, self.workcenter,
            now + timedelta(hours=1), now + timedelta(hours=3))

        self.assertTrue(wo1.has_conflict)
        self.assertTrue(wo2.has_conflict)

    def test_non_overlapping_workorders_not_flagged(self):
        production = self._create_production()
        now = fields.Datetime.now()
        wo1 = self._create_workorder(
            production, self.workcenter, now, now + timedelta(hours=2))
        wo2 = self._create_workorder(
            production, self.workcenter,
            now + timedelta(hours=2), now + timedelta(hours=4))

        self.assertFalse(wo1.has_conflict)
        self.assertFalse(wo2.has_conflict)

    def test_due_risk_high_when_overdue(self):
        now = fields.Datetime.now()
        production = self._create_production(deadline=now + timedelta(hours=1))
        wo = self._create_workorder(
            production, self.workcenter, now, now + timedelta(hours=5))
        self.assertEqual(wo.due_risk, 'high_risk')

    def test_due_risk_on_track_with_margin(self):
        now = fields.Datetime.now()
        production = self._create_production(deadline=now + timedelta(days=10))
        wo = self._create_workorder(
            production, self.workcenter, now, now + timedelta(hours=1))
        self.assertEqual(wo.due_risk, 'on_track')

    def test_due_risk_no_due_date(self):
        production = self._create_production()
        now = fields.Datetime.now()
        wo = self._create_workorder(
            production, self.workcenter, now, now + timedelta(hours=1))
        self.assertEqual(wo.due_risk, 'no_due')

    def test_auto_schedule_avoids_overlap(self):
        production = self._create_production()
        now = fields.Datetime.now()
        existing = self._create_workorder(
            production, self.workcenter, now, now + timedelta(hours=2))

        unscheduled = self.env['mrp.workorder'].create({
            'name': 'Unscheduled WO',
            'production_id': production.id,
            'workcenter_id': self.workcenter.id,
            'product_uom_id': self.product.uom_id.id,
            'duration_expected': 60.0,
        })
        wizard = self.env['mrp.auto.schedule.wizard'].create({
            'work_order_ids': [(6, 0, unscheduled.ids)],
        })
        wizard.action_auto_schedule()

        self.assertTrue(unscheduled.date_start)
        self.assertGreaterEqual(
            unscheduled.date_start, existing.date_finished)
