from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMultichannelOversellingGuard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'MOG Test Warehouse',
            'code': 'MOGW',
        })
        cls.guarded_category = cls.env['product.category'].create({
            'name': 'MOG Guarded Category',
            'overselling_guard_enabled': True,
            'default_reserved_buffer_qty': 5.0,
        })
        cls.plain_category = cls.env['product.category'].create({
            'name': 'MOG Plain Category',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'MOG Test Product',
            'type': 'consu',
            'is_storable': True,
            'categ_id': cls.guarded_category.id,
        })
        cls.plain_product = cls.env['product.product'].create({
            'name': 'MOG Plain Product',
            'type': 'consu',
            'is_storable': True,
            'categ_id': cls.plain_category.id,
        })

    def _set_on_hand(self, product, quantity):
        self.env['stock.quant']._update_available_quantity(
            product, self.warehouse.lot_stock_id, quantity)

    def _create_reservation(self, product=None, quantity=1.0, channel='website',
                             state='active', expires_at=None, res_model='sale.order', res_id=1):
        reservation = self.env['stock.soft.reservation'].create({
            'product_id': (product or self.product).id,
            'warehouse_id': self.warehouse.id,
            'quantity': quantity,
            'channel': channel,
            'res_model': res_model,
            'res_id': res_id,
        })
        vals = {'state': state}
        if expires_at is not None:
            vals['expires_at'] = expires_at
        reservation.write(vals)
        return reservation

    # -- stock.soft.reservation -------------------------------------------------

    def test_reservation_expires_at_defaults_from_config_param(self):
        reservation = self._create_reservation()
        self.assertTrue(reservation.expires_at)
        # Default timeout is 15 minutes; allow a little slack for test runtime.
        expected = fields.Datetime.now() + timedelta(minutes=15)
        self.assertLess(abs((reservation.expires_at - expected).total_seconds()), 60)

    def test_cron_expires_past_due_reservations_only(self):
        past = self._create_reservation(
            expires_at=fields.Datetime.now() - timedelta(minutes=1))
        future = self._create_reservation(
            expires_at=fields.Datetime.now() + timedelta(minutes=30))

        self.env['stock.soft.reservation']._cron_expire_soft_reservations()

        self.assertEqual(past.state, 'expired')
        self.assertEqual(future.state, 'active')

    def test_get_active_reserved_qty_sums_only_active_unexpired(self):
        self._create_reservation(quantity=3.0, state='active',
                                  expires_at=fields.Datetime.now() + timedelta(minutes=10))
        self._create_reservation(quantity=2.0, state='active',
                                  expires_at=fields.Datetime.now() + timedelta(minutes=10))
        self._create_reservation(quantity=100.0, state='confirmed',
                                  expires_at=fields.Datetime.now() + timedelta(minutes=10))
        self._create_reservation(quantity=100.0, state='active',
                                  expires_at=fields.Datetime.now() - timedelta(minutes=1))

        total = self.env['stock.soft.reservation']._get_active_reserved_qty(
            self.product.id, self.warehouse.id)
        self.assertEqual(total, 5.0)

    def test_sync_soft_reservation_updates_existing_row(self):
        SoftReservation = self.env['stock.soft.reservation']
        SoftReservation._sync_soft_reservation(
            self.product.id, self.warehouse.id, 'website', 3.0, 'sale.order', 42)
        SoftReservation._sync_soft_reservation(
            self.product.id, self.warehouse.id, 'website', 7.0, 'sale.order', 42)

        reservations = SoftReservation.search([
            ('res_model', '=', 'sale.order'), ('res_id', '=', 42),
        ])
        self.assertEqual(len(reservations), 1)
        self.assertEqual(reservations.quantity, 7.0)

        SoftReservation._sync_soft_reservation(
            self.product.id, self.warehouse.id, 'website', 0.0, 'sale.order', 42)
        self.assertEqual(reservations.state, 'released')

    # -- category buffer/guard fallback -----------------------------------------

    def test_category_guard_climbs_to_parent(self):
        child = self.env['product.category'].create({
            'name': 'MOG Child Category',
            'parent_id': self.guarded_category.id,
        })
        self.assertTrue(child._is_overselling_guard_enabled())
        self.assertFalse(self.plain_category._is_overselling_guard_enabled())

    def test_buffer_qty_falls_back_to_category_default(self):
        self.assertEqual(
            self.product._get_reserved_buffer_qty(self.warehouse.id), 5.0)

        self.env['multichannel.stock.buffer'].create({
            'product_id': self.product.id,
            'warehouse_id': self.warehouse.id,
            'buffer_qty': 20.0,
        })
        self.assertEqual(
            self.product._get_reserved_buffer_qty(self.warehouse.id), 20.0)

    # -- get_sellable_now ---------------------------------------------------

    def test_get_sellable_now_guard_enabled(self):
        self._set_on_hand(self.product, 100.0)
        self._create_reservation(quantity=10.0, state='active',
                                  expires_at=fields.Datetime.now() + timedelta(minutes=10))
        # on_hand (100) - buffer (category default 5) - active reservation (10)
        self.assertEqual(self.product.get_sellable_now(self.warehouse.id), 85.0)

    def test_get_sellable_now_guard_disabled_behaves_like_plain_on_hand(self):
        self._set_on_hand(self.plain_product, 50.0)
        self._create_reservation(product=self.plain_product, quantity=10.0, state='active',
                                  expires_at=fields.Datetime.now() + timedelta(minutes=10))
        # Guard disabled on this category: buffer/reservations are ignored.
        self.assertEqual(self.plain_product.get_sellable_now(self.warehouse.id), 50.0)

    # -- oversell alert -------------------------------------------------------

    def test_check_and_flag_oversell_creates_alert_when_oversold(self):
        self._set_on_hand(self.product, 10.0)
        Alert = self.env['multichannel.oversell.alert']
        alert = Alert._check_and_flag_oversell(
            product=self.product, warehouse=self.warehouse, channel='pos',
            requested_qty=20.0)
        self.assertTrue(alert)
        self.assertEqual(alert.state, 'pending')
        # on_hand (10) - buffer (category default 5) - reserved (0) = 5 available
        self.assertEqual(alert.available_qty, 5.0)
        self.assertEqual(alert.oversell_qty, 15.0)

    def test_check_and_flag_oversell_no_alert_when_enough_stock(self):
        self._set_on_hand(self.product, 100.0)
        Alert = self.env['multichannel.oversell.alert']
        alert = Alert._check_and_flag_oversell(
            product=self.product, warehouse=self.warehouse, channel='pos',
            requested_qty=1.0)
        self.assertFalse(alert)

    def test_check_and_flag_oversell_skipped_when_guard_disabled(self):
        self._set_on_hand(self.plain_product, 1.0)
        Alert = self.env['multichannel.oversell.alert']
        alert = Alert._check_and_flag_oversell(
            product=self.plain_product, warehouse=self.warehouse, channel='pos',
            requested_qty=100.0)
        self.assertFalse(alert)

    def test_action_mark_reviewed(self):
        alert = self.env['multichannel.oversell.alert'].create({
            'product_id': self.product.id,
            'channel': 'pos',
            'requested_qty': 5.0,
            'available_qty': 1.0,
        })
        alert.action_mark_reviewed()
        self.assertEqual(alert.state, 'reviewed')

    # -- SQL report view ------------------------------------------------------

    def test_sellable_report_view_queries_without_error(self):
        self._set_on_hand(self.product, 42.0)
        Report = self.env['multichannel.sellable.report']
        rows = Report.search_read(
            [('product_id', '=', self.product.id), ('warehouse_id', '=', self.warehouse.id)],
            ['product_id', 'warehouse_id', 'on_hand', 'reserved', 'buffer_qty', 'sellable_now', 'status'])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['on_hand'], 42.0)
