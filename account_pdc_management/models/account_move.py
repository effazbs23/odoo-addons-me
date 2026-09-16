from odoo import _, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    pdc_payment_id = fields.Many2one(
        'account.payment', string='Post Dated Cheque', copy=False, readonly=True,
        index='btree_not_null', ondelete='set null',
        help="Cheque this entry was posted for.",
    )
    pdc_entry_type = fields.Selection(
        selection=[
            ('clearing', 'Cheque Clearing'),
            ('bounce', 'Cheque Bounce'),
            ('redeposit', 'Cheque Redeposit'),
            ('bank_charge', 'Bank Charge'),
            ('recovery', 'Bank Charge Recovery'),
        ],
        string='PDC Entry Type', copy=False, readonly=True, index='btree_not_null',
    )
    pdc_cheque_number = fields.Char(
        related='pdc_payment_id.cheque_number', string='Cheque Number', store=True,
    )

    def action_view_pdc_payment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Post Dated Cheque'),
            'res_model': 'account.payment',
            'res_id': self.pdc_payment_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
