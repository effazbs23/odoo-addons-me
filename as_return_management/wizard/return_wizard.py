from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ReturnWizard(models.TransientModel):
    _name = 'return.wizard'
    _description = 'Return Wizard'

    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        domain=[('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]
    )

    picking_id = fields.Many2one(
        'stock.picking',
        string='Delivery Order',
        domain=[('picking_type_code', '=', 'outgoing'), ('state', '=', 'done')]
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True
    )

    return_reason = fields.Text(
        string='Return Reason',
        required=True
    )

    def action_create_return_request(self):
        """Create return request from wizard"""
        if not self.invoice_id and not self.picking_id:
            raise UserError(_('Please select at least one document (Invoice or Delivery Order).'))

        vals = {
            'partner_id': self.partner_id.id,
            'invoice_id': self.invoice_id.id if self.invoice_id else False,
            'picking_id': self.picking_id.id if self.picking_id else False,
            'reason': self.return_reason,
        }

        return_request = self.env['return.request'].create(vals)
        return_request._generate_return_lines()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Return Request'),
            'res_model': 'return.request',
            'res_id': return_request.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        if self.invoice_id:
            self.partner_id = self.invoice_id.partner_id

    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        if self.picking_id:
            self.partner_id = self.picking_id.partner_id
