from odoo import models, fields, api


class BsResPartner(models.Model):
    _inherit = 'res.partner'

    bs_vendor_delay_index = fields.Float(string='BS Fulfillment Delay Variance', compute='_compute_bs_delay_index')

    def _compute_bs_delay_index(self):
        for partner in self:
            pos = self.env['purchase.order'].search([('partner_id', '=', partner.id), ('state', '=', 'purchase')])
            if not pos:
                partner.bs_vendor_delay_index = 0.0
                continue
            total_days_slip = 0.0
            valid_pos = 0
            for po in pos:
                for picking in po.picking_ids.filtered(lambda p: p.state == 'done'):
                    if picking.date_done and po.date_planned:
                        slip = (picking.date_done - po.date_planned).days
                        total_days_slip += max(0, slip)
                        valid_pos += 1
            partner.bs_vendor_delay_index = round(total_days_slip / valid_pos, 1) if valid_pos > 0 else 0.0
