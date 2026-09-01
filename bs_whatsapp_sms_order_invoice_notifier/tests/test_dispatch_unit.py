from unittest.mock import patch

from odoo.tests.common import tagged

from ..models.bs_notify_utils import is_valid_e164, render_template
from .common import NotifyTestCommon


@tagged('post_install', '-at_install')
class TestPhoneValidation(NotifyTestCommon):
    """Unit: E.164 validation (spec section 10)."""

    def test_valid_numbers_accepted(self):
        for number in ('+15550001111', '+8801711223344', '+442071838750'):
            self.assertTrue(is_valid_e164(number), number)

    def test_invalid_numbers_rejected(self):
        for number in (None, '', '0171122334', '15550001111', '+0155500011', 'not-a-number', '+1'):
            self.assertFalse(is_valid_e164(number), number)


@tagged('post_install', '-at_install')
class TestTemplateRendering(NotifyTestCommon):
    """Unit: placeholder substitution (spec section 10)."""

    def test_all_documented_tokens_substituted(self):
        template = (
            "{{partner_name}} {{order_reference}} {{amount_total}} "
            "{{due_date}} {{invoice_number}} {{payment_link}}"
        )
        tokens = {
            'partner_name': 'Jane Doe', 'order_reference': 'S00001', 'amount_total': 100.0,
            'due_date': '2026-09-15', 'invoice_number': 'INV/2026/0001', 'payment_link': 'https://pay.example/x',
        }
        rendered = render_template(template, tokens)
        for value in tokens.values():
            self.assertIn(str(value), rendered)

    def test_unknown_token_left_blank_not_raised(self):
        self.assertEqual(render_template("Hi {{nonexistent_token}}!", {}), "Hi !")


@tagged('post_install', '-at_install')
class TestDispatchNeverRaises(NotifyTestCommon):
    """Unit: the dispatch method never raises -- a gateway exception must
    never block the business transaction that triggered it (spec section
    10, called out as the single most important test in the module).
    """

    def test_gateway_exception_does_not_block_so_confirmation(self):
        order = self._create_sale_order()
        with patch(
            'odoo.addons.bs_whatsapp_sms_order_invoice_notifier.models.gateway_adapters.send_message',
            side_effect=ConnectionError("gateway is down"),
        ):
            order.action_confirm()  # must not raise
        self.assertEqual(order.state, 'sale')
        log = self.env['bs.notify.log'].search([
            ('source_record_ref', '=', 'sale.order,%s' % order.id), ('event_type', '=', 'so_confirmed'),
        ])
        self.assertTrue(log)
        self.assertTrue(all(entry.status == 'failed' for entry in log))

    def test_internal_dispatch_bug_does_not_escape(self):
        """Even a bug inside the dispatch logic itself (not just a gateway
        error) must be swallowed by the outer safety net.
        """
        order = self._create_sale_order()
        with patch.object(
            type(self.env['bs.notify.log']), '_send_notification_unsafe', side_effect=RuntimeError("boom"),
        ):
            self.env['bs.notify.log']._send_notification('so_confirmed', order)  # must not raise
