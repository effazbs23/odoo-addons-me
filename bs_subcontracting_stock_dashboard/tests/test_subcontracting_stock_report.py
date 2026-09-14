from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSubcontractingStockReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report_model = cls.env['subcontracting.stock.report']
        cls.company = cls.env.company
        cls.subcon_root = cls.company.subcontracting_location_id
        assert cls.subcon_root, "mrp_subcontracting should auto-create a company subcontracting location"

        cls.vendor = cls.env['res.partner'].create({'name': 'Acme Subcontractor'})
        cls.vendor_location = cls.env['stock.location'].create({
            'name': 'Acme Subcontractor Location', 'usage': 'internal',
            'location_id': cls.subcon_root.id, 'company_id': cls.company.id,
        })
        cls.vendor.with_company(cls.company).property_stock_subcontractor = cls.vendor_location.id

        cls.product = cls.env['product.product'].create({
            'name': 'Subcon Test Widget', 'type': 'consu', 'is_storable': True, 'standard_price': 10.0,
        })
        cls.other_partner = cls.env['res.partner'].create({'name': 'Vendor Own Materials'})

    def _create_quant(self, quantity, owner=None):
        return self.env['stock.quant'].create({
            'product_id': self.product.id, 'location_id': self.vendor_location.id,
            'quantity': quantity, 'owner_id': owner.id if owner else False,
        })

    def _create_incoming_move_line(self, quantity, days_ago):
        source = self.env.ref('stock.stock_location_suppliers')
        move = self.env['stock.move'].create({
            'product_id': self.product.id, 'product_uom_qty': quantity, 'product_uom': self.product.uom_id.id,
            'location_id': source.id, 'location_dest_id': self.vendor_location.id,
            'date': datetime.now() - timedelta(days=days_ago),
        })
        move.write({'quantity': quantity, 'state': 'done'})
        self.env.cr.execute(
            "UPDATE stock_move_line SET date = %s WHERE move_id = %s",
            (datetime.now() - timedelta(days=days_ago), move.id),
        )
        return move

    def test_company_owned_quant_classified_correctly(self):
        quant = self._create_quant(50)
        row = self.report_model.search([('quant_id', '=', quant.id)])
        self.assertEqual(row.ownership, 'company')
        self.assertEqual(row.partner_id, self.vendor)
        self.assertEqual(row.value, 500.0)

    def test_subcontractor_owned_quant_classified_correctly(self):
        quant = self._create_quant(20, owner=self.other_partner)
        row = self.report_model.search([('quant_id', '=', quant.id)])
        self.assertEqual(row.ownership, 'subcontractor')

    def test_aging_bucket_thresholds(self):
        self.env['ir.config_parameter'].sudo().set_param('bs_subcontracting_stock_dashboard.bucket_1_max', '7')
        self.env['ir.config_parameter'].sudo().set_param('bs_subcontracting_stock_dashboard.bucket_2_max', '14')
        self.env['ir.config_parameter'].sudo().set_param('bs_subcontracting_stock_dashboard.bucket_3_max', '30')

        self._create_incoming_move_line(10, days_ago=3)
        quant = self._create_quant(10)
        row = self.report_model.search([('quant_id', '=', quant.id)])
        self.assertEqual(row.age_days, 3)
        self.assertEqual(row.aging_bucket, 'b1')

    def test_dashboard_summary_and_split(self):
        self._create_quant(30)
        self._create_quant(15, owner=self.other_partner)
        domain = [('location_id', '=', self.vendor_location.id)]
        summary = self.report_model.get_dashboard_summary(domain)
        self.assertEqual(summary['total_quantity'], 45)
        self.assertEqual(summary['company_quantity'], 30)
        self.assertEqual(summary['subcontractor_quantity'], 15)

        split = self.report_model.get_ownership_split(domain)
        self.assertEqual(split['company'], 30)
        self.assertEqual(split['subcontractor'], 15)

    def test_breakdown_by_subcontractor(self):
        self._create_quant(25)
        domain = [('location_id', '=', self.vendor_location.id)]
        rows = self.report_model.get_breakdown_by_subcontractor(domain)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['partner'], self.vendor.display_name)
        self.assertEqual(rows[0]['company_qty'], 25)
        self.assertEqual(rows[0]['company_value'], 250.0)

    def test_value_report_totals(self):
        self._create_quant(25)
        domain = [('location_id', '=', self.vendor_location.id)]
        result = self.report_model.get_value_report(domain)
        self.assertEqual(result['total_at_risk'], 250.0)


@tagged('post_install', '-at_install')
class TestSubcontractingOverdueAlert(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.subcon_root = self.company.subcontracting_location_id
        self.vendor = self.env['res.partner'].create({'name': 'Overdue Vendor'})
        self.vendor_location = self.env['stock.location'].create({
            'name': 'Overdue Vendor Location', 'usage': 'internal',
            'location_id': self.subcon_root.id, 'company_id': self.company.id,
        })
        self.vendor.with_company(self.company).property_stock_subcontractor = self.vendor_location.id
        self.product = self.env['product.product'].create({
            'name': 'Overdue Widget', 'type': 'consu', 'is_storable': True, 'standard_price': 5.0,
        })
        source = self.env.ref('stock.stock_location_suppliers')
        move = self.env['stock.move'].create({
            'product_id': self.product.id, 'product_uom_qty': 5, 'product_uom': self.product.uom_id.id,
            'location_id': source.id, 'location_dest_id': self.vendor_location.id,
        })
        move.write({'quantity': 5, 'state': 'done'})
        self.env.cr.execute(
            "UPDATE stock_move_line SET date = %s WHERE move_id = %s",
            (datetime.now() - timedelta(days=45), move.id),
        )
        self.env['stock.quant'].create({
            'product_id': self.product.id, 'location_id': self.vendor_location.id, 'quantity': 5,
        })

    def test_cron_creates_activity_when_enabled(self):
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('bs_subcontracting_stock_dashboard.enable_alerts', 'True')
        params.set_param('bs_subcontracting_stock_dashboard.alert_days', '30')
        params.set_param('bs_subcontracting_stock_dashboard.notification_type', 'activity')

        self.env['subcontracting.stock.report'].cron_check_overdue_alerts()

        activity = self.env['mail.activity'].search([
            ('res_model', '=', 'res.partner'), ('res_id', '=', self.vendor.id),
        ])
        self.assertTrue(activity)

    def test_cron_noop_when_disabled(self):
        self.env['ir.config_parameter'].sudo().set_param('bs_subcontracting_stock_dashboard.enable_alerts', 'False')
        self.env['subcontracting.stock.report'].cron_check_overdue_alerts()
        activity = self.env['mail.activity'].search([
            ('res_model', '=', 'res.partner'), ('res_id', '=', self.vendor.id),
        ])
        self.assertFalse(activity)
