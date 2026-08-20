from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import RepairShopTestCase


@tagged('post_install', '-at_install')
class TestDeletionRequestApproval(RepairShopTestCase):

    def test_approve_blocked_deletion_raises_clean_error(self):
        # The vehicle has an open repair order referencing it (required,
        # restrict) — approving a deletion request for it must surface a
        # clean UserError, not a raw database IntegrityError, and the
        # request must stay reviewable afterwards rather than being stuck
        # mid-transaction.
        self._create_order()
        request = self.env['automotive.deletion.request'].create({
            'res_model': 'automotive.vehicle',
            'res_id': self.vehicle.id,
            'record_name': self.vehicle.display_name,
            'reason': 'Testing',
        })
        with self.assertRaises(UserError):
            request.with_user(self.manager).action_approve()
        self.assertTrue(self.vehicle.exists())
        self.assertEqual(request.state, 'pending')

    def test_approve_unblocked_deletion_succeeds(self):
        vehicle = self.env['automotive.vehicle'].create({
            'partner_id': self.customer.id, 'manufacturer': 'Honda',
            'model': 'Civic', 'license_plate': 'TEST-002',
        })
        request = self.env['automotive.deletion.request'].create({
            'res_model': 'automotive.vehicle',
            'res_id': vehicle.id,
            'record_name': vehicle.display_name,
            'reason': 'Testing',
        })
        request.with_user(self.manager).action_approve()
        self.assertFalse(vehicle.exists())
        self.assertEqual(request.state, 'approved')

    def test_non_manager_cannot_approve(self):
        vehicle = self.env['automotive.vehicle'].create({
            'partner_id': self.customer.id, 'manufacturer': 'Honda',
            'model': 'Civic', 'license_plate': 'TEST-003',
        })
        request = self.env['automotive.deletion.request'].create({
            'res_model': 'automotive.vehicle',
            'res_id': vehicle.id,
            'record_name': vehicle.display_name,
            'reason': 'Testing',
        })
        with self.assertRaises(UserError):
            request.with_user(self.technician).action_approve()
