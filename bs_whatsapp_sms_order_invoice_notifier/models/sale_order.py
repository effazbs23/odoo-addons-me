from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    notify_log_count = fields.Integer(compute='_compute_notify_log_count')
    partner_has_valid_notify_number = fields.Boolean(related='partner_id.has_valid_notify_number')

    def _compute_notify_log_count(self):
        for order in self:
            order.notify_log_count = self.env['bs.notify.log'].search_count([
                ('source_record_ref', '=', 'sale.order,%s' % order.id),
            ])

    def action_view_notify_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Notifications",
            'res_model': 'bs.notify.log',
            'view_mode': 'list,form',
            'domain': [('source_record_ref', '=', 'sale.order,%s' % self.id)],
        }

    def action_confirm(self):
        res = super().action_confirm()
        for order in self.filtered(lambda o: o.state == 'sale'):
            self.env['bs.notify.log']._send_notification('so_confirmed', order)
        return res
