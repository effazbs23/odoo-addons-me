from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PettyCashAdvanceSettlementLine(models.Model):
    _name = 'petty.cash.advance.settlement.line'
    _description = 'Petty Cash Advance Settlement Line'

    settlement_id = fields.Many2one('petty.cash.settlement', 'Settlement', required=True, ondelete='cascade')
    advance_id = fields.Many2one('petty.cash.advance', 'Advance', required=True,
                                 domain="[('employee_id', '=', parent.employee_id), ('state', 'in', ['paid', 'partially_settled']), ('company_id', '=', parent.company_id)]")

    advance_amount = fields.Monetary(related='advance_id.amount', readonly=True)
    advance_balance = fields.Monetary(related='advance_id.balance', readonly=True)
    settled_amount = fields.Monetary('Settlement Amount', required=True)
    settlement_mode = fields.Selection(related='settlement_id.settlement_mode', string='Settlement Mode', readonly=True)

    currency_id = fields.Many2one('res.currency', related='settlement_id.currency_id')
    company_id = fields.Many2one('res.company', related='settlement_id.company_id', store=True)

    @api.constrains('settlement_id', 'advance_id')
    def _check_duplicate_advance(self):
        """Check for duplicate advances in the same settlement"""
        for line in self:
            if line.settlement_id and line.advance_id:
                duplicate = self.search([
                    ('settlement_id', '=', line.settlement_id.id),
                    ('advance_id', '=', line.advance_id.id),
                    ('id', '!=', line.id)
                ], limit=1)
                if duplicate:
                    raise ValidationError(
                        _('Advance "%s" is already added to this settlement. '
                          'Each advance can only be added once') %
                        line.advance_id.name
                    )

    @api.constrains('settled_amount', 'advance_id')
    def _check_settled_amount(self):
        for line in self:
            if line.settled_amount <= 0:
                raise ValidationError(_('Settlement amount must be greater than zero.'))
            if line.settled_amount > line.advance_balance:
                raise ValidationError(
                    _('Settlement amount (%.2f) cannot exceed the advance balance (%.2f).') %
                    (line.settled_amount, line.advance_balance)
                )
            # For full settlement mode, settled amount must equal advance balance
            if line.settlement_mode == 'full' and line.settled_amount != line.advance_balance:
                raise ValidationError(
                    _('In Full Settlement mode, you must settle the complete advance balance (%.2f).') %
                    line.advance_balance
                )

    @api.onchange('advance_id')
    def _onchange_advance_id(self):
        """Set settled amount to remaining balance when advance is selected"""
        if self.advance_id:
            self.settled_amount = self.advance_id.balance

    @api.onchange('settlement_mode')
    def _onchange_settlement_mode(self):
        """When switching to full mode, set settled amount to full balance"""
        if self.settlement_mode == 'full' and self.advance_id:
            self.settled_amount = self.advance_id.balance
