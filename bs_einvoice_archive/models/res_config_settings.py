from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    bs_einvoice_drive_client_id = fields.Char(
        "Google Drive Backup Client ID", config_parameter='google_bs_einvoice_drive_client_id')
    bs_einvoice_drive_client_secret = fields.Char(
        "Google Drive Backup Client Secret", config_parameter='google_bs_einvoice_drive_client_secret')
