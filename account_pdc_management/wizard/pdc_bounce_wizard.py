from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PdcBounceWizard(models.TransientModel):
    _name = 'pdc.bounce.wizard'
    _description = 'Bounce Post Dated Cheque'

    payment_id = fields.Many2one(
        'account.payment', string='Cheque', required=True, ondelete='cascade', readonly=True,
    )
    company_id = fields.Many2one(related='payment_id.company_id')
    currency_id = fields.Many2one(related='payment_id.currency_id')
    amount = fields.Monetary(related='payment_id.amount', string='Amount')
    cheque_number = fields.Char(related='payment_id.cheque_number', string='Cheque Number')
    partner_id = fields.Many2one(related='payment_id.partner_id', string='Partner')
    is_second_bounce = fields.Boolean(
        string='Second Bounce', compute='_compute_is_second_bounce',
        help="The cheque was redeposited and has now been returned again.",
    )

    bounce_date = fields.Date(
        string='Bounce Date', required=True, default=fields.Date.context_today,
        help="Date the bank returned the cheque. The bounce entry is posted on this date.",
    )
    bounce_reason = fields.Text(
        string='Bounce Reason', required=True,
        help="Reason given by the bank, for example insufficient funds or signature mismatch.",
    )
    return_advice = fields.Binary(string='Bank Return Advice', attachment=False)
    return_advice_filename = fields.Char(string='Return Advice Filename')

    @api.depends('payment_id.pdc_state')
    def _compute_is_second_bounce(self):
        for wizard in self:
            wizard.is_second_bounce = wizard.payment_id.pdc_state == 'redeposited'

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        payment = self.env['account.payment'].browse(
            res.get('payment_id') or self.env.context.get('active_id'))
        if not payment.exists():
            raise UserError(_("No cheque selected to bounce."))
        res['payment_id'] = payment.id
        return res

    def action_confirm(self):
        self.ensure_one()
        if not (self.bounce_reason or '').strip():
            raise UserError(_("A bounce reason is required."))

        attachment = self.env['ir.attachment']
        if self.return_advice:
            # Materialised against the payment so the chatter can carry it: an
            # attachment=True binary would be tied to its field and filtered out.
            attachment = attachment.create({
                'name': self.return_advice_filename or _('Bank Return Advice'),
                'datas': self.return_advice,
                'res_model': 'account.payment',
                'res_id': self.payment_id.id,
            })

        self.payment_id.pdc_bounce(self.bounce_date, self.bounce_reason.strip(), attachment)
        return {'type': 'ir.actions.act_window_close'}
