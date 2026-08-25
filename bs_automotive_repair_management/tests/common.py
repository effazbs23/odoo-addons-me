from odoo.tests.common import TransactionCase


class RepairShopTestCase(TransactionCase):
    """Shared fixtures for the repair-shop test suite: one user per role
    group and a minimal vehicle/product to build orders against."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group_technician = cls.env.ref('bs_automotive_repair_management.group_shop_technician')
        cls.group_salesperson = cls.env.ref('bs_automotive_repair_management.group_shop_salesperson')
        cls.group_manager = cls.env.ref('bs_automotive_repair_management.group_shop_manager')

        Users = cls.env['res.users'].with_context(no_reset_password=True, mail_create_nosubscribe=True)
        cls.technician = Users.create({
            'name': 'Test Technician',
            'login': 'test_technician',
            'email': 'technician@example.com',
            'group_ids': [(6, 0, [cls.group_technician.id])],
        })
        cls.salesperson = Users.create({
            'name': 'Test Salesperson',
            'login': 'test_salesperson',
            'email': 'salesperson@example.com',
            'group_ids': [(6, 0, [cls.group_salesperson.id])],
        })
        cls.manager = Users.create({
            'name': 'Test Manager',
            'login': 'test_manager',
            'email': 'manager@example.com',
            'group_ids': [(6, 0, [cls.group_manager.id])],
        })
        # linked so tests can assign an order to the Technician and have the
        # repair_order_technician_rule ('own jobs only') actually grant them
        # write access to it, matching real usage.
        cls.technician_employee = cls.env['hr.employee'].create({
            'name': 'Test Technician',
            'user_id': cls.technician.id,
        })

        cls.customer = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'phone': '+1 555 010 0100',
            'email': 'customer@example.com',
            'street': '1 Test Street',
            'city': 'Testville',
        })
        cls.vehicle = cls.env['automotive.vehicle'].create({
            'partner_id': cls.customer.id,
            'manufacturer': 'Toyota',
            'model': 'Corolla',
            'license_plate': 'TEST-001',
        })
        cls.part_product = cls.env['product.product'].create({
            'name': 'Test Part',
            'type': 'consu',
            'is_storable': True,
        })

    def _create_order(self, order_type='standard', **vals):
        vals.setdefault('vehicle_id', self.vehicle.id)
        vals.setdefault('order_type', order_type)
        return self.env['automotive.repair.order'].create(vals)
