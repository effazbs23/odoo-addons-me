from odoo import models, fields, api

CHANNELS = [
    ('shopify', 'Shopify'), ('amazon', 'Amazon'), ('woo', 'WooCommerce'), ('pos', 'POS')
]


class BsSaleOrder(models.Model):
    _inherit = 'sale.order'

    bs_channel = fields.Selection(CHANNELS, string='BS Channel', index=True)
    bs_commission_fees = fields.Monetary(string='BS Commissions')
    bs_marketing_spend = fields.Monetary(string='BS Ad Spend')
    bs_actual_shipping_cost = fields.Monetary(string='BS Shipping Cost')


class BsEcomProfitEngine(models.AbstractModel):
    _name = 'bs.ecom.profit.engine'
    _description = 'BS Profit Analytics Engine'

    def _channel_margins(self, orders):
        gross = sum(orders.mapped('amount_untaxed'))
        fees = sum(orders.mapped('bs_commission_fees'))
        ads = sum(orders.mapped('bs_marketing_spend'))
        shipping = sum(orders.mapped('bs_actual_shipping_cost'))
        cogs = sum(
            sum(l.product_id.standard_price * l.product_uom_qty for l in o.order_line if l.product_id)
            for o in orders
        )
        net = gross - (cogs + fees + ads + shipping)
        return {
            'gross_revenue': round(gross, 2),
            'cogs': round(cogs, 2),
            'channel_fees': round(fees, 2),
            'marketing_spend': round(ads, 2),
            'shipping_cost': round(shipping, 2),
            'net_profit': round(net, 2),
            'margin_ratio': round((net / gross * 100), 2) if gross > 0 else 0.0,
        }

    @api.model
    def get_net_margins(self):
        orders = self.env['sale.order'].search([('state', '=', 'sale')])
        result = self._channel_margins(orders)
        result['channels'] = []
        for code, label in CHANNELS:
            channel_orders = orders.filtered(lambda o: o.bs_channel == code)
            metrics = self._channel_margins(channel_orders)
            metrics.update({'code': code, 'label': label})
            result['channels'].append(metrics)
        return result
