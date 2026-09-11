from odoo import _, api, fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    days_to_expiry = fields.Integer(
        string='Days to Expiry', compute='_compute_expiry_alert')
    expiry_alert_threshold_days = fields.Integer(
        string='Alert Threshold (Days)', compute='_compute_expiry_alert')
    is_near_expiry = fields.Boolean(
        string='Near Expiry', compute='_compute_expiry_alert', search='_search_is_near_expiry')
    suggested_action = fields.Selection([
        ('markdown', 'Suggest Markdown/Promotion'),
        ('transfer', 'Suggest Internal Transfer'),
    ], string='Suggested Action', compute='_compute_expiry_alert')

    def _get_expiry_alert_threshold(self, category):
        return category.expiry_alert_days or int(
            self.env['ir.config_parameter'].sudo().get_param(
                'bs_inventory_expiry_alerts.expiry_alert_days_default', default=30))

    @api.depends('lot_id.expiration_date', 'product_id.categ_id', 'quantity', 'location_id.usage')
    def _compute_expiry_alert(self):
        today = fields.Date.context_today(self)
        for quant in self:
            threshold = self._get_expiry_alert_threshold(quant.product_id.categ_id)
            quant.expiry_alert_threshold_days = threshold
            if quant.quantity > 0 and quant.location_id.usage == 'internal' and quant.lot_id.expiration_date:
                delta = (quant.lot_id.expiration_date.date() - today).days
                quant.days_to_expiry = delta
                quant.is_near_expiry = delta <= threshold
                if not quant.is_near_expiry:
                    quant.suggested_action = False
                elif delta <= threshold / 2.0:
                    quant.suggested_action = 'markdown'
                else:
                    quant.suggested_action = 'transfer'
            else:
                quant.days_to_expiry = 0
                quant.is_near_expiry = False
                quant.suggested_action = False

    def _search_is_near_expiry(self, operator, value):
        near = (self.env['stock.quant'].search([('lot_id', '!=', False)]).filtered('is_near_expiry')).ids
        return [('id', 'in', near)]

    def action_open_internal_transfer(self):
        self.ensure_one()
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id', '=', self.warehouse_id.id),
        ], limit=1)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_picking_type_id': picking_type.id,
                'default_location_id': self.location_id.id,
                'default_move_ids_without_package': [(0, 0, {
                    'name': self.product_id.display_name,
                    'product_id': self.product_id.id,
                    'product_uom_qty': self.quantity,
                    'product_uom': self.product_uom_id.id,
                    'location_id': self.location_id.id,
                    'lot_ids': [(4, self.lot_id.id)] if self.lot_id else False,
                })],
            },
            'name': _('Internal Transfer'),
        }
