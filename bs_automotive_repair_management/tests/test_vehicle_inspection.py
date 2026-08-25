from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import RepairShopTestCase


@tagged('post_install', '-at_install')
class TestInspectionAccess(RepairShopTestCase):
    """Regression tests for the perm_write=0 ACL that used to block
    Technicians from ever writing to an inspection — even the media_ids/
    item_ids carve-out the model's own write() override explicitly grants
    once locked. recorded_by (and therefore the lock, per _is_locked()) is
    set at create() time, so every inspection is locked immediately; media
    and items are the fields that actually matter post-creation."""

    def test_technician_can_add_media_after_creation(self):
        order = self._create_order()
        inspection = self.env['automotive.vehicle.inspection'].with_user(self.technician).create({
            'repair_order_id': order.id, 'inspection_type': 'checkin',
        })
        attachment = self.env['ir.attachment'].create({
            'name': 'photo.jpg', 'datas': b'', 'res_model': 'automotive.vehicle.inspection',
            'res_id': inspection.id,
        })
        inspection.with_user(self.technician).write({'media_ids': [(4, attachment.id)]})
        self.assertIn(attachment, inspection.media_ids)

    def test_technician_can_add_items_after_creation(self):
        order = self._create_order()
        inspection = self.env['automotive.vehicle.inspection'].with_user(self.technician).create({
            'repair_order_id': order.id, 'inspection_type': 'checkin',
        })
        inspection.with_user(self.technician).write({
            'item_ids': [(0, 0, {'description': 'Keys', 'quantity': 1})],
        })
        self.assertEqual(len(inspection.item_ids), 1)

    def test_technician_cannot_edit_other_fields_once_recorded(self):
        order = self._create_order()
        inspection = self.env['automotive.vehicle.inspection'].with_user(self.technician).create({
            'repair_order_id': order.id, 'inspection_type': 'checkin',
        })
        self.assertTrue(inspection.recorded_by)
        with self.assertRaises(AccessError):
            inspection.with_user(self.technician).write({'signature_full_name': 'Someone Else'})

    def test_manager_can_edit_any_field_after_lock(self):
        order = self._create_order()
        inspection = self.env['automotive.vehicle.inspection'].with_user(self.technician).create({
            'repair_order_id': order.id, 'inspection_type': 'checkin',
        })
        inspection.with_user(self.manager).write({'signature_full_name': 'Manager Override'})
        self.assertEqual(inspection.signature_full_name, 'Manager Override')
