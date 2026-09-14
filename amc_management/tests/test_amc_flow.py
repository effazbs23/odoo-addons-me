from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import Command, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAmcFlow(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.env.user.group_ids |= cls.env.ref('amc_management.group_amc_manager')

        def account(code, name, account_type):
            return cls.env['account.account'].create({
                'code': code, 'name': name, 'account_type': account_type,
                'company_ids': [Command.link(cls.company.id)],
            })

        cls.expense_account = account('AMC600', 'AMC Expense', 'expense')
        cls.provision_account = account('AMC210', 'AMC Provision', 'liability_current')
        cls.journal = cls.env['account.journal'].create({
            'name': 'AMC Misc', 'code': 'AMCMI', 'type': 'general',
            'company_id': cls.company.id,
        })
        cls.env['ir.config_parameter'].sudo().set_param(
            'amc_management.provision_journal_id', cls.journal.id)

        cls.categ = cls.env['product.category'].create({'name': 'AMC Services'})
        cls.categ.with_company(cls.company).property_account_expense_categ_id = cls.expense_account
        cls.categ.with_company(cls.company).amc_provision_account_id = cls.provision_account

        cls.service = cls.env['product.product'].create({
            'name': 'Lift Maintenance', 'type': 'service',
            'categ_id': cls.categ.id, 'purchase_ok': True, 'standard_price': 1200.0,
        })
        cls.goods = cls.env['product.product'].create({
            'name': 'Spare Belt', 'type': 'consu',
            'categ_id': cls.categ.id, 'purchase_ok': True,
        })
        cls.vendor = cls.env['res.partner'].create({'name': 'Acme Lifts'})
        cls.site = cls.env['amc.site'].create({
            'name': 'Head Office', 'code': 'HQ', 'company_id': cls.company.id,
        })

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _make_order(self, start=None, months=12, periods=4, price=1200.0, product=None):
        start = start or date(fields.Date.context_today(self.env.user).year, 1, 1)
        return self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'is_amc_order': True,
            'amc_site_id': self.site.id,
            'amc_start_date': start,
            'amc_duration_months': months,
            'amc_frequency_number': periods,
            'order_line': [Command.create({
                'product_id': (product or self.service).id,
                'name': 'Annual lift maintenance',
                'product_qty': 1,
                'price_unit': price,
                'tax_ids': [Command.clear()],
            })],
        })

    # ------------------------------------------------------------------
    # order level
    # ------------------------------------------------------------------

    def test_amc_order_rejects_non_service_product(self):
        """An AMC line must be a service; a storable one is refused."""
        with self.assertRaises(ValidationError):
            self._make_order(product=self.goods)

    def test_end_date_derives_from_duration(self):
        """12 months from 15 Jan runs to 14 Jan, so the span is whole months."""
        order = self._make_order(start=date(2025, 1, 15), months=12)
        self.assertEqual(order.amc_end_date, date(2026, 1, 14))

    def test_confirm_without_dates_is_refused(self):
        order = self._make_order()
        order.amc_start_date = False
        order.amc_end_date = False
        with self.assertRaises(UserError):
            order.button_confirm()

    # ------------------------------------------------------------------
    # contract generation
    # ------------------------------------------------------------------

    def test_confirm_creates_contract_and_periods(self):
        order = self._make_order(start=date(2025, 1, 1), months=12, periods=4)
        order.button_confirm()

        contracts = order.amc_mother_ids
        self.assertEqual(len(contracts), 1)
        mother = contracts
        self.assertEqual(mother.state, 'in_progress')
        self.assertEqual(mother.amc_charge_annum, 1200.0, "value is taken net of tax")
        self.assertEqual(mother.site_id, self.site)
        self.assertEqual(mother.amc_ref, '%s-1' % order.name)

        periods = mother.child_amc_ids.sorted('period_seq')
        self.assertEqual(len(periods), 4)
        # Whole months divisible by the frequency: cut on the calendar, quarter by quarter.
        self.assertEqual(periods[0].start_date, date(2025, 1, 1))
        self.assertEqual(periods[0].end_date, date(2025, 3, 31))
        self.assertEqual(periods[3].end_date, order.amc_end_date)
        # Contiguous, no gap and no overlap.
        for previous, following in zip(periods, periods[1:]):
            self.assertEqual(following.start_date, previous.end_date + relativedelta(days=1))
        self.assertEqual(sum(periods.mapped('service_days')), mother.service_days)
        self.assertEqual(periods[0].amc_ref, '%s-1-P1' % order.name)

    def test_periods_split_by_days_when_months_do_not_divide(self):
        """100 days over 3 periods: even split, remainder to the earliest periods."""
        order = self._make_order(start=date(2025, 1, 1), months=0, periods=3)
        order.amc_end_date = date(2025, 4, 10)  # 100 days inclusive
        order.button_confirm()
        periods = order.amc_mother_ids.child_amc_ids.sorted('period_seq')
        self.assertEqual(periods.mapped('service_days'), [34, 33, 33])

    def test_confirm_is_idempotent_on_relaunch(self):
        order = self._make_order()
        order.button_confirm()
        order._amc_create_contracts()
        self.assertEqual(len(order.amc_mother_ids), 1, "a second run raises no duplicate")

    # ------------------------------------------------------------------
    # signing and provisioning
    # ------------------------------------------------------------------

    def _confirm_and_sign(self, **kwargs):
        order = self._make_order(**kwargs)
        order.button_confirm()
        order.action_mark_as_signed()
        return order

    def test_mark_as_signed_generates_monthly_provisions(self):
        # Starts this month, so every month of the contract is still ahead and each one
        # gets its own regular entry. A contract already in the past folds instead, see
        # test_late_signature_folds_past_months_into_one_catchup.
        start = fields.Date.context_today(self.env.user).replace(day=1)
        order = self._confirm_and_sign(start=start, months=12, price=1200.0)
        self.assertTrue(order.amc_is_signed)

        moves = order.amc_provision_move_ids
        self.assertEqual(len(moves), 12, "one entry per calendar month spanned")
        self.assertEqual(set(moves.mapped('state')), {'draft'}, "left for accounting review")
        self.assertEqual(set(moves.mapped('amc_provision_type')), {'regular'})
        self.assertAlmostEqual(sum(moves.mapped('amc_provision_amount')), 1200.0, places=2)

        line = moves[0].line_ids
        self.assertEqual(line.filtered(lambda l: l.debit).account_id, self.expense_account)
        self.assertEqual(line.filtered(lambda l: l.credit).account_id, self.provision_account)
        self.assertEqual(set(line.mapped('amc_site_id')), {self.site})

    def test_signing_twice_is_refused(self):
        order = self._confirm_and_sign()
        with self.assertRaises(UserError):
            order.action_mark_as_signed()

    def test_provisions_are_not_duplicated(self):
        start = fields.Date.context_today(self.env.user).replace(day=1)
        order = self._confirm_and_sign(start=start, months=12)
        order._amc_generate_provision_moves()
        self.assertEqual(len(order.amc_provision_move_ids), 12)

    def test_contract_wholly_in_the_past_yields_one_catchup_entry(self):
        """Nothing is booked in a month that is already closed; it all folds forward."""
        start = fields.Date.context_today(self.env.user) - relativedelta(years=2)
        order = self._confirm_and_sign(start=start, months=12, price=1200.0)
        moves = order.amc_provision_move_ids
        self.assertEqual(len(moves), 1)
        self.assertEqual(moves.amc_provision_type, 'catchup')
        self.assertAlmostEqual(moves.amc_provision_amount, 1200.0, places=2)

    def test_late_signature_folds_past_months_into_one_catchup(self):
        """A contract that started in the past gets one catch-up entry, not many."""
        start = fields.Date.context_today(self.env.user) - relativedelta(months=3)
        order = self._confirm_and_sign(start=start, months=12)
        moves = order.amc_provision_move_ids
        catchup = moves.filtered(lambda m: m.amc_provision_type == 'catchup')
        self.assertEqual(len(catchup), 1)
        current_month = fields.Date.context_today(self.env.user).replace(day=1)
        self.assertEqual(catchup.amc_provision_month, current_month)
        self.assertFalse(moves.filtered(lambda m: m.amc_provision_month < current_month))

    def test_missing_provision_account_is_reported(self):
        self.categ.with_company(self.company).amc_provision_account_id = False
        order = self._make_order()
        order.button_confirm()
        with self.assertRaises(UserError):
            order.action_mark_as_signed()

    # ------------------------------------------------------------------
    # service period closure
    # ------------------------------------------------------------------

    def _period(self, order):
        return order.amc_mother_ids.child_amc_ids.sorted('period_seq')[0]

    def test_mark_done_closes_period_without_reversal(self):
        order = self._confirm_and_sign(start=date(2025, 1, 1), months=12, periods=4)
        period = self._period(order)
        before = len(order.amc_provision_move_ids)
        self.env['amc.mark.done.wizard'].create({
            'service_period_id': period.id,
            'service_report': b'UkVQT1JU',
            'service_report_filename': 'report.pdf',
        }).action_confirm()
        self.assertEqual(period.state, 'closed')
        self.assertEqual(period.days_serviced, period.service_days)
        self.assertEqual(period.days_not_serviced, 0)
        self.assertEqual(len(order.amc_provision_move_ids), before, "nothing reversed")

    def test_expire_period_reverses_the_whole_period(self):
        order = self._confirm_and_sign(start=date(2025, 1, 1), months=12, periods=4, price=1200.0)
        period = self._period(order)
        self.env['amc.expire.period.wizard'].create({
            'service_period_id': period.id,
            'reason': 'Vendor never turned up',
        }).action_confirm()

        self.assertEqual(period.state, 'expired')
        self.assertEqual(period.days_not_serviced, period.service_days)
        reversal = period.provision_move_ids
        self.assertEqual(len(reversal), 1)
        self.assertEqual(reversal.amc_provision_type, 'reversal')
        self.assertEqual(reversal.state, 'draft')
        # A reversal flips the pair: provision debited, expense credited.
        self.assertEqual(reversal.line_ids.filtered(lambda l: l.debit).account_id,
                         self.provision_account)
        expected = period.service_days * (1200.0 / 365)
        self.assertAlmostEqual(reversal.amc_provision_amount, expected, places=2)

    def test_partial_service_reverses_only_missing_days(self):
        order = self._confirm_and_sign(start=date(2025, 1, 1), months=12, periods=4, price=1200.0)
        period = self._period(order)
        self.env['amc.partial.service.wizard'].create({
            'service_period_id': period.id,
            'days_serviced': 60,
            'service_report': b'UkVQT1JU',
            'service_report_filename': 'report.pdf',
        }).action_confirm()

        self.assertEqual(period.state, 'partially_serviced')
        self.assertEqual(period.days_not_serviced, period.service_days - 60)
        reversal = period.provision_move_ids
        self.assertAlmostEqual(reversal.amc_provision_amount,
                               period.days_not_serviced * (1200.0 / 365), places=2)

    def test_partial_service_rejects_full_or_empty_service(self):
        order = self._confirm_and_sign(periods=4)
        period = self._period(order)
        with self.assertRaises(ValidationError):
            self.env['amc.partial.service.wizard'].create({
                'service_period_id': period.id,
                'days_serviced': period.service_days,
                'service_report': b'UkVQT1JU',
            })

    def test_terminal_period_cannot_be_closed_again(self):
        order = self._confirm_and_sign(periods=4)
        period = self._period(order)
        self.env['amc.expire.period.wizard'].create({
            'service_period_id': period.id, 'reason': 'gone',
        }).action_confirm()
        with self.assertRaises(UserError):
            period.action_mark_done()

    def test_mother_closes_once_every_period_is_settled(self):
        order = self._confirm_and_sign(start=date(2025, 1, 1), months=12, periods=2)
        mother = order.amc_mother_ids
        for period in mother.child_amc_ids:
            self.env['amc.mark.done.wizard'].create({
                'service_period_id': period.id,
                'service_report': b'UkVQT1JU',
                'service_report_filename': 'r.pdf',
            }).action_confirm()
        self.assertEqual(mother.cnt_validated_periods, 2)
        self.assertEqual(mother.state, 'closed')

    # ------------------------------------------------------------------
    # vendor billing
    # ------------------------------------------------------------------

    def _bill_wizard(self, mother, milestone, amount=300.0):
        return self.env['amc.vendor.bill.wizard'].with_context(
            default_amc_id=mother.id).create({
                'amc_id': mother.id,
                'milestone_number': milestone,
                'bill_amount': amount,
                'invoice_date': fields.Date.context_today(self.env.user),
            })

    def test_milestone_bill_posts_against_the_provision_account(self):
        order = self._confirm_and_sign(periods=4, price=1200.0)
        mother = order.amc_mother_ids
        self._bill_wizard(mother, 1).action_create_bill()

        bill = mother.bill_ids
        self.assertEqual(len(bill), 1)
        self.assertEqual(bill.move_type, 'in_invoice')
        self.assertEqual(bill.amc_milestone_label, 'Q1')
        self.assertEqual(bill.invoice_line_ids.account_id, self.provision_account)
        self.assertEqual(bill.invoice_date_due, bill.date)

    def test_milestone_cannot_be_skipped(self):
        order = self._confirm_and_sign(periods=4)
        with self.assertRaises(UserError):
            self._bill_wizard(order.amc_mother_ids, 2).action_create_bill()

    def test_milestone_cannot_be_billed_twice(self):
        order = self._confirm_and_sign(periods=4)
        mother = order.amc_mother_ids
        self._bill_wizard(mother, 1).action_create_bill()
        with self.assertRaises(UserError):
            self._bill_wizard(mother, 1).action_create_bill()

    def test_next_milestone_waits_for_the_previous_to_leave_draft(self):
        order = self._confirm_and_sign(periods=4)
        mother = order.amc_mother_ids
        self._bill_wizard(mother, 1).action_create_bill()
        with self.assertRaises(UserError):
            self._bill_wizard(mother, 2).action_create_bill()
        mother.bill_ids.action_post()
        self._bill_wizard(mother, 2).action_create_bill()
        self.assertEqual(len(mother.bill_ids), 2)

    def test_bill_is_refused_before_signing(self):
        order = self._make_order()
        order.button_confirm()
        with self.assertRaises(UserError):
            order.amc_mother_ids.action_create_vendor_bill()

    def test_bill_cannot_be_raised_from_a_service_period(self):
        order = self._confirm_and_sign(periods=4)
        with self.assertRaises(UserError):
            self._period(order).action_create_vendor_bill()

    # ------------------------------------------------------------------
    # order lifecycle guards
    # ------------------------------------------------------------------

    def test_signed_order_cannot_be_cancelled(self):
        order = self._confirm_and_sign()
        with self.assertRaises(UserError):
            order.button_cancel()

    def test_cancelling_an_unsigned_order_terminates_its_contracts(self):
        order = self._make_order()
        order.button_confirm()
        order.button_cancel()
        self.assertEqual(order.amc_mother_ids.state, 'terminated')
        self.assertEqual(set(order.amc_mother_ids.child_amc_ids.mapped('state')), {'terminated'})

    # ------------------------------------------------------------------
    # crons and reporting
    # ------------------------------------------------------------------

    def test_cron_moves_finished_periods_to_validation_pending(self):
        start = fields.Date.context_today(self.env.user) - relativedelta(years=1)
        order = self._confirm_and_sign(start=start, months=12, periods=4)
        self.env['amc.contract']._cron_update_service_periods()
        states = set(order.amc_mother_ids.child_amc_ids.mapped('state'))
        self.assertEqual(states, {'validation_pending'})

    def test_schedule_report_renders_a_workbook(self):
        order = self._confirm_and_sign(start=date(2025, 1, 1), months=12)
        wizard = self.env['amc.schedule.report.wizard'].create({
            'year': '2025', 'site_ids': [Command.set(self.site.ids)],
        })
        action = wizard.action_generate_report()
        self.assertEqual(action['type'], 'ir.actions.report',
                         "config=False keeps the layout configurator out of the way")
        self.assertEqual(action['report_type'], 'xlsx')
        content, extension = self.env['ir.actions.report']._render_xlsx(
            'amc_management.report_amc_schedule', [], data=action['data'])
        self.assertEqual(extension, 'xlsx')
        self.assertTrue(content.startswith(b'PK'), "an xlsx file is a zip archive")
        self.assertTrue(order.amc_mother_ids.amc_ref)
