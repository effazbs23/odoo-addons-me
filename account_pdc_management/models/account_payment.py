from dateutil.relativedelta import relativedelta

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    """A payment made by cheque that is not honoured yet.

    The whole PDC flow hangs off a plain ``account.payment``. Posting one in a
    journal flagged ``is_pdc`` parks the amount in the journal's PDC holding
    account instead of the bank, and every later step -- clearing, bouncing,
    redepositing -- is an ordinary posted journal entry against that account, so
    the general ledger and the partner ledger stay correct throughout.
    """
    _inherit = 'account.payment'

    is_pdc = fields.Boolean(
        related='journal_id.is_pdc', string='Is Post Dated Cheque', store=True, readonly=True,
    )
    pdc_state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('registered', 'Registered'),
            ('cleared', 'Cleared'),
            ('bounced', 'Bounced'),
            ('redeposited', 'Redeposited'),
            ('cancelled', 'Cancelled'),
        ],
        # No default: an ordinary payment carries no cheque status at all, so the
        # column stays empty for it instead of claiming every payment is a draft
        # cheque. It is stamped on creation when the journal is a PDC journal.
        string='Cheque Status', copy=False, tracking=True, index='btree_not_null',
        help="Registered: the cheque is held in the PDC account.\n"
             "Cleared: the bank honoured it and the money reached the bank account.\n"
             "Bounced: the bank returned it and the balance is back on the partner.\n"
             "Redeposited: a bounced cheque was presented to the bank again.",
    )

    # -- cheque identification ------------------------------------------------
    cheque_number = fields.Char(string='Cheque Number', copy=False, tracking=True, index='btree_not_null')
    cheque_date = fields.Date(
        string='Cheque Date', copy=False, tracking=True,
        help="Date written on the cheque, i.e. the day it can be presented to the bank.",
    )
    cheque_bank_id = fields.Many2one('res.bank', string='Drawee Bank', copy=False, tracking=True)

    # -- clearing -------------------------------------------------------------
    pdc_bank_journal_id = fields.Many2one(
        'account.journal', string='Deposit Bank', copy=False, check_company=True,
        domain="[('type', '=', 'bank'), ('is_pdc', '=', False)]",
    )
    pdc_cleared_date = fields.Date(string='Cleared On', copy=False, readonly=True, tracking=True)
    pdc_clearing_move_id = fields.Many2one(
        'account.move', string='Clearing Entry', copy=False, readonly=True,
    )

    # -- bounce ---------------------------------------------------------------
    pdc_bounce_date = fields.Date(string='Bounce Date', copy=False, readonly=True, tracking=True)
    pdc_bounce_reason = fields.Text(string='Bounce Reason', copy=False, readonly=True)
    pdc_bounce_move_id = fields.Many2one(
        'account.move', string='Bounce Entry', copy=False, readonly=True,
    )
    pdc_redeposit_move_id = fields.Many2one(
        'account.move', string='Redeposit Entry', copy=False, readonly=True,
    )
    pdc_second_bounce_date = fields.Date(string='2nd Bounce Date', copy=False, readonly=True)
    pdc_second_bounce_reason = fields.Text(string='2nd Bounce Reason', copy=False, readonly=True)
    pdc_second_bounce_move_id = fields.Many2one(
        'account.move', string='2nd Bounce Entry', copy=False, readonly=True,
    )
    pdc_bounce_count = fields.Integer(
        string='Times Bounced', default=0, copy=False, readonly=True, tracking=True,
    )

    # -- bank charge recovery -------------------------------------------------
    bank_recovery_ids = fields.One2many(
        'pdc.bank.recovery', 'payment_id', string='Bank Recoveries', copy=False,
    )
    bank_recovery_count = fields.Integer(
        string='Bank Recovery Count', compute='_compute_bank_recovery_count',
    )

    pdc_entry_count = fields.Integer(string='PDC Entries', compute='_compute_pdc_entry_count')

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends('journal_id.is_pdc', 'journal_id.pdc_account_id', 'payment_method_line_id')
    def _compute_outstanding_account_id(self):
        """Park PDC payments in the journal's holding account.

        Standard Odoo takes the outstanding receipts / payments account from the
        payment method line. For a PDC journal the money is not with the bank
        yet, so the holding account configured on the journal wins instead --
        which also means a PDC journal works without anyone having to edit its
        payment method lines by hand.
        """
        super()._compute_outstanding_account_id()
        for payment in self:
            journal = payment.journal_id
            if journal.is_pdc and journal.pdc_account_id:
                payment.outstanding_account_id = journal.pdc_account_id

    @api.depends('bank_recovery_ids')
    def _compute_bank_recovery_count(self):
        counts = dict(self.env['pdc.bank.recovery']._read_group(
            [('payment_id', 'in', self.ids)], ['payment_id'], ['__count'],
        ))
        for payment in self:
            payment.bank_recovery_count = counts.get(payment, 0)

    @api.depends('pdc_clearing_move_id', 'pdc_bounce_move_id', 'pdc_redeposit_move_id',
                 'pdc_second_bounce_move_id', 'bank_recovery_ids.charge_move_id',
                 'bank_recovery_ids.invoice_id')
    def _compute_pdc_entry_count(self):
        for payment in self:
            payment.pdc_entry_count = len(payment._pdc_operation_moves())

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _pdc_operation_moves(self):
        """Every entry this module posted for the cheque, newest logic first."""
        self.ensure_one()
        moves = (
            self.pdc_clearing_move_id
            | self.pdc_bounce_move_id
            | self.pdc_redeposit_move_id
            | self.pdc_second_bounce_move_id
            | self.bank_recovery_ids.charge_move_id
            | self.bank_recovery_ids.invoice_id
        )
        return moves

    def _pdc_check_is_pdc(self):
        for payment in self:
            if not payment.is_pdc:
                raise UserError(_(
                    "Payment %s was not made in a Post Dated Cheque journal.",
                    payment.display_name))

    def _pdc_operations_journal(self):
        """Miscellaneous journal the clearing / bounce entries are posted in."""
        self.ensure_one()
        journal = self.company_id.pdc_operations_journal_id
        if not journal:
            raise UserError(_(
                "Set a PDC Operations Journal under Accounting > Configuration > Settings > "
                "Post Dated Cheques before clearing or bouncing a cheque."))
        return journal

    def _pdc_holding_account(self):
        self.ensure_one()
        account = self.journal_id.pdc_account_id
        if not account:
            raise UserError(_(
                "Journal %s has no PDC holding account configured.", self.journal_id.display_name))
        return account

    def _pdc_bank_account(self, bank_journal):
        self.ensure_one()
        account = bank_journal.default_account_id
        if not account:
            raise UserError(_(
                "Bank journal %s has no default account configured.", bank_journal.display_name))
        return account

    def _pdc_partner_account(self):
        """Receivable / payable account the cheque settles."""
        self.ensure_one()
        account = self.destination_account_id
        if not account:
            raise UserError(_(
                "Payment %s has no destination account, so the entry cannot be built.",
                self.display_name))
        return account

    def _pdc_prepare_move(self, journal, date, ref, debit_account, credit_account,
                          entry_type, partner=None):
        """One balanced two line entry for ``self.amount`` in company currency."""
        self.ensure_one()
        partner = partner if partner is not None else self.partner_id
        label = ref
        return {
            'move_type': 'entry',
            'journal_id': journal.id,
            'date': date,
            'ref': ref,
            'company_id': self.company_id.id,
            'pdc_payment_id': self.id,
            'pdc_entry_type': entry_type,
            'line_ids': [
                Command.create({
                    'name': label,
                    'account_id': debit_account.id,
                    'partner_id': partner.id if partner else False,
                    'debit': self.amount,
                    'credit': 0.0,
                }),
                Command.create({
                    'name': label,
                    'account_id': credit_account.id,
                    'partner_id': partner.id if partner else False,
                    'debit': 0.0,
                    'credit': self.amount,
                }),
            ],
        }

    def _pdc_post_move(self, vals):
        move = self.env['account.move'].create(vals)
        move.action_post()
        return move

    @staticmethod
    def _pdc_sides(is_inbound, held_account, partner_account):
        """(debit, credit) accounts putting the balance back on the partner.

        Money came in on a customer cheque: the holding account was debited, so
        undoing it credits the holding account and debits the receivable. An
        outgoing cheque is the mirror image.
        """
        if is_inbound:
            return partner_account, held_account
        return held_account, partner_account

    def _pdc_reconcile_pair(self, first_lines, second_lines):
        """Reconcile two sets of lines on the same account, when it allows it.

        Keeps the holding account clean per cheque. Purely cosmetic for the
        ledger totals, so a non reconcilable account is not an error.
        """
        lines = first_lines | second_lines
        if not lines or not all(line.account_id.reconcile for line in lines):
            return
        try:
            lines.reconcile()
        except UserError:
            # Partially reconciled already, or a currency mismatch: the balances
            # are still right, only the matching number is missing.
            pass

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        payments = super().create(vals_list)
        payments.filtered(
            lambda payment: payment.is_pdc and not payment.pdc_state
        ).pdc_state = 'draft'
        return payments

    def action_post(self):
        res = super().action_post()
        pdc_payments = self.filtered(
            lambda payment: payment.is_pdc and payment.pdc_state in (False, 'draft'))
        pdc_payments.write({'pdc_state': 'registered'})
        return res

    def action_cancel(self):
        res = super().action_cancel()
        self.filtered('is_pdc').write({'pdc_state': 'cancelled'})
        return res

    def action_draft(self):
        for payment in self.filtered('is_pdc'):
            if payment._pdc_operation_moves().filtered(lambda move: move.state == 'posted'):
                raise UserError(_(
                    "Cheque %s already has posted PDC entries. Cancel those entries before "
                    "resetting the payment to draft.", payment.display_name))
        res = super().action_draft()
        self.filtered('is_pdc').write({'pdc_state': 'draft'})
        return res

    # ------------------------------------------------------------------
    # Clearing
    # ------------------------------------------------------------------
    def action_pdc_clear(self):
        """Open the wizard asking which bank the cheque was deposited into."""
        self.ensure_one()
        self._pdc_check_is_pdc()
        if self.pdc_state not in ('registered', 'redeposited'):
            raise UserError(_("Only a registered or redeposited cheque can be cleared."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Clear Cheque'),
            'res_model': 'pdc.clear.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_payment_id': self.id},
        }

    def pdc_clear(self, clearing_date, bank_journal):
        """Move the cheque value from the holding account into the bank."""
        self.ensure_one()
        self._pdc_check_is_pdc()
        if self.pdc_state not in ('registered', 'redeposited'):
            raise UserError(_("Only a registered or redeposited cheque can be cleared."))

        holding = self._pdc_holding_account()
        bank_account = self._pdc_bank_account(bank_journal)
        debit, credit = (bank_account, holding) if self.payment_type == 'inbound' \
            else (holding, bank_account)
        ref = _("Cheque cleared - %s", self._pdc_label())
        move = self._pdc_post_move(self._pdc_prepare_move(
            self._pdc_operations_journal(), clearing_date, ref, debit, credit, 'clearing'))

        self.write({
            'pdc_state': 'cleared',
            'pdc_cleared_date': clearing_date,
            'pdc_bank_journal_id': bank_journal.id,
            'pdc_clearing_move_id': move.id,
        })
        self._pdc_reconcile_pair(
            self.move_id.line_ids.filtered(lambda line: line.account_id == holding),
            move.line_ids.filtered(lambda line: line.account_id == holding))
        self.message_post(body=_("Cheque cleared into %(bank)s, entry %(move)s.",
                                 bank=bank_journal.display_name, move=move.name))
        return move

    # ------------------------------------------------------------------
    # Bounce / redeposit
    # ------------------------------------------------------------------
    def action_pdc_bounce(self):
        """Open the wizard capturing the return reason and the bank advice."""
        self.ensure_one()
        self._pdc_check_is_pdc()
        if self.pdc_state not in ('registered', 'cleared', 'redeposited'):
            raise UserError(_("Only a registered, cleared or redeposited cheque can bounce."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bounce Cheque'),
            'res_model': 'pdc.bounce.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_payment_id': self.id},
        }

    def pdc_bounce(self, bounce_date, reason, attachment=None):
        """Put the cheque value back on the partner.

        The account released is whichever one is holding the money at that
        moment: the PDC account while the cheque is merely registered, the bank
        account once it has been cleared. A cheque that bounces after a
        redeposit reverses the redeposit entry instead, so the pair nets out and
        the ledger does not show the same cheque twice.
        """
        self.ensure_one()
        self._pdc_check_is_pdc()
        if self.pdc_state not in ('registered', 'cleared', 'redeposited'):
            raise UserError(_("Only a registered, cleared or redeposited cheque can bounce."))

        second_bounce = self.pdc_state == 'redeposited'
        journal = self._pdc_operations_journal()
        ref = _("Cheque bounced - %s", self._pdc_label())

        if second_bounce:
            # Mirror the redeposit rather than build a fresh entry, so redeposit
            # and second bounce cancel each other exactly.
            move = self.pdc_redeposit_move_id._reverse_moves([{
                'date': bounce_date,
                'ref': ref,
                'journal_id': journal.id,
                'pdc_payment_id': self.id,
                'pdc_entry_type': 'bounce',
            }])
            move.action_post()
        else:
            holding = self._pdc_holding_account()
            released = holding
            if self.pdc_state == 'cleared':
                released = self._pdc_bank_account(self.pdc_bank_journal_id)
            debit, credit = self._pdc_sides(
                self.payment_type == 'inbound', released, self._pdc_partner_account())
            move = self._pdc_post_move(self._pdc_prepare_move(
                journal, bounce_date, ref, debit, credit, 'bounce'))
            if released == holding:
                self._pdc_reconcile_pair(
                    self.move_id.line_ids.filtered(lambda line: line.account_id == holding),
                    move.line_ids.filtered(lambda line: line.account_id == holding))

        values = {
            'pdc_state': 'bounced',
            'pdc_bounce_count': self.pdc_bounce_count + 1,
        }
        if second_bounce:
            values.update({
                'pdc_second_bounce_date': bounce_date,
                'pdc_second_bounce_reason': reason,
                'pdc_second_bounce_move_id': move.id,
            })
        else:
            values.update({
                'pdc_bounce_date': bounce_date,
                'pdc_bounce_reason': reason,
                'pdc_bounce_move_id': move.id,
            })
        self.write(values)

        self.message_post(
            body=_("Cheque bounced on %(date)s. Reason: %(reason)s<br/>Entry: %(move)s",
                   date=bounce_date, reason=reason, move=move.name),
            attachment_ids=attachment.ids if attachment else None,
        )
        return move

    def action_pdc_redeposit(self):
        """Present a bounced cheque to the bank again.

        Reverses the bounce entry, which puts the value back into the account it
        was released from and takes it off the partner again.
        """
        self.ensure_one()
        self._pdc_check_is_pdc()
        if self.pdc_state != 'bounced':
            raise UserError(_("Only a bounced cheque can be redeposited."))
        if self.pdc_second_bounce_move_id:
            raise UserError(_(
                "Cheque %s has already bounced twice. Recover it through a bank recovery "
                "instead of redepositing it again.", self.display_name))

        bounce_move = self.pdc_bounce_move_id
        if not bounce_move or bounce_move.state != 'posted':
            raise UserError(_("The bounce entry has to be posted before the cheque can be "
                              "redeposited."))

        move = bounce_move._reverse_moves([{
            'date': fields.Date.context_today(self),
            'ref': _("Cheque redeposited - %s", self._pdc_label()),
            'journal_id': bounce_move.journal_id.id,
            'pdc_payment_id': self.id,
            'pdc_entry_type': 'redeposit',
        }])
        move.action_post()
        self.write({'pdc_state': 'redeposited', 'pdc_redeposit_move_id': move.id})
        self.message_post(body=_("Cheque redeposited, entry %s.", move.name))
        return self._pdc_action_open_move(move, _('Redeposit Entry'))

    def _pdc_label(self):
        self.ensure_one()
        return _("cheque %(number)s (%(payment)s)",
                 number=self.cheque_number or _('n/a'), payment=self.name or self.display_name)

    # ------------------------------------------------------------------
    # Bank charge recovery
    # ------------------------------------------------------------------
    def action_pdc_bank_recovery(self):
        """Record what the bank charged for the returned cheque."""
        self.ensure_one()
        self._pdc_check_is_pdc()
        if self.pdc_state != 'bounced':
            raise UserError(_("A bank charge can only be recovered on a bounced cheque."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bank Charge Recovery'),
            'res_model': 'pdc.bank.recovery',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_payment_id': self.id,
                'default_partner_id': self.partner_id.id,
            },
        }

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def _pdc_action_open_move(self, move, name):
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': 'account.move',
            'res_id': move.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_pdc_entries(self):
        self.ensure_one()
        moves = self._pdc_operation_moves()
        action = {
            'type': 'ir.actions.act_window',
            'name': _('PDC Entries'),
            'res_model': 'account.move',
            'domain': [('id', 'in', moves.ids)],
            'view_mode': 'list,form',
            'context': {'create': False},
        }
        if len(moves) == 1:
            action.update({'view_mode': 'form', 'res_id': moves.id})
        return action

    # ------------------------------------------------------------------
    # Demo
    # ------------------------------------------------------------------
    @api.model
    def _pdc_demo_setup(self):
        """Walk the demo cheques through the flow. Called from demo data only.

        Written in Python rather than as XML records so the dates are relative to
        the day the database is created, and so the entries are produced by the
        same code a user would trigger from the interface.
        """
        def _ref(xmlid):
            return self.env.ref('account_pdc_management.%s' % xmlid, raise_if_not_found=False)

        company = self.env.ref('base.main_company')
        operations_journal = _ref('demo_journal_pdc_operations')
        bank_journal = self.env['account.journal'].search([
            ('type', '=', 'bank'), ('is_pdc', '=', False), ('company_id', '=', company.id),
        ], limit=1)
        sale_journal = self.env['account.journal'].search([
            ('type', '=', 'sale'), ('company_id', '=', company.id),
        ], limit=1)
        company.write({
            'pdc_operations_journal_id': operations_journal.id,
            'pdc_bank_charge_account_id': _ref('demo_account_bank_charge').id,
            'pdc_recovery_income_account_id': _ref('demo_account_charge_recovery').id,
            'pdc_recovery_journal_id': sale_journal.id,
        })
        if bank_journal:
            _ref('demo_journal_pdc').pdc_bank_journal_id = bank_journal.id

        today = fields.Date.context_today(self)
        payments = {
            name: _ref('demo_pdc_payment_%s' % name)
            for name in ('registered', 'cleared', 'bounced', 'redeposited')
        }
        if not all(payments.values()):
            return False

        offsets = {'registered': 25, 'cleared': -12, 'bounced': -20, 'redeposited': -30}
        for name, payment in payments.items():
            payment.write({
                'date': today + relativedelta(days=min(0, offsets[name])),
                'cheque_date': today + relativedelta(days=offsets[name]),
            })
            payment.action_post()

        if bank_journal:
            payments['cleared'].pdc_clear(today + relativedelta(days=-10), bank_journal)

        payments['bounced'].pdc_bounce(
            today + relativedelta(days=-15), 'Insufficient funds')
        recovery = self.env['pdc.bank.recovery'].create({
            'payment_id': payments['bounced'].id,
            'partner_id': payments['bounced'].partner_id.id,
            'charge_amount': 50.0,
            'charge_date': today + relativedelta(days=-15),
            'bank_journal_id': bank_journal.id,
            'charge_reason': 'Returned cheque handling fee',
        }) if bank_journal else self.env['pdc.bank.recovery']
        if recovery:
            recovery.action_post_charge()
            recovery.action_create_invoice()

        payments['redeposited'].pdc_bounce(
            today + relativedelta(days=-25), 'Signature mismatch')
        payments['redeposited'].action_pdc_redeposit()
        return True

    def action_view_bank_recoveries(self):
        self.ensure_one()
        recoveries = self.bank_recovery_ids
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Bank Recoveries'),
            'res_model': 'pdc.bank.recovery',
            'domain': [('payment_id', '=', self.id)],
            'view_mode': 'list,form',
            'context': {'default_payment_id': self.id},
        }
        if len(recoveries) == 1:
            action.update({'view_mode': 'form', 'res_id': recoveries.id})
        return action
