from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # A related field does not inherit the domain of the field it points at, so every
    # domain below has to be repeated here. Without them the settings pickers list every
    # journal / account and a wrong pick only surfaces later, as a posting error.
    pdc_operations_journal_id = fields.Many2one(
        related='company_id.pdc_operations_journal_id', readonly=False,
        string='PDC Operations Journal',
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
    )
    pdc_bank_charge_account_id = fields.Many2one(
        related='company_id.pdc_bank_charge_account_id', readonly=False,
        string='Bank Charge Account',
        domain="[('company_ids', '=', company_id)]",
    )
    pdc_recovery_income_account_id = fields.Many2one(
        related='company_id.pdc_recovery_income_account_id', readonly=False,
        string='Bank Charge Recovery Account',
        domain="[('company_ids', '=', company_id)]",
    )
    pdc_recovery_journal_id = fields.Many2one(
        related='company_id.pdc_recovery_journal_id', readonly=False,
        string='Bank Charge Recovery Journal',
        domain="[('type', '=', 'sale'), ('company_id', '=', company_id)]",
    )
    pdc_recovery_tax_ids = fields.Many2many(
        related='company_id.pdc_recovery_tax_ids', readonly=False,
        string='Bank Charge Recovery Taxes',
        domain="[('type_tax_use', '=', 'sale'), ('company_id', '=', company_id)]",
    )
