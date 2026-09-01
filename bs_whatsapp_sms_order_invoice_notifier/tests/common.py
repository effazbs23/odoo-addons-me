from odoo.tests.common import TransactionCase


class NotifyTestCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Notify Test Customer',
            'mobile': '+15550001111',
            'email': 'notify.customer@example.com',
        })
        cls.partner_no_phone = cls.env['res.partner'].create({
            'name': 'No Phone Customer',
            'email': 'nophone.customer@example.com',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Notify Test Product',
            'type': 'consu',
            'is_storable': True,
            'invoice_policy': 'order',
            'list_price': 100.0,
        })
        cls.whatsapp_gateway = cls.env['bs.notify.gateway.config'].create({
            'channel': 'whatsapp', 'provider': 'generic_rest',
            'api_endpoint': 'https://example.test/whatsapp', 'sender_id': '+15559990000',
        })
        cls.sms_gateway = cls.env['bs.notify.gateway.config'].create({
            'channel': 'sms', 'provider': 'generic_rest',
            'api_endpoint': 'https://example.test/sms', 'sender_id': '+15559990000',
        })

    def _create_sale_order(self, partner=None):
        return self.env['sale.order'].create({
            'partner_id': (partner or self.partner).id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        })

    def _validate_delivery(self, order):
        picking = order.picking_ids
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        picking.button_validate()
        return picking

    def _post_invoice(self, order):
        order._create_invoices()
        invoice = order.invoice_ids
        invoice.action_post()
        return invoice

    def _register_full_payment(self, invoice):
        wizard = self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=invoice.ids,
        ).create({})
        wizard.action_create_payments()
