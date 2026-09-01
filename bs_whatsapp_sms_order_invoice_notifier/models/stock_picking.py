from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    notify_log_count = fields.Integer(compute='_compute_notify_log_count')
    partner_has_valid_notify_number = fields.Boolean(related='partner_id.has_valid_notify_number')

    def _compute_notify_log_count(self):
        for picking in self:
            picking.notify_log_count = self.env['bs.notify.log'].search_count([
                ('source_record_ref', '=', 'stock.picking,%s' % picking.id),
            ])

    def action_view_notify_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Notifications",
            'res_model': 'bs.notify.log',
            'view_mode': 'list,form',
            'domain': [('source_record_ref', '=', 'stock.picking,%s' % self.id)],
        }

    def button_validate(self):
        res = super().button_validate()
        # Only outgoing pickings represent a customer-facing delivery;
        # internal transfers/receipts should never fire "delivery shipped".
        for picking in self.filtered(lambda p: p.state == 'done' and p.picking_type_id.code == 'outgoing'):
            self.env['bs.notify.log']._send_notification('delivery_shipped', picking)
        return res
