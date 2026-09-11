from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    expiry_alert_days_default = fields.Integer(
        string='Default Expiry Alert (Days)', default=30,
        config_parameter='bs_inventory_expiry_alerts.expiry_alert_days_default',
        help="Fallback near-expiry threshold used for product categories that "
             "don't set their own Expiry Alert (Days).")
