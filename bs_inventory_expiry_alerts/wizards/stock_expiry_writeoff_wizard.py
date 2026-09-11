from odoo import api, fields, models


class StockExpiryWriteoffWizard(models.TransientModel):
    _name = 'stock.expiry.writeoff.wizard'
    _description = 'Expiry Write-off Assistant'

    quant_id = fields.Many2one('stock.quant', string='Source Stock')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    lot_id = fields.Many2one('stock.lot', string='Lot/Serial')
    location_id = fields.Many2one('stock.location', string='Source Location', required=True,
                                   domain="[('usage', '=', 'internal')]")
    scrap_location_id = fields.Many2one('stock.location', string='Scrap Location', required=True,
                                         domain="[('scrap_location', '=', True)]")
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True)
    scrap_qty = fields.Float(string='Quantity', required=True, default=1.0)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        quant = self.env['stock.quant'].browse(self.env.context.get('active_id'))
        if self.env.context.get('active_model') == 'stock.quant' and quant.exists():
            default_scrap_location = self.env['stock.location'].search(
                [('usage', '=', 'inventory'), ('company_id', 'in', [quant.company_id.id, False])], limit=1)
            res.update({
                'quant_id': quant.id,
                'product_id': quant.product_id.id,
                'lot_id': quant.lot_id.id,
                'location_id': quant.location_id.id,
                'product_uom_id': quant.product_uom_id.id,
                'scrap_qty': quant.quantity,
                'scrap_location_id': default_scrap_location.id,
            })
        return res

    def action_create_writeoff(self):
        self.ensure_one()
        scrap = self.env['stock.scrap'].create({
            'product_id': self.product_id.id,
            'lot_id': self.lot_id.id,
            'location_id': self.location_id.id,
            'scrap_location_id': self.scrap_location_id.id,
            'product_uom_id': self.product_uom_id.id,
            'scrap_qty': self.scrap_qty,
            'is_expiry_writeoff': True,
        })
        scrap.action_validate()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.scrap',
            'res_id': scrap.id,
            'view_mode': 'form',
            'target': 'current',
        }
