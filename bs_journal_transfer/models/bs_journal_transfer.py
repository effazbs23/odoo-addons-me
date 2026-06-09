# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BsJournalTransfer(models.Model):
    _name = 'bs.journal.transfer'
    _description = 'Journal Transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True
    )
    source_journal_id = fields.Many2one(
        'account.journal',
        string='Source Journal',
        required=True,
        tracking=True,
        domain=[('type', 'in', ['bank', 'cash'])],
        help='Journal from which the amount is being transferred'
    )
    destination_journal_id = fields.Many2one(
        'account.journal',
        string='Destination Journal',
        required=True,
        tracking=True,
        domain=[('type', 'in', ['bank', 'cash'])],
        help='Journal to which the amount is being transferred'
    )
    amount = fields.Monetary(
        string='Amount',
        required=True,
        currency_field='currency_id',
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    date = fields.Date(
        string='Transfer Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )
    deposit_slip = fields.Binary(
        string='Deposit Slip',
        attachment=True,
        help='Upload deposit slip or proof of transaction'
    )
    deposit_slip_filename = fields.Char(string='Filename')
    notes = fields.Text(string='Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    submitted_by = fields.Many2one(
        'res.users',
        string='Submitted By',
        default=lambda self: self.env.user,
    )

    statement_line_ids = fields.Many2many(
        'account.bank.statement.line',
        'bs_journal_transfer_statement_line_rel',
        'transfer_id',
        'statement_line_id',
        string='Bank Statement Lines',
        readonly=True,
        help='Automatically created bank statement lines for this transfer'
    )
    statement_count = fields.Integer(
        string='Statement Lines',
        compute='_compute_statement_count'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('bs.journal.transfer') or _('New')
        return super().create(vals_list)

    @api.onchange('source_journal_id', 'destination_journal_id')
    def _onchange_journals_not_same(self):
        for record in self:
            if record.source_journal_id and record.destination_journal_id and record.source_journal_id == record.destination_journal_id:
                record.destination_journal_id = False
                raise ValidationError(_('Source Journal and Destination Journal cannot be the same.'))

    @api.onchange('source_journal_id', 'amount')
    def _onchange_source_journal_balance(self):
        for record in self:
            record._check_source_journal_running_balance()

    @api.constrains('source_journal_id', 'destination_journal_id')
    def _check_journals_not_same(self):
        for record in self:
            if record.source_journal_id and record.destination_journal_id:
                if record.source_journal_id.id == record.destination_journal_id.id:
                    raise ValidationError(_('Source Journal and Destination Journal cannot be the same.'))

    @api.constrains('amount')
    def _check_amount_positive(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(_('Amount must be greater than zero.'))

    def _get_source_journal_running_balance(self):
        self.ensure_one()
        if not self.source_journal_id:
            return 0.0

        latest_statement_line = self.env['account.bank.statement.line'].search([
            ('journal_id', '=', self.source_journal_id.id),
            ('company_id', '=', self.company_id.id),
            ('move_id.state', '=', 'posted'),
        ], order='internal_index desc, id desc', limit=1)
        return latest_statement_line.running_balance if latest_statement_line else 0.0

    def _check_source_journal_running_balance(self):
        for record in self:
            if not record.source_journal_id or record.amount <= 0:
                continue

            running_balance = record._get_source_journal_running_balance()
            if record.amount > running_balance:
                raise ValidationError(_(
                    'Transfer amount cannot exceed the source journal running balance. '\
                    'Available balance: %s, Transfer amount: %s.'
                ) % (
                    record.currency_id.symbol and f"{record.currency_id.symbol} {running_balance}" or running_balance,
                    record.currency_id.symbol and f"{record.currency_id.symbol} {record.amount}" or record.amount,
                ))

    @api.depends('statement_line_ids')
    def _compute_statement_count(self):
        for record in self:
            record.statement_count = len(record.statement_line_ids)

    def action_confirm(self):
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError(_('Only draft transfers can be confirmed.'))

        self._create_bank_statement_lines()

        self.write({'state': 'confirmed'})
        self.message_post(body=_('Journal transfer confirmed and bank statement lines created.'))
        return True

    def action_draft(self):
        self.ensure_one()
        if self.state != 'confirmed':
            raise ValidationError(_('Only confirmed transfers can be reset to draft.'))

        if self.statement_line_ids:
            if any(line.is_reconciled for line in self.statement_line_ids):
                raise ValidationError(_(
                    'Cannot reset to draft because some bank statement lines are already reconciled. '
                    'Please unreconcile them first.'
                ))
            self.statement_line_ids.unlink()

        self.write({'state': 'draft'})
        self.message_post(body=_('Journal transfer reset to draft and bank statement lines deleted.'))
        return True

    def action_cancel(self):
        self.ensure_one()
        if self.statement_line_ids and any(line.is_reconciled for line in self.statement_line_ids):
            raise ValidationError(_(
                'Cannot cancel because some bank statement lines are already reconciled. '
                'Please unreconcile them first.'
            ))

        self.write({'state': 'cancelled'})
        self.message_post(body=_('Journal transfer cancelled.'))
        return True

    def action_view_statement_lines(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bank Statement Lines'),
            'res_model': 'account.bank.statement.line',
            'view_mode': 'kanban,list',
            'domain': [('id', 'in', self.statement_line_ids.ids)],
            'context': {'create': False},
        }

    def _create_bank_statement_lines(self):
        self.ensure_one()

        if self.statement_line_ids:
            raise ValidationError(_('Bank statement lines already exist for this transfer.'))

        StatementLine = self.env['account.bank.statement.line'].sudo()

        payment_ref = _('Internal Transfer - %s', self.name)

        withdrawal_vals = {
            'journal_id': self.source_journal_id.id,
            'date': self.date,
            'payment_ref': payment_ref + _(' (Out)'),
            'amount': -abs(self.amount),
            'company_id': self.company_id.id,
        }
        withdrawal_line = StatementLine.create(withdrawal_vals)

        deposit_vals = {
            'journal_id': self.destination_journal_id.id,
            'date': self.date,
            'payment_ref': payment_ref + _(' (In)'),
            'amount': abs(self.amount),
            'company_id': self.company_id.id,
        }
        deposit_line = StatementLine.create(deposit_vals)

        self.statement_line_ids = [(6, 0, [withdrawal_line.id, deposit_line.id])]

        note = _('Created from Journal Transfer: %s', self.name)
        if self.notes:
            note += '\n' + self.notes

        withdrawal_line.move_id.message_post(body=note)
        deposit_line.move_id.message_post(body=note)

        self._auto_reconcile_statement_lines(withdrawal_line, deposit_line)

        return withdrawal_line, deposit_line

    def _auto_reconcile_statement_lines(self, withdrawal_line, deposit_line):
        ReconcileModel = self.env['account.reconcile.model'].sudo()

        internal_transfer_models = ReconcileModel.search([
            ('name', 'ilike', 'Internal Transfer'),
            ('company_id', '=', self.company_id.id),
            ('active', '=', True),
        ], limit=1)

        if not internal_transfer_models:
            self.message_post(
                body=_('Warning: No "Internal Transfers" reconciliation model found. '
                       'Bank statement lines created but not automatically reconciled. '
                       'Please reconcile manually or create the reconciliation model.'),
                message_type='comment'
            )
            return

        reco_model = internal_transfer_models[0]

        try:
            reco_model.trigger_reconciliation_model(withdrawal_line.id)
            self.message_post(
                body=_('Internal Transfers model applied to withdrawal line: %s', withdrawal_line.payment_ref)
            )
        except Exception as e:
            self.message_post(
                body=_('Failed to auto-reconcile withdrawal line: %s', str(e)),
                message_type='comment'
            )

        try:
            reco_model.trigger_reconciliation_model(deposit_line.id)
            self.message_post(
                body=_('Internal Transfers model applied to deposit line: %s', deposit_line.payment_ref)
            )
        except Exception as e:
            self.message_post(
                body=_('Failed to auto-reconcile deposit line: %s', str(e)),
                message_type='comment'
            )
