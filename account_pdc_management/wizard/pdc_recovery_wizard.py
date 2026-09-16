from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PdcRecoveryWaiverWizard(models.TransientModel):
    """Waive part of a bank charge before it is billed to the partner."""
    _name = 'pdc.recovery.waiver.wizard'
    _description = 'Waive Part of a Bank Charge'

    recovery_id = fields.Many2one(
        'pdc.bank.recovery', string='Recovery', required=True, ondelete='cascade', readonly=True,
    )
    currency_id = fields.Many2one(related='recovery_id.currency_id')
    charge_amount = fields.Monetary(related='recovery_id.charge_amount', string='Bank Charge')
    waiver_amount = fields.Monetary(
        string='Waive', required=True,
        help="Part of the bank charge the company absorbs. The partner is billed for the rest.",
    )
    waiver_reason = fields.Text(string='Reason', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        recovery = self.env['pdc.bank.recovery'].browse(
            res.get('recovery_id') or self.env.context.get('active_id'))
        if not recovery.exists():
            raise UserError(_("No bank charge recovery selected."))
        res['recovery_id'] = recovery.id
        return res

    def action_confirm(self):
        self.ensure_one()
        recovery = self.recovery_id
        if recovery.state not in ('draft', 'charged'):
            raise UserError(_(
                "A waiver can only be applied while the recovery has not been invoiced yet."))
        if self.waiver_amount <= 0:
            raise UserError(_("The waived amount has to be greater than zero."))
        if self.waiver_amount > recovery.charge_amount:
            raise UserError(_("The waived amount cannot exceed the bank charge."))
        recovery.write({
            'waiver_amount': self.waiver_amount,
            'waiver_reason': self.waiver_reason,
        })
        recovery.message_post(body=_("Waived %(amount)s of the bank charge. Reason: %(reason)s",
                                     amount=self.waiver_amount, reason=self.waiver_reason))
        return {'type': 'ir.actions.act_window_close'}
