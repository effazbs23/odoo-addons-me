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
        """View related return requests"""
        # an incoming receipt can only be the anchor of vendor return requests
        is_vendor = self.picking_type_code == 'incoming'
        action_xmlid = ('as_return_management.action_vendor_return' if is_vendor
                        else 'as_return_management.action_return_request')
        form_xmlid = ('as_return_management.view_vendor_return_form' if is_vendor
                      else 'as_return_management.view_return_request_form')
        action = self.env.ref(action_xmlid).read()[0]
        if len(self.return_request_ids) > 1:
            action['domain'] = [('id', 'in', self.return_request_ids.ids)]
        elif self.return_request_ids:
            action['views'] = [(self.env.ref(form_xmlid).id, 'form')]
            action['res_id'] = self.return_request_ids.id
        return action
