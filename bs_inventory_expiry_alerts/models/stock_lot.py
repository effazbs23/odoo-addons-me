from odoo import SUPERUSER_ID, _, api, fields, models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    expiry_threshold_activity_created = fields.Boolean(
        string='Expiry Threshold Activity Created',
        help="Set once an activity has been created for this lot crossing its "
             "category expiry-alert threshold, to avoid duplicate activities.")

    @api.model
    def _cron_create_expiry_threshold_activities(self):
        candidate_lots = self.env['stock.lot'].search([
            ('expiration_date', '!=', False),
            ('expiry_threshold_activity_created', '=', False),
        ])
        if not candidate_lots:
            return
        quants = self.env['stock.quant'].search([
            ('lot_id', 'in', candidate_lots.ids),
            ('quantity', '>', 0),
            ('location_id.usage', '=', 'internal'),
        ])
        handled_lots = self.env['stock.lot']
        for quant in quants:
            lot = quant.lot_id
            if lot in handled_lots or not quant.is_near_expiry:
                continue
            responsible = (
                quant.product_id.with_company(lot.company_id).responsible_id.id
                or quant.product_id.responsible_id.id
                or SUPERUSER_ID
            )
            lot.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=responsible,
                summary=_("Near-Expiry Alert"),
                note=_(
                    "Lot/Serial %(lot)s of %(product)s is %(days)s day(s) from expiry "
                    "(warehouse: %(warehouse)s). Suggested action: %(action)s.",
                    lot=lot.name, product=quant.product_id.display_name,
                    days=quant.days_to_expiry, warehouse=quant.warehouse_id.display_name or _('N/A'),
                    action=dict(quant._fields['suggested_action'].selection).get(
                        quant.suggested_action, _('review stock')),
                ),
            )
            handled_lots |= lot
        handled_lots.write({'expiry_threshold_activity_created': True})
