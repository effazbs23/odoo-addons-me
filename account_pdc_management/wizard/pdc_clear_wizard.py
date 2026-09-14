from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PdcClearWizard(models.TransientModel):
    _name = 'pdc.clear.wizard'
    _description = 'Clear Post Dated Cheque'

    payment_id = fields.Many2one(
        'account.payment', string='Cheque', required=True, ondelete='cascade', readonly=True,
    )
    company_id = fields.Many2one(related='payment_id.company_id')
    currency_id = fields.Many2one(related='payment_id.currency_id')
    amount = fields.Monetary(related='payment_id.amount', string='Amount')
    cheque_number = fields.Char(related='payment_id.cheque_number', string='Cheque Number')
    partner_id = fields.Many2one(related='payment_id.partner_id', string='Partner')
    clearing_date = fields.Date(
        string='Clearing Date', required=True, default=fields.Date.context_today,
        help="Date the bank honoured the cheque. The clearing entry is posted on this date.",
    )
    bank_journal_id = fields.Many2one(
        'account.journal', string='Deposit Bank', required=True, check_company=True,
        domain="[('type', '=', 'bank'), ('is_pdc', '=', False)]",
        help="Bank account the cheque value is moved into.",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        payment = self.env['account.payment'].browse(
            res.get('payment_id') or self.env.context.get('active_id'))
        if not payment.exists():
            raise UserError(_("No cheque selected to clear."))
        res['payment_id'] = payment.id
        if 'bank_journal_id' in fields_list and not res.get('bank_journal_id'):
            res['bank_journal_id'] = (
                payment.pdc_bank_journal_id.id
                or payment.journal_id.pdc_bank_journal_id.id
                or self.env['account.journal'].search([
                    ('type', '=', 'bank'), ('is_pdc', '=', False),
                    ('company_id', '=', payment.company_id.id),
                ], limit=1).id
            )
        return res

    def action_confirm(self):
        self.ensure_one()
        self.payment_id.pdc_clear(self.clearing_date, self.bank_journal_id)
        return {'type': 'ir.actions.act_window_close'}
