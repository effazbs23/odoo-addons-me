from datetime import timedelta

from odoo import fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class BrandingTestCommon(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= (
            cls.env.ref('sales_team.group_sale_manager')
            + cls.env.ref('stock.group_stock_manager')
            + cls.env.ref('purchase.group_purchase_manager')
        )
        cls.company = cls.company_data['company']
        cls.partner = cls.env['res.partner'].create({'name': 'Branding Test Customer'})
        cls.product = cls.env['product.product'].create({
            'name': 'Branding Test Product', 'type': 'consu', 'is_storable': True,
            'invoice_policy': 'order', 'list_price': 50.0,
        })
        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'Branding Test Warehouse', 'code': 'BTWH', 'company_id': cls.company.id,
        })

    def _create_invoice(self, company=None, partner=None, due_days=0):
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': (partner or self.partner).id,
            'company_id': (company or self.company).id,
            'invoice_date': fields.Date.today(),
            'invoice_date_due': fields.Date.today() + timedelta(days=due_days),
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id, 'quantity': 1, 'price_unit': 50.0,
            })],
        })
        move.action_post()
        return move

    def _create_sale_order(self, company=None, partner=None):
        return self.env['sale.order'].create({
            'partner_id': (partner or self.partner).id,
            'company_id': (company or self.company).id,
            'order_line': [(0, 0, {
                'product_id': self.product.id, 'product_uom_qty': 1, 'price_unit': 50.0,
            })],
        })

    def _create_purchase_order(self, company=None, partner=None):
        return self.env['purchase.order'].create({
            'partner_id': (partner or self.partner).id,
            'company_id': (company or self.company).id,
            'order_line': [(0, 0, {
                'product_id': self.product.id, 'product_qty': 1,
                'price_unit': 20.0, 'name': self.product.name,
            })],
        })

    def _create_delivery_picking(self, company=None, partner=None, warehouse=None):
        warehouse = warehouse or self.warehouse
        return self.env['stock.picking'].create({
            'partner_id': (partner or self.partner).id,
            'company_id': (company or self.company).id,
            'picking_type_id': warehouse.out_type_id.id,
            'location_id': warehouse.lot_stock_id.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
        })
