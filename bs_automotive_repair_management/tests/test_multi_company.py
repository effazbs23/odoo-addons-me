from odoo.tests import tagged

from .common import RepairShopTestCase


@tagged('post_install', '-at_install')
class TestVehicleMultiCompany(RepairShopTestCase):
    """Regression tests for the missing company_id/record rule on
    automotive.vehicle — previously every vehicle was visible to every
    company in the database regardless of ownership."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_b = cls.env['res.company'].create({'name': 'Company B Repairs'})
        cls.user_b = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'User B',
            'login': 'test_user_b',
            'email': 'userb@example.com',
            'group_ids': [(6, 0, [cls.group_salesperson.id])],
            'company_ids': [(6, 0, [cls.company_b.id])],
            'company_id': cls.company_b.id,
        })
        cls.vehicle.company_id = cls.env.company

    def test_company_scoped_vehicle_not_visible_to_other_company_user(self):
        found = self.env['automotive.vehicle'].with_user(self.user_b).search(
            [('id', '=', self.vehicle.id)]
        )
        self.assertFalse(found)

    def test_unscoped_vehicle_visible_everywhere(self):
        self.vehicle.company_id = False
        found = self.env['automotive.vehicle'].with_user(self.user_b).search(
            [('id', '=', self.vehicle.id)]
        )
        self.assertTrue(found)


@tagged('post_install', '-at_install')
class TestRepairPickingTypeMultiCompany(RepairShopTestCase):
    """Regression test for the parts-consumption picking type being
    hardcoded to base.main_company — every other company needs its own,
    matched to its own warehouse, or stock.picking creation breaks."""

    def test_picking_type_created_for_new_company(self):
        company_b = self.env['res.company'].create({'name': 'Company B Repairs'})
        self.env['stock.warehouse'].create({
            'name': 'Company B Warehouse', 'code': 'WHB', 'company_id': company_b.id,
        })
        picking_type = self.env['automotive.repair.order.part']._get_repair_picking_type(company_b)
        self.assertEqual(picking_type.company_id, company_b)
        self.assertEqual(picking_type.sequence_code, 'RPARTS')

        # Calling it again must reuse the same picking type, not create a
        # second one.
        picking_type_again = self.env['automotive.repair.order.part']._get_repair_picking_type(company_b)
        self.assertEqual(picking_type, picking_type_again)
