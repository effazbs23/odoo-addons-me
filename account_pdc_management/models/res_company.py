from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    pdc_operations_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='PDC Operations Journal',
        check_company=True,
        domain="[('type', '=', 'general')]",
        help="Miscellaneous journal the clearing, bounce, redeposit and bank charge entries "
             "are posted in. Keeping them out of the bank journals leaves the bank "
             "reconciliation showing only real bank movements.",
    )
    pdc_bank_charge_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Bank Charge Account',
        check_company=True,
        help="Expense account debited with the fee the bank deducts for a returned cheque.",
    )
    pdc_recovery_income_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Bank Charge Recovery Account',
        check_company=True,
        help="Income account credited when the bank charge is billed back to the partner. "
             "It offsets the bank charge expense, so the net effect on profit is nil.",
    )
    pdc_recovery_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Bank Charge Recovery Journal',
        check_company=True,
        domain="[('type', '=', 'sale')]",
        help="Sales journal used for the bank recovery invoice.",
    )
    pdc_recovery_tax_ids = fields.Many2many(
        comodel_name='account.tax',
        relation='res_company_pdc_recovery_tax_rel',
        column1='company_id', column2='tax_id',
        string='Bank Charge Recovery Taxes',
        check_company=True,
        domain="[('type_tax_use', '=', 'sale')]",
        help="Taxes proposed by default on the bank recovery invoice.",
    )

    # The settings pages reach these through related fields, which carry no domain of their
    # own, so guard the values here as well. A journal of the wrong type only fails much
    # later, when a PDC entry is posted, with a message that names none of these settings.
    @api.constrains('pdc_operations_journal_id')
    def _check_pdc_operations_journal(self):
        for company in self:
            journal = company.pdc_operations_journal_id
            if journal and journal.type != 'general':
                raise ValidationError(_(
                    "The PDC Operations journal has to be a Miscellaneous journal. "
                    "%(journal)s is a '%(type)s' journal.",
                    journal=journal.display_name, type=journal.type))

    @api.constrains('pdc_recovery_journal_id')
    def _check_pdc_recovery_journal(self):
        for company in self:
            journal = company.pdc_recovery_journal_id
            if journal and journal.type != 'sale':
                raise ValidationError(_(
                    "The Bank Charge Recovery journal has to be a Sales journal, because the "
                    "recovery is raised as a customer invoice. %(journal)s is a '%(type)s' "
                    "journal.",
                    journal=journal.display_name, type=journal.type))
