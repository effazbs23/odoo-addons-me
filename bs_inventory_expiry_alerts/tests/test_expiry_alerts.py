from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestExpiryAlerts(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env['product.category'].create({
            'name': 'Dairy Test Category',
            'expiry_alert_days': 7,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Yogurt',
            'is_storable': True,
            'tracking': 'lot',
            'use_expiration_date': True,
            'categ_id': cls.category.id,
        })
        cls.location = cls.env.ref('stock.stock_location_stock')
        cls.lot_near = cls.env['stock.lot'].create({
            'name': 'LOT-NEAR',
            'product_id': cls.product.id,
            'expiration_date': fields.Datetime.now() + timedelta(days=3),
        })
        cls.lot_far = cls.env['stock.lot'].create({
            'name': 'LOT-FAR',
            'product_id': cls.product.id,
            'expiration_date': fields.Datetime.now() + timedelta(days=60),
        })
        cls.env['stock.quant']._update_available_quantity(
            cls.product, cls.location, 10, lot_id=cls.lot_near)
        cls.env['stock.quant']._update_available_quantity(
            cls.product, cls.location, 10, lot_id=cls.lot_far)

    def _quant_for_lot(self, lot):
        return self.env['stock.quant'].search([
            ('lot_id', '=', lot.id), ('location_id', '=', self.location.id)])

    def test_category_threshold_flags_near_expiry_only(self):
        near_quant = self._quant_for_lot(self.lot_near)
        far_quant = self._quant_for_lot(self.lot_far)
        self.assertTrue(near_quant.is_near_expiry)
        self.assertFalse(far_quant.is_near_expiry)
        self.assertEqual(near_quant.suggested_action, 'markdown')

    def test_global_default_used_when_category_unset(self):
        self.category.expiry_alert_days = 0
        self.env['ir.config_parameter'].sudo().set_param(
            'bs_inventory_expiry_alerts.expiry_alert_days_default', '90')
        far_quant = self._quant_for_lot(self.lot_far)
        far_quant.invalidate_recordset(['is_near_expiry', 'suggested_action'])
        self.assertTrue(far_quant.is_near_expiry)
        self.assertEqual(far_quant.suggested_action, 'transfer')

    def test_dashboard_view_includes_near_expiry_lot(self):
        lines = self.env['stock.expiry.dashboard.line'].search([('lot_id', '=', self.lot_near.id)])
        self.assertTrue(lines)
        self.assertEqual(lines[0].expiry_bucket, '0_7')

    def test_cron_creates_single_activity_no_duplicates(self):
        self.assertFalse(self.lot_near.expiry_threshold_activity_created)
        self.env['stock.lot']._cron_create_expiry_threshold_activities()
        self.assertTrue(self.lot_near.expiry_threshold_activity_created)
        activity_count = self.env['mail.activity'].search_count([
            ('res_model', '=', 'stock.lot'), ('res_id', '=', self.lot_near.id)])
        self.assertEqual(activity_count, 1)
        # Second run must not create a duplicate activity for the same lot.
        self.env['stock.lot']._cron_create_expiry_threshold_activities()
        activity_count_after = self.env['mail.activity'].search_count([
            ('res_model', '=', 'stock.lot'), ('res_id', '=', self.lot_near.id)])
        self.assertEqual(activity_count_after, 1)

    def test_writeoff_wizard_creates_flagged_scrap(self):
        near_quant = self._quant_for_lot(self.lot_near)
        wizard = self.env['stock.expiry.writeoff.wizard'].with_context(
            active_model='stock.quant', active_id=near_quant.id).create({})
        self.assertEqual(wizard.product_id, self.product)
        self.assertEqual(wizard.scrap_qty, 10)
        wizard.action_create_writeoff()
        scrap = self.env['stock.scrap'].search([('lot_id', '=', self.lot_near.id)])
        self.assertTrue(scrap.is_expiry_writeoff)
        self.assertEqual(scrap.state, 'done')
        self.assertAlmostEqual(scrap.expiry_writeoff_value, 10 * self.product.standard_price)
