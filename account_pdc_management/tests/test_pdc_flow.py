from odoo import Command, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class TestPdcFlow(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.company_data['company']

        cls.pdc_account = cls.env['account.account'].create({
            'name': 'Cheques Received - Post Dated',
            'code': 'PDC001',
            'account_type': 'asset_current',
            'reconcile': True,
            'company_ids': [Command.link(company.id)],
        })
        cls.bank_charge_account = cls.env['account.account'].create({
            'name': 'Bank Charges',
            'code': 'PDC002',
            'account_type': 'expense',
            'company_ids': [Command.link(company.id)],
        })
        cls.recovery_account = cls.env['account.account'].create({
            'name': 'Bank Charge Recovery',
            'code': 'PDC003',
            'account_type': 'income_other',
            'company_ids': [Command.link(company.id)],
        })

        cls.operations_journal = cls.env['account.journal'].create({
            'name': 'PDC Operations',
            'code': 'PDCOP',
            'type': 'general',
            'company_id': company.id,
        })
        cls.bank_journal = cls.company_data['default_journal_bank']
        cls.pdc_journal = cls.env['account.journal'].create({
            'name': 'Post Dated Cheques',
            'code': 'PDCJ',
            'type': 'bank',
            'company_id': company.id,
            'is_pdc': True,
            'pdc_account_id': cls.pdc_account.id,
            'pdc_bank_journal_id': cls.bank_journal.id,
        })

        company.write({
            'pdc_operations_journal_id': cls.operations_journal.id,
            'pdc_bank_charge_account_id': cls.bank_charge_account.id,
            'pdc_recovery_income_account_id': cls.recovery_account.id,
            'pdc_recovery_journal_id': cls.company_data['default_journal_sale'].id,
        })

        cls.customer = cls.partner_a

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _new_cheque(self, amount=1000.0, post=True):
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.customer.id,
            'journal_id': self.pdc_journal.id,
            'amount': amount,
            'cheque_number': '900001',
            'cheque_date': fields.Date.context_today(self.env['account.payment']),
        })
        if post:
            payment.action_post()
        return payment

    def _balance(self, account, payment=None):
        domain = [('account_id', '=', account.id), ('parent_state', '=', 'posted')]
        if payment is not None:
            moves = payment.move_id | payment._pdc_operation_moves()
            domain.append(('move_id', 'in', moves.ids))
        lines = self.env['account.move.line'].search(domain)
        return sum(lines.mapped('balance'))

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def test_posting_parks_amount_in_holding_account(self):
        """A PDC payment debits the holding account, not the bank."""
        payment = self._new_cheque(1000.0)

        self.assertTrue(payment.is_pdc)
        self.assertEqual(payment.pdc_state, 'registered')
        self.assertEqual(payment.outstanding_account_id, self.pdc_account)
        self.assertEqual(self._balance(self.pdc_account, payment), 1000.0)
        self.assertEqual(self._balance(self.bank_journal.default_account_id, payment), 0.0)

    def test_non_pdc_journal_untouched(self):
        """A payment in an ordinary journal keeps standard Odoo behaviour."""
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.customer.id,
            'journal_id': self.bank_journal.id,
            'amount': 500.0,
        })
        payment.action_post()

        self.assertFalse(payment.is_pdc)
        self.assertFalse(payment.pdc_state)
        self.assertNotEqual(payment.outstanding_account_id, self.pdc_account)

    # ------------------------------------------------------------------
    # Clearing
    # ------------------------------------------------------------------
    def test_clearing_moves_money_to_the_bank(self):
        payment = self._new_cheque(1000.0)
        payment.pdc_clear(fields.Date.context_today(payment), self.bank_journal)

        self.assertEqual(payment.pdc_state, 'cleared')
        self.assertEqual(payment.pdc_clearing_move_id.state, 'posted')
        self.assertEqual(payment.pdc_clearing_move_id.pdc_entry_type, 'clearing')
        # Holding account emptied, bank account funded.
        self.assertEqual(self._balance(self.pdc_account, payment), 0.0)
        self.assertEqual(self._balance(self.bank_journal.default_account_id, payment), 1000.0)

    def test_clearing_requires_operations_journal(self):
        self.env.company.pdc_operations_journal_id = False
        payment = self._new_cheque(1000.0)
        with self.assertRaises(UserError):
            payment.pdc_clear(fields.Date.context_today(payment), self.bank_journal)

    # ------------------------------------------------------------------
    # Bounce
    # ------------------------------------------------------------------
    def test_bounce_before_clearing_puts_balance_back_on_partner(self):
        payment = self._new_cheque(1000.0)
        receivable = payment.destination_account_id

        before = self._balance(receivable, payment)
        payment.pdc_bounce(fields.Date.context_today(payment), 'Insufficient funds')

        self.assertEqual(payment.pdc_state, 'bounced')
        self.assertEqual(payment.pdc_bounce_count, 1)
        self.assertEqual(payment.pdc_bounce_move_id.pdc_entry_type, 'bounce')
        # Holding account released, receivable back up by the cheque amount.
        self.assertEqual(self._balance(self.pdc_account, payment), 0.0)
        self.assertEqual(self._balance(receivable, payment), before + 1000.0)

    def test_bounce_after_clearing_releases_the_bank_account(self):
        payment = self._new_cheque(1000.0)
        payment.pdc_clear(fields.Date.context_today(payment), self.bank_journal)
        payment.pdc_bounce(fields.Date.context_today(payment), 'Returned by bank')

        self.assertEqual(payment.pdc_state, 'bounced')
        # The money never stayed in the bank, and never stayed in the holding account.
        self.assertEqual(self._balance(self.bank_journal.default_account_id, payment), 0.0)
        self.assertEqual(self._balance(self.pdc_account, payment), 0.0)

    def test_bounce_requires_a_bounceable_state(self):
        payment = self._new_cheque(1000.0, post=False)
        with self.assertRaises(UserError):
            payment.pdc_bounce(fields.Date.context_today(payment), 'Too early')

    # ------------------------------------------------------------------
    # Redeposit and second bounce
    # ------------------------------------------------------------------
    def test_redeposit_restores_the_holding_account(self):
        payment = self._new_cheque(1000.0)
        payment.pdc_bounce(fields.Date.context_today(payment), 'Insufficient funds')
        payment.action_pdc_redeposit()

        self.assertEqual(payment.pdc_state, 'redeposited')
        self.assertEqual(payment.pdc_redeposit_move_id.pdc_entry_type, 'redeposit')
        self.assertEqual(self._balance(self.pdc_account, payment), 1000.0)

    def test_second_bounce_nets_out_the_redeposit(self):
        payment = self._new_cheque(1000.0)
        receivable = payment.destination_account_id
        payment.pdc_bounce(fields.Date.context_today(payment), 'Insufficient funds')
        after_first_bounce = self._balance(receivable, payment)

        payment.action_pdc_redeposit()
        payment.pdc_bounce(fields.Date.context_today(payment), 'Insufficient funds again')

        self.assertEqual(payment.pdc_state, 'bounced')
        self.assertEqual(payment.pdc_bounce_count, 2)
        self.assertTrue(payment.pdc_second_bounce_move_id)
        # Redeposit and second bounce cancel out, so the ledger looks exactly as
        # it did right after the first bounce.
        self.assertEqual(self._balance(receivable, payment), after_first_bounce)
        self.assertEqual(self._balance(self.pdc_account, payment), 0.0)

    def test_cannot_redeposit_twice(self):
        payment = self._new_cheque(1000.0)
        payment.pdc_bounce(fields.Date.context_today(payment), 'Insufficient funds')
        payment.action_pdc_redeposit()
        payment.pdc_bounce(fields.Date.context_today(payment), 'Again')
        with self.assertRaises(UserError):
            payment.action_pdc_redeposit()

    # ------------------------------------------------------------------
    # Bank charge recovery
    # ------------------------------------------------------------------
    def _new_recovery(self, payment, charge=75.0):
        return self.env['pdc.bank.recovery'].create({
            'payment_id': payment.id,
            'partner_id': payment.partner_id.id,
            'charge_amount': charge,
            'bank_journal_id': self.bank_journal.id,
        })

    def _bounced_cheque(self):
        payment = self._new_cheque(1000.0)
        payment.pdc_bounce(fields.Date.context_today(payment), 'Insufficient funds')
        return payment

    def test_bank_charge_entry_books_the_fee(self):
        payment = self._bounced_cheque()
        recovery = self._new_recovery(payment, 75.0)
        recovery.action_post_charge()

        self.assertEqual(recovery.state, 'charged')
        move = recovery.charge_move_id
        self.assertEqual(move.state, 'posted')
        self.assertEqual(move.pdc_entry_type, 'bank_charge')
        charge_line = move.line_ids.filtered(lambda l: l.account_id == self.bank_charge_account)
        bank_line = move.line_ids.filtered(
            lambda l: l.account_id == self.bank_journal.default_account_id)
        self.assertEqual(charge_line.debit, 75.0)
        self.assertEqual(bank_line.credit, 75.0)

    def test_recovery_invoice_matches_the_charge(self):
        payment = self._bounced_cheque()
        recovery = self._new_recovery(payment, 75.0)
        recovery.action_post_charge()
        recovery.action_create_invoice()

        invoice = recovery.invoice_id
        self.assertEqual(recovery.state, 'invoiced')
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(invoice.amount_untaxed, 75.0)
        self.assertEqual(invoice.invoice_line_ids.account_id, self.recovery_account)

    def test_waiver_lowers_what_is_invoiced(self):
        payment = self._bounced_cheque()
        recovery = self._new_recovery(payment, 100.0)
        recovery.waiver_amount = 40.0
        recovery.action_post_charge()
        recovery.action_create_invoice()

        self.assertEqual(recovery.recovery_amount, 60.0)
        self.assertEqual(recovery.invoice_id.amount_untaxed, 60.0)
        # The bank was still charged the full fee.
        self.assertEqual(recovery.charge_move_id.amount_total, 100.0)

    def test_waiver_cannot_exceed_the_charge(self):
        payment = self._bounced_cheque()
        recovery = self._new_recovery(payment, 100.0)
        with self.assertRaises(ValidationError):
            recovery.waiver_amount = 150.0

    def test_recovery_cannot_exceed_the_charge(self):
        """The ceiling holds even when the amounts are written directly."""
        payment = self._bounced_cheque()
        recovery = self._new_recovery(payment, 100.0)
        with self.assertRaises(ValidationError):
            # A negative waiver is the only way to push the recoverable amount
            # above the charge, so that is what the guard has to catch.
            recovery.waiver_amount = -50.0

    def test_invoice_needs_the_charge_posted_first(self):
        payment = self._bounced_cheque()
        recovery = self._new_recovery(payment, 75.0)
        with self.assertRaises(UserError):
            recovery.action_create_invoice()

    def test_fully_waived_charge_raises_no_invoice(self):
        payment = self._bounced_cheque()
        recovery = self._new_recovery(payment, 100.0)
        recovery.waiver_amount = 100.0
        recovery.action_post_charge()
        recovery.action_create_invoice()

        self.assertEqual(recovery.state, 'invoiced')
        self.assertFalse(recovery.invoice_id)

    def test_recovery_only_on_bounced_cheque(self):
        payment = self._new_cheque(1000.0)
        with self.assertRaises(UserError):
            payment.action_pdc_bank_recovery()

    def test_cancel_reverses_the_bank_charge(self):
        payment = self._bounced_cheque()
        recovery = self._new_recovery(payment, 75.0)
        recovery.action_post_charge()
        recovery.action_create_invoice()
        recovery.action_cancel()

        self.assertEqual(recovery.state, 'cancel')
        self.assertEqual(recovery.invoice_id.state, 'cancel')
        # Charge and its reversal leave the expense account flat.
        self.assertEqual(self._balance(self.bank_charge_account), 0.0)

    # ------------------------------------------------------------------
    # Configuration guards
    # ------------------------------------------------------------------
    def test_pdc_journal_needs_a_holding_account(self):
        with self.assertRaises(ValidationError):
            self.env['account.journal'].create({
                'name': 'Bad PDC',
                'code': 'BADPD',
                'type': 'bank',
                'is_pdc': True,
            })

    def test_reset_to_draft_blocked_once_entries_exist(self):
        payment = self._new_cheque(1000.0)
        payment.pdc_bounce(fields.Date.context_today(payment), 'Insufficient funds')
        with self.assertRaises(UserError):
            payment.action_draft()
