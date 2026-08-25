from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import RepairShopTestCase


@tagged('post_install', '-at_install')
class TestDiscountCap(RepairShopTestCase):

    def test_new_user_defaults_to_uncapped(self):
        # Regression test: max_discount_percent used to default to 0.0,
        # which blocked the very first non-zero discount any new user tried
        # to apply on a fresh install. It now defaults to 100 (effectively
        # uncapped) so onboarding doesn't start broken.
        self.assertEqual(self.salesperson.max_discount_percent, 100.0)

    def test_discount_within_cap_succeeds(self):
        self.salesperson.max_discount_percent = 20.0
        order = self._create_order(salesperson_id=self.salesperson.id)
        self.env['automotive.repair.order.labor'].with_user(self.manager).create({
            'order_id': order.id, 'description': 'Labor', 'hours': 10, 'hourly_rate': 100,
        })
        order.write({'discount_percent': 20.0})
        self.assertAlmostEqual(order.final_price, 800.0)

    def test_discount_over_cap_is_blocked(self):
        self.salesperson.max_discount_percent = 10.0
        order = self._create_order(salesperson_id=self.salesperson.id)
        self.env['automotive.repair.order.labor'].with_user(self.manager).create({
            'order_id': order.id, 'description': 'Labor', 'hours': 10, 'hourly_rate': 100,
        })
        with self.assertRaises(ValidationError):
            order.write({'discount_percent': 50.0})
