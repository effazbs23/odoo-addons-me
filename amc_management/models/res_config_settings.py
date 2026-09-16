from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    amc_provision_journal_id = fields.Many2one(
        'account.journal', string='AMC Provision Journal',
        config_parameter='amc_management.provision_journal_id',
        domain="[('type', '=', 'general')]",
        help='Journal used for AMC provision and reversal entries. Falls back to the first '
             'miscellaneous journal of the company when empty.')
    amc_expiry_reminder_days = fields.Integer(
        string='AMC Expiry Reminder (Days)', default=15,
        config_parameter='amc_management.expiry_reminder_days',
        help='Mail the contractor this many days before a contract ends. Set to zero to '
             'switch the reminder off.')
