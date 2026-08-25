from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import RepairShopTestCase


@tagged('post_install', '-at_install')
class TestBillingFieldAccessControl(RepairShopTestCase):
    """Regression tests for the RPC-writable billing-field bypass: hourly_rate/
    unit_cost/covered_by_warranty are hidden from Technicians in the view
    (groups=...) but that is a client-side courtesy only — these fields must
    be rejected server-side too, or a Technician-level API session can
    manipulate what the customer is billed directly."""

    def test_technician_cannot_create_labor_line_with_hourly_rate(self):
        order = self._create_order()
        with self.assertRaises(AccessError):
            self.env['automotive.repair.order.labor'].with_user(self.technician).create({
                'order_id': order.id, 'description': 'Diagnose', 'hours': 1.0, 'hourly_rate': 500.0,
            })

    def test_technician_cannot_write_labor_hourly_rate(self):
        order = self._create_order()
        line = self.env['automotive.repair.order.labor'].with_user(self.manager).create({
            'order_id': order.id, 'description': 'Diagnose', 'hours': 1.0, 'hourly_rate': 50.0,
        })
        with self.assertRaises(AccessError):
            line.with_user(self.technician).write({'hourly_rate': 999.0})

    def test_technician_cannot_create_part_line_with_unit_cost(self):
        order = self._create_order()
        with self.assertRaises(AccessError):
            self.env['automotive.repair.order.part'].with_user(self.technician).create({
                'order_id': order.id, 'product_id': self.part_product.id,
                'quantity': 1, 'unit_cost': 1.0,
            })

    def test_technician_cannot_flip_covered_by_warranty_on_standard_order(self):
        order = self._create_order(order_type='standard')
        with self.assertRaises(AccessError):
            self.env['automotive.repair.order.part'].with_user(self.technician).create({
                'order_id': order.id, 'product_id': self.part_product.id,
                'quantity': 1, 'covered_by_warranty': True,
            })

    def test_technician_can_create_warranty_line_on_warranty_order(self):
        # covered_by_warranty=True is the *natural* value here (it matches
        # order_type == 'warranty_claim'), so this must succeed — it is
        # exactly what default_get()/onchange prefill for a Technician
        # recording ordinary warranty work.
        claim_order = self._create_order(
            order_type='warranty_claim', lead_technician_id=self.technician_employee.id,
        )
        line = self.env['automotive.repair.order.part'].with_user(self.technician).create({
            'order_id': claim_order.id, 'product_id': self.part_product.id, 'quantity': 1,
        })
        self.assertTrue(line.covered_by_warranty)

    def test_manager_can_set_hourly_rate_and_unit_cost(self):
        order = self._create_order()
        labor = self.env['automotive.repair.order.labor'].with_user(self.manager).create({
            'order_id': order.id, 'description': 'Diagnose', 'hours': 1.0, 'hourly_rate': 90.0,
        })
        part = self.env['automotive.repair.order.part'].with_user(self.manager).create({
            'order_id': order.id, 'product_id': self.part_product.id, 'quantity': 1, 'unit_cost': 42.0,
        })
        self.assertEqual(labor.hourly_rate, 90.0)
        self.assertEqual(part.unit_cost, 42.0)


@tagged('post_install', '-at_install')
class TestStateTransitionRoles(RepairShopTestCase):
    """Approve/Invoice move real money (locking in a price, creating an
    invoice) — gated to Salesperson+ so a Technician can't unilaterally
    approve or invoice their own order."""

    def test_technician_cannot_approve_order(self):
        order = self._create_order()
        order.action_confirm_estimate()
        with self.assertRaises(UserError):
            order.with_user(self.technician).action_approve()

    def test_salesperson_can_approve_order(self):
        order = self._create_order(salesperson_id=self.salesperson.id)
        order.action_confirm_estimate()
        order.with_user(self.salesperson).action_approve()
        self.assertEqual(order.state, 'approved')


@tagged('post_install', '-at_install')
class TestVehicleHistorySudo(RepairShopTestCase):
    """automotive.vehicle.history has no create access for Technician/
    Salesperson (it's a system-generated log) but action_close() — reachable
    by any role, no group restriction — needs to create one. Regression test
    for the narrow sudo() added to _create_vehicle_history()."""

    def test_salesperson_can_create_vehicle_history(self):
        order = self._create_order(salesperson_id=self.salesperson.id)
        order.with_user(self.salesperson)._create_vehicle_history()
        self.assertTrue(order.history_id)
