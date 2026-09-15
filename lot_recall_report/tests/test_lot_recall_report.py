from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestLotRecallReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({'name': 'Recall Test Customer'})
        cls.vendor = cls.env['res.partner'].create({'name': 'Recall Test Vendor'})
        cls.product = cls.env['product.product'].create({
            'name': 'Recall Test Product',
            'type': 'consu',
            'is_storable': True,
            'tracking': 'lot',
        })
        cls.lot = cls.env['stock.lot'].create({
            'name': 'RECALL-LOT-001',
            'product_id': cls.product.id,
        })
        cls.warehouse = cls.env.ref('stock.warehouse0', raise_if_not_found=False) \
            or cls.env['stock.warehouse'].search([], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.customer_location = cls.env.ref('stock.stock_location_customers')
        cls.vendor_location = cls.env.ref('stock.stock_location_suppliers')

    def _do_picking(self, picking_type, partner, src, dst, qty):
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'partner_id': partner.id,
            'location_id': src.id,
            'location_dest_id': dst.id,
        })
        move = self.env['stock.move'].create({
            'name': self.product.name,
            'picking_id': picking.id,
            'product_id': self.product.id,
            'product_uom_qty': qty,
            'product_uom': self.product.uom_id.id,
            'location_id': src.id,
            'location_dest_id': dst.id,
        })
        picking.action_confirm()
        move.write({
            'move_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'lot_id': self.lot.id,
                'quantity': qty,
                'product_uom_id': self.product.uom_id.id,
                'location_id': src.id,
                'location_dest_id': dst.id,
            })],
        })
        picking.button_validate()
        return picking

    def test_forward_trace(self):
        self._do_picking(
            self.warehouse.out_type_id, self.customer,
            self.stock_location, self.customer_location, 5.0)

        report = self.env['lot.recall.report'].create({
            'lot_ids': [(6, 0, self.lot.ids)],
            'direction': 'forward',
        })
        report.action_generate()

        self.assertEqual(report.state, 'generated')
        self.assertEqual(len(report.forward_line_ids), 1)
        self.assertEqual(report.forward_line_ids.partner_id, self.customer)
        self.assertEqual(report.forward_quantity, 5.0)
        self.assertFalse(report.backward_line_ids)

    def test_backward_trace_purchase(self):
        self._do_picking(
            self.warehouse.in_type_id, self.vendor,
            self.vendor_location, self.stock_location, 10.0)

        report = self.env['lot.recall.report'].create({
            'lot_ids': [(6, 0, self.lot.ids)],
            'direction': 'backward',
        })
        report.action_generate()

        self.assertEqual(len(report.backward_line_ids), 1)
        self.assertEqual(report.backward_line_ids.partner_id, self.vendor)
        self.assertEqual(report.backward_quantity, 10.0)

    def test_both_directions_and_fully_traceable(self):
        self._do_picking(
            self.warehouse.in_type_id, self.vendor,
            self.vendor_location, self.stock_location, 10.0)
        self._do_picking(
            self.warehouse.out_type_id, self.customer,
            self.stock_location, self.customer_location, 4.0)

        report = self.env['lot.recall.report'].create({
            'lot_ids': [(6, 0, self.lot.ids)],
            'direction': 'both',
        })
        report.action_generate()

        self.assertTrue(report.fully_traceable)
        self.assertEqual(len(report.recall_line_ids), 2)

    def test_regenerate_clears_old_lines(self):
        self._do_picking(
            self.warehouse.out_type_id, self.customer,
            self.stock_location, self.customer_location, 3.0)

        report = self.env['lot.recall.report'].create({
            'lot_ids': [(6, 0, self.lot.ids)],
            'direction': 'forward',
        })
        report.action_generate()
        first_count = len(report.recall_line_ids)

        report.action_generate()
        self.assertEqual(len(report.recall_line_ids), first_count)

    def test_stock_lot_smart_button_creates_report(self):
        action = self.lot.action_generate_recall_report()
        report = self.env['lot.recall.report'].browse(action['res_id'])
        self.assertIn(self.lot, report.lot_ids)
        self.assertEqual(self.lot.recall_report_count, 1)
