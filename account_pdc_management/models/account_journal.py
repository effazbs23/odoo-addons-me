from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_pdc = fields.Boolean(
        string='Post Dated Cheque Journal',
        help="Payments registered in this journal are post dated cheques. Their amount is "
             "held in the PDC account below instead of the bank account, until the cheque "
             "is cleared or bounced.",
    )
    pdc_account_id = fields.Many2one(
        comodel_name='account.account',
        string='PDC Holding Account',
        check_company=True,
        help="Account holding the value of cheques that have not been honoured yet, for "
             "example 'Cheques Received - Post Dated'. It replaces the outstanding "
             "receipts / payments account on payments made in this journal.",
    )
    pdc_bank_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Deposit Bank Journal',
        check_company=True,
        domain="[('type', '=', 'bank'), ('is_pdc', '=', False)]",
        help="Bank journal the cheques of this journal are deposited into. It provides the "
             "default bank account of the clearing entry; it can still be changed cheque "
             "by cheque when clearing.",
    )

    @api.constrains('is_pdc', 'pdc_account_id')
    def _check_pdc_account(self):
        for journal in self:
            if journal.is_pdc and not journal.pdc_account_id:
                raise ValidationError(_(
                    "Journal %s is marked as a Post Dated Cheque journal, so it needs a PDC "
                    "holding account.", journal.display_name))

    @api.onchange('is_pdc')
    def _onchange_is_pdc(self):
        """A PDC journal behaves like a bank journal, so default it to one."""
        if self.is_pdc and self.type not in ('bank', 'cash'):
            self.type = 'bank'
