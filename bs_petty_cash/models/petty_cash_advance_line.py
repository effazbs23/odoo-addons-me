from odoo import models, fields, api


class PettyCashAdvanceLine(models.Model):
    _name = 'petty.cash.advance.line'
    _description = 'Petty Cash Advance Line'

    advance_id = fields.Many2one('petty.cash.advance', 'Advance', required=True, ondelete='cascade')
    purpose = fields.Char('Purpose', required=True)
    amount = fields.Monetary('Amount', required=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='advance_id.currency_id', store=True)
    company_id = fields.Many2one('res.company', related='advance_id.company_id', store=True)
    from_month = fields.Date(string='From Month')
    to_month = fields.Date(string='To Month')
    cost_center_id = fields.Many2one('account.analytic.account', string='Cost Center')

    @api.onchange('amount')
    def _onchange_amount(self):
        """Trigger recomputation of total in parent"""
        if self.advance_id:
            self.advance_id._compute_amount()
