from datetime import timedelta
from unittest.mock import patch

from odoo.exceptions import AccessError
from odoo.fields import Date
from odoo.tests.common import tagged

from .common import NotifyTestCommon

SEND_PATH = 'odoo.addons.bs_whatsapp_sms_order_invoice_notifier.models.gateway_adapters.send_message'


@tagged('post_install', '-at_install')
class TestTriggersFireOnce(NotifyTestCommon):
    """Integration: each of the five trigger events fires exactly once per
    record under normal flow (spec section 10).
    """

    def _log_count(self, event_type, record):
        return self.env['bs.notify.log'].search_count([
            ('event_type', '=', event_type),
            ('source_record_ref', '=', '%s,%s' % (record._name, record.id)),
        ])

    def test_so_confirmed_fires_once(self):
        order = self._create_sale_order()
        with patch(SEND_PATH, return_value='ok'):
            order.action_confirm()
        self.assertEqual(self._log_count('so_confirmed', order), 2)  # whatsapp + sms (channel='both')

    def test_delivery_shipped_fires_once(self):
        order = self._create_sale_order()
        with patch(SEND_PATH, return_value='ok'):
            order.action_confirm()
            picking = self._validate_delivery(order)
        self.assertEqual(self._log_count('delivery_shipped', picking), 2)

    def test_invoice_posted_fires_once(self):
        order = self._create_sale_order()
        with patch(SEND_PATH, return_value='ok'):
            order.action_confirm()
            invoice = self._post_invoice(order)
        self.assertEqual(self._log_count('invoice_posted', invoice), 2)

    def test_payment_received_fires_once_and_not_on_partial(self):
        order = self._create_sale_order()
        with patch(SEND_PATH, return_value='ok'):
            order.action_confirm()
            invoice = self._post_invoice(order)
            self.assertEqual(self._log_count('payment_received', invoice), 0, "must not fire before payment")
            self._register_full_payment(invoice)
        self.assertEqual(invoice.payment_state, 'paid')
        self.assertEqual(self._log_count('payment_received', invoice), 2)

    def test_overdue_cron_fires_once_per_invoice(self):
        order = self._create_sale_order()
        with patch(SEND_PATH, return_value='ok'):
            order.action_confirm()
            invoice = self._post_invoice(order)
        invoice.invoice_date_due = Date.context_today(invoice) - timedelta(days=1)
        with patch(SEND_PATH, return_value='ok'):
            self.env['account.move']._cron_notify_overdue_invoices()
        self.assertEqual(self._log_count('invoice_overdue', invoice), 2)


@tagged('post_install', '-at_install')
class TestDuplicateGuards(NotifyTestCommon):
    """Integration: duplicate-trigger guard and overdue fire-once guard
    (spec section 9 / 10).
    """

    def test_duplicate_trigger_guarded(self):
        order = self._create_sale_order()
        with patch(SEND_PATH, return_value='ok'):
            order.action_confirm()
            # Simulate the lifecycle method firing a second time for the
            # same already-confirmed record (e.g. re-entrant call).
            self.env['bs.notify.log']._send_notification('so_confirmed', order)
        self.assertEqual(
            self.env['bs.notify.log'].search_count([
                ('event_type', '=', 'so_confirmed'),
                ('source_record_ref', '=', 'sale.order,%s' % order.id),
            ]), 2,
        )

    def test_overdue_cron_does_not_repeat_daily(self):
        order = self._create_sale_order()
        with patch(SEND_PATH, return_value='ok'):
            order.action_confirm()
            invoice = self._post_invoice(order)
        invoice.invoice_date_due = Date.context_today(invoice) - timedelta(days=1)
        with patch(SEND_PATH, return_value='ok'):
            self.env['account.move']._cron_notify_overdue_invoices()
            self.env['account.move']._cron_notify_overdue_invoices()  # simulates the next day's run
        self.assertEqual(
            self.env['bs.notify.log'].search_count([
                ('event_type', '=', 'invoice_overdue'),
                ('source_record_ref', '=', 'account.move,%s' % invoice.id),
            ]), 2,
        )

    def test_overdue_guard_blocks_even_on_prior_failure(self):
        """A failed first attempt still counts as "already tried" for the
        fire-once overdue guard -- it must not spam-retry daily; recovery
        is via the manual resend button.
        """
        order = self._create_sale_order()
        with patch(SEND_PATH, return_value='ok'):
            order.action_confirm()
            invoice = self._post_invoice(order)
        invoice.invoice_date_due = Date.context_today(invoice) - timedelta(days=1)
        with patch(SEND_PATH, side_effect=ConnectionError("down")):
            self.env['account.move']._cron_notify_overdue_invoices()
        with patch(SEND_PATH, return_value='ok'):
            self.env['account.move']._cron_notify_overdue_invoices()
        logs = self.env['bs.notify.log'].search([
            ('event_type', '=', 'invoice_overdue'), ('source_record_ref', '=', 'account.move,%s' % invoice.id),
        ])
        self.assertEqual(len(logs), 2)  # only the first (failed) run's two channel attempts
        self.assertTrue(all(entry.status == 'failed' for entry in logs))


@tagged('post_install', '-at_install')
class TestManualResend(NotifyTestCommon):
    """Integration: manual resend re-attempts and logs a new entry without
    duplicating (or mutating) the original log (spec section 10).
    """

    def test_resend_creates_new_entry_bypassing_guard(self):
        order = self._create_sale_order()
        with patch(SEND_PATH, side_effect=ConnectionError("down")):
            order.action_confirm()
        original_logs = self.env['bs.notify.log'].search([
            ('event_type', '=', 'so_confirmed'), ('source_record_ref', '=', 'sale.order,%s' % order.id),
        ])
        self.assertEqual(len(original_logs), 2)
        self.assertTrue(all(entry.status == 'failed' for entry in original_logs))

        with patch(SEND_PATH, return_value='ok'):
            original_logs[0].action_resend()

        self.assertEqual(original_logs[0].status, 'failed', "the original failed log must not be mutated")
        all_logs = self.env['bs.notify.log'].search([
            ('event_type', '=', 'so_confirmed'), ('source_record_ref', '=', 'sale.order,%s' % order.id),
        ])
        self.assertEqual(len(all_logs), 3)
        self.assertTrue(any(entry.status == 'sent' for entry in all_logs))


@tagged('post_install', '-at_install')
class TestSkippedNoPhone(NotifyTestCommon):

    def test_missing_phone_skipped_not_silently_dropped(self):
        order = self._create_sale_order(partner=self.partner_no_phone)
        order.action_confirm()
        log = self.env['bs.notify.log'].search([
            ('event_type', '=', 'so_confirmed'), ('source_record_ref', '=', 'sale.order,%s' % order.id),
        ])
        self.assertEqual(len(log), 1)
        self.assertEqual(log.status, 'skipped_no_phone')
        self.assertFalse(order.partner_has_valid_notify_number)


@tagged('post_install', '-at_install')
class TestNonBlockingRegression(NotifyTestCommon):
    """Regression: gateway failure never rolls back or blocks the SO
    confirmation, delivery validation, or invoice posting themselves
    (spec section 10).
    """

    def test_full_flow_completes_despite_permanent_gateway_failure(self):
        order = self._create_sale_order()
        with patch(SEND_PATH, side_effect=ConnectionError("gateway permanently down")):
            order.action_confirm()
            self.assertEqual(order.state, 'sale')

            picking = self._validate_delivery(order)
            self.assertEqual(picking.state, 'done')

            invoice = self._post_invoice(order)
            self.assertEqual(invoice.state, 'posted')

            self._register_full_payment(invoice)
            self.assertEqual(invoice.payment_state, 'paid')


@tagged('post_install', '-at_install')
class TestNonAdminUserDispatch(NotifyTestCommon):
    """Regression (found by production-readiness audit): bs.notify.gateway.config
    is deliberately restricted to base.group_system (it holds API secrets), but
    the dispatch method must still be able to look it up regardless of which
    user's action triggered it -- a plain sales user confirming an order has
    no reason to have System access, and previously got a silently-swallowed
    AccessError with zero log entry written, instead of a working send.
    """

    def test_plain_sales_user_triggers_a_real_send(self):
        sales_user = self.env['res.users'].create({
            'name': 'Plain Sales User', 'login': 'plain_sales_user_test',
            'group_ids': [(6, 0, [self.env.ref('sales_team.group_sale_salesman').id])],
        })
        # sales_team.group_sale_salesman is "Own Documents Only" -- the
        # order must actually belong to this user, not just be confirmed
        # by them, or write access is denied for an unrelated reason.
        order = self.env['sale.order'].with_user(sales_user).create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id, 'product_uom_qty': 1, 'price_unit': 100.0,
            })],
        })
        with patch(SEND_PATH, return_value='ok'):
            order.with_user(sales_user).action_confirm()
        self.assertEqual(order.state, 'sale')
        logs = self.env['bs.notify.log'].search([
            ('event_type', '=', 'so_confirmed'), ('source_record_ref', '=', 'sale.order,%s' % order.id),
        ])
        self.assertEqual(len(logs), 2)
        self.assertTrue(all(entry.status == 'sent' for entry in logs))


@tagged('post_install', '-at_install')
class TestNotifyLogAccessControl(NotifyTestCommon):
    """Regression (found by production-readiness audit, 60.audit.md): bs.notify.log
    had no record rule at all, so any internal employee -- in ANY company, with
    no relation whatsoever to the order -- could read every other company's
    notification log (customer names, phone numbers, order/invoice amounts,
    message bodies), and action_resend carried no authorization check, so
    they could also trigger a real outbound resend on it. Verified live via
    odoo-bin shell before this fix existed.
    """

    def test_unrelated_company_user_cannot_see_the_log(self):
        other_company = self.env['res.company'].create({'name': 'Unrelated Company'})
        outsider = self.env['res.users'].create({
            'name': 'Totally Unrelated Employee', 'login': 'outsider_test',
            'company_id': other_company.id, 'company_ids': [(6, 0, [other_company.id])],
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        order = self._create_sale_order()
        with patch(SEND_PATH, return_value='ok'):
            order.action_confirm()
        log = self.env['bs.notify.log'].search([('source_record_ref', '=', 'sale.order,%s' % order.id)])
        self.assertTrue(log)

        visible_to_outsider = self.env['bs.notify.log'].with_user(outsider).search([])
        self.assertFalse(
            visible_to_outsider & log,
            "an employee of a completely unrelated company must not see this company's notification log",
        )

    def test_plain_employee_cannot_resend(self):
        plain_employee = self.env['res.users'].create({
            'name': 'Plain Employee, No Sales Rights', 'login': 'plain_employee_test',
            'company_id': self.env.company.id, 'company_ids': [(6, 0, [self.env.company.id])],
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        order = self._create_sale_order()
        with patch(SEND_PATH, side_effect=ConnectionError("down")):
            order.action_confirm()
        log = self.env['bs.notify.log'].search([
            ('source_record_ref', '=', 'sale.order,%s' % order.id),
        ], limit=1)

        with self.assertRaises(AccessError):
            log.with_user(plain_employee).action_resend()
