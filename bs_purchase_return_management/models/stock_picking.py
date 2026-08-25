from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    return_request_ids = fields.One2many(
        'return.request',
        'picking_id',
        string='Return Requests'
    )

    return_request_count = fields.Integer(
        string='Return Request Count',
        compute='_compute_return_request_count'
    )

    @api.depends('return_request_ids')
    def _compute_return_request_count(self):
        for picking in self:
            picking.return_request_count = len(picking.return_request_ids)

    def action_view_return_requests(self):
        """View related vendor return requests."""
        action = self.env.ref('bs_purchase_return_management.action_vendor_return').read()[0]
        if len(self.return_request_ids) > 1:
            action['domain'] = [('id', 'in', self.return_request_ids.ids)]
        elif self.return_request_ids:
            action['views'] = [
                (self.env.ref('bs_purchase_return_management.view_vendor_return_form').id, 'form')]
            action['res_id'] = self.return_request_ids.id
        return action
