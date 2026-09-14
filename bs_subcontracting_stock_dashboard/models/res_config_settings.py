from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    subcon_bucket_1_max = fields.Integer(
        'Aging Bucket 1 Max (days)', config_parameter='bs_subcontracting_stock_dashboard.bucket_1_max', default=7)
    subcon_bucket_2_max = fields.Integer(
        'Aging Bucket 2 Max (days)', config_parameter='bs_subcontracting_stock_dashboard.bucket_2_max', default=14)
    subcon_bucket_3_max = fields.Integer(
        'Aging Bucket 3 Max (days)', config_parameter='bs_subcontracting_stock_dashboard.bucket_3_max', default=30)
    subcon_enable_alerts = fields.Boolean(
        'Enable Alerts', config_parameter='bs_subcontracting_stock_dashboard.enable_alerts', default=True)
    subcon_alert_days = fields.Integer(
        'Days without expected receipt', config_parameter='bs_subcontracting_stock_dashboard.alert_days', default=30)
    subcon_notification_type = fields.Selection(
        [('activity', 'Activity (To-do)'), ('email', 'Email')],
        string='Notification Type', config_parameter='bs_subcontracting_stock_dashboard.notification_type', default='activity')
