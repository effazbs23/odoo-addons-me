from odoo import models, fields


class PettyCashSettlementLine(models.Model):
    _name = 'petty.cash.settlement.line'
    _description = 'Petty Cash Settlement Line'

    settlement_id = fields.Many2one('petty.cash.settlement', 'Settlement', required=True, ondelete='cascade')
    date = fields.Date('Date', required=True, default=fields.Date.context_today)
    description = fields.Char('Description', required=True)
    expense_account_id = fields.Many2one('account.account', 'Expense Account', required=True,
                                          domain=[('account_type', '=', 'expense')])
    amount = fields.Monetary('Amount', required=True)
    currency_id = fields.Many2one('res.currency', related='settlement_id.currency_id')
    company_id = fields.Many2one('res.company', related='settlement_id.company_id', store=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

