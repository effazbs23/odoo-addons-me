from datetime import datetime, timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class CommonApprovalReminderCase(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(
            cls.env.context,
            mail_create_nolog=True,
            mail_create_nosubscribe=True,
            mail_notrack=True,
            tracking_disable=True,
        ))
        cls.manager_user = new_test_user(
            cls.env, login='bs_mgr',
            groups='base.group_user,'
                   'purchase.group_purchase_user,'
                   'hr_expense.group_hr_expense_team_approver,'
                   'hr_holidays.group_hr_holidays_user',
        )
        cls.approver_user = new_test_user(
            cls.env, login='bs_appr',
            groups='base.group_user,'
                   'purchase.group_purchase_user,'
                   'hr_expense.group_hr_expense_team_approver,'
                   'hr_holidays.group_hr_holidays_user',
        )
        cls.requester_user = new_test_user(
            cls.env, login='bs_req',
            groups='base.group_user,'
                   'purchase.group_purchase_user,'
                   'hr_expense.group_hr_expense_user,'
                   'hr_holidays.group_hr_holidays_user',
        )
        cls.employee_manager = cls.env['hr.employee'].sudo().create({
            'name': 'Manager Employee',
            'user_id': cls.manager_user.id,
            'work_contact_id': cls.manager_user.partner_id.id,
        })
        cls.employee_approver = cls.env['hr.employee'].sudo().create({
            'name': 'Approver Employee',
            'user_id': cls.approver_user.id,
            'parent_id': cls.employee_manager.id,
            'work_contact_id': cls.approver_user.partner_id.id,
            'leave_manager_id': cls.approver_user.id,
            'expense_manager_id': cls.approver_user.id,
        })
        cls.employee_requester = cls.env['hr.employee'].sudo().create({
            'name': 'Requester Employee',
            'user_id': cls.requester_user.id,
            'parent_id': cls.employee_manager.id,
            'work_contact_id': cls.requester_user.partner_id.id,
            'expense_manager_id': cls.approver_user.id,
        })
        cls.leave_type = cls.env['hr.leave.type'].sudo().create({
            'name': 'Test Annual Leave',
            'requires_allocation': False,
            'leave_validation_type': 'manager',
        })
        cls.vendor = cls.env['res.partner'].sudo().create({'name': 'Test Vendor'})

        # Fixed reference instants (weekdays, standard Mon-Fri working calendar).
        cls.FRI_9 = datetime(2026, 1, 9, 9, 0, 0)
        cls.MON_9 = datetime(2026, 1, 12, 9, 0, 0)
        cls.MON_17 = datetime(2026, 1, 12, 17, 0, 0)
        cls.WED_9 = datetime(2026, 1, 14, 9, 0, 0)
        cls.THU_17 = datetime(2026, 1, 15, 17, 0, 0)

    def _backdate(self, record, dt):
        """Rewrite create_date to a deterministic past instant (tests only)."""
        self.env.cr.execute(
            'UPDATE %s SET create_date = %%s WHERE id = %%s' % record._table,
            (fields.Datetime.to_string(dt), record.id),
        )
        record.invalidate_recordset()

    def _make_config(self, approval_type, reminder, escalation, backup=None, fallback=None):
        return self.env['bs.approval.reminder.config'].sudo().create({
            'approval_type': approval_type,
            'reminder_threshold_days': reminder,
            'escalation_threshold_days': escalation,
            'backup_approver_id': backup.id if backup else False,
            'fallback_admin_id': fallback.id if fallback else False,
        })

    def _activities(self, record):
        return self.env['mail.activity'].sudo().search([
            ('res_model', '=', record._name),
            ('res_id', '=', record.id),
        ])

    def _logs(self, record_ref, action=None):
        domain = [('record_ref', '=', record_ref)]
        if action:
            domain.append(('action_taken', '=', action))
        return self.env['bs.approval.reminder.log'].sudo().search(domain)

    # --- fixture builders -------------------------------------------------

    def _create_po(self, user=None, state='to approve'):
        po = self.env['purchase.order'].sudo().create({
            'partner_id': self.vendor.id,
            'user_id': (user or self.approver_user).id,
        })
        po.sudo().state = state
        return po

    def _create_expense(self, state='submitted'):
        expense = self.env['hr.expense'].sudo().create({
            'name': 'Test Expense',
            'employee_id': self.employee_requester.id,
            'total_amount_currency': 100.0,
        })
        expense.sudo().approval_state = state
        return expense

    def _create_leave(self, state='confirm'):
        leave = self.env['hr.leave'].sudo().create({
            'name': 'Test Leave',
            'employee_id': self.employee_approver.id,
            'holiday_status_id': self.leave_type.id,
            'request_date_from': fields.Date.to_date('2026-02-02'),
            'request_date_to': fields.Date.to_date('2026-02-02'),
        })
        leave.sudo().state = state
        return leave


@tagged('post_install', '-at_install')
class TestBusinessDayCalculation(CommonApprovalReminderCase):

    def test_weekends_are_excluded(self):
        po = self._create_po()
        self._backdate(po, self.FRI_9)
        days = po._bs_business_days_pending(self.MON_17)
        # Friday(partial) + Monday(partial) only — Saturday/Sunday not counted.
        self.assertGreater(days, 0.5)
        self.assertLess(days, 3.0)

    def test_configured_calendar_holidays_are_excluded(self):
        calendar = self.env['resource.calendar'].sudo().create({
            'name': 'Test Calendar Mon-Fri',
            'attendance_ids': [
                (0, 0, {'name': 'Mon', 'dayofweek': '0', 'hour_from': 8.0, 'hour_to': 17.0, 'day_period': 'morning'}),
                (0, 0, {'name': 'Tue', 'dayofweek': '1', 'hour_from': 8.0, 'hour_to': 17.0, 'day_period': 'morning'}),
                (0, 0, {'name': 'Wed', 'dayofweek': '2', 'hour_from': 8.0, 'hour_to': 17.0, 'day_period': 'morning'}),
                (0, 0, {'name': 'Thu', 'dayofweek': '3', 'hour_from': 8.0, 'hour_to': 17.0, 'day_period': 'morning'}),
                (0, 0, {'name': 'Fri', 'dayofweek': '4', 'hour_from': 8.0, 'hour_to': 17.0, 'day_period': 'morning'}),
            ],
        })
        self.env['resource.calendar.leaves'].sudo().create({
            'name': 'Regional Holiday',
            'calendar_id': calendar.id,
            'date_from': datetime(2026, 1, 14, 0, 0, 0),
            'date_to': datetime(2026, 1, 14, 23, 59, 59),
            'time_type': 'leave',
        })
        company = self.env.company.sudo()
        original_calendar = company.resource_calendar_id
        company.resource_calendar_id = calendar
        try:
            po = self._create_po()
            self._backdate(po, self.MON_9)
            days_with_holiday = po._bs_business_days_pending(self.THU_17)
            # Mon -> Thu is 4 working days; the Wednesday holiday drops it by one.
            self.assertGreaterEqual(days_with_holiday, 2.0)
            self.assertLess(days_with_holiday, 4.0)
        finally:
            company.resource_calendar_id = original_calendar

    def test_raw_day_fallback_without_calendar(self):
        company = self.env.company.sudo()
        original_calendar = company.resource_calendar_id
        company.resource_calendar_id = False
        try:
            po = self._create_po()
            self._backdate(po, self.FRI_9)
            days = po._bs_business_days_pending(self.MON_17)
            self.assertEqual(days, 3.0)
        finally:
            company.resource_calendar_id = original_calendar


@tagged('post_install', '-at_install')
class TestThresholdAndActions(CommonApprovalReminderCase):

    def test_reminder_fires_for_purchase_order(self):
        config = self._make_config('purchase_order', 1, 3)
        po = self._create_po(user=self.approver_user)
        self._backdate(po, self.FRI_9)
        result = po._bs_check_and_act(config, self.MON_17)
        self.assertEqual(result, 'reminded')
        activities = self._activities(po)
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities.user_id.id, self.approver_user.id)
        self.assertEqual(
            activities.activity_type_id.id,
            self.env.ref(
                'bs_approval_reminder_escalation_bot.bs_activity_type_reminder',
            ).id,
        )
        logs = self._logs('purchase.order,%s' % po.id, 'reminded')
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs.original_approver_id.id, self.approver_user.id)

    def test_expense_uses_configured_approver(self):
        config = self._make_config('expense_report', 1, 3)
        expense = self._create_expense()
        self._backdate(expense, self.FRI_9)
        result = expense._bs_check_and_act(config, self.MON_17)
        self.assertEqual(result, 'reminded')
        activities = self._activities(expense)
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities.user_id.id, self.approver_user.id)

    def test_leave_uses_responsible_approver(self):
        config = self._make_config('time_off', 1, 3)
        leave = self._create_leave()
        self._backdate(leave, self.FRI_9)
        result = leave._bs_check_and_act(config, self.MON_17)
        self.assertEqual(result, 'reminded')
        our_types = self.env.ref(
            'bs_approval_reminder_escalation_bot.bs_activity_type_reminder',
        ).id
        activities = self._activities(leave).filtered(
            lambda a: a.activity_type_id.id == our_types,
        )
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities.user_id.id, self.approver_user.id)

    def test_escalation_above_longer_threshold(self):
        config = self._make_config('purchase_order', 1, 2, backup=self.manager_user)
        po = self._create_po(user=self.approver_user)
        self._backdate(po, self.MON_9)
        result = po._bs_check_and_act(config, self.THU_17)
        self.assertEqual(result, 'escalated')
        activities = self._activities(po)
        self.assertEqual(len(activities), 1)
        self.assertEqual(
            activities.activity_type_id.id,
            self.env.ref(
                'bs_approval_reminder_escalation_bot.bs_activity_type_escalation',
            ).id,
        )
        self.assertEqual(activities.user_id.id, self.manager_user.id)
        logs = self._logs('purchase.order,%s' % po.id, 'escalated')
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs.escalated_to_id.id, self.manager_user.id)

    def test_no_escalation_below_threshold(self):
        config = self._make_config('purchase_order', 3, 5)
        po = self._create_po(user=self.approver_user)
        self._backdate(po, self.MON_9)
        result = po._bs_check_and_act(config, self.THU_17)
        self.assertEqual(result, 'reminded')
        self.assertEqual(len(self._logs('purchase.order,%s' % po.id, 'escalated')), 0)

    def test_same_record_not_reminded_twice_in_one_day(self):
        # Real "now" drives both calls: the record must be past the reminder
        # threshold but far below the escalation threshold at that instant.
        config = self._make_config('purchase_order', 1, 20)
        po = self._create_po(user=self.approver_user)
        self._backdate(po, fields.Datetime.now() - timedelta(days=3))
        # Two invocations against real "today": the second must be suppressed
        # by the already-acted-today guard.
        self.assertEqual(po._bs_check_and_act(config), 'reminded')
        self.assertEqual(po._bs_check_and_act(config), 'none')
        self.assertEqual(len(self._activities(po)), 1)

    def test_config_validations(self):
        with self.assertRaises(ValidationError):
            self._make_config('purchase_order', 3, 3)
        with self.assertRaises(ValidationError):
            self._make_config('purchase_order', 5, 2)
        with self.assertRaises(ValidationError):
            self._make_config('purchase_order', 0, 3)


@tagged('post_install', '-at_install')
class TestSnooze(CommonApprovalReminderCase):

    def test_snooze_suppresses_until_date(self):
        config = self._make_config('purchase_order', 1, 3)
        po = self._create_po(user=self.approver_user)
        self._backdate(po, self.FRI_9)
        po.bs_reminder_snoozed_until = fields.Date.to_date('2026-01-12')
        self.assertEqual(po._bs_check_and_act(config, self.MON_17), 'snoozed')
        self.assertEqual(len(self._activities(po)), 0)
        self.assertEqual(len(self._logs('purchase.order,%s' % po.id)), 0)

    def test_snooze_expired_resumes_reminders(self):
        config = self._make_config('purchase_order', 1, 3)
        po = self._create_po(user=self.approver_user)
        self._backdate(po, self.FRI_9)
        po.bs_reminder_snoozed_until = fields.Date.to_date('2026-01-11')
        self.assertEqual(po._bs_check_and_act(config, self.MON_17), 'reminded')

    def test_snooze_wizard_bounds_are_validated(self):
        wizard = self.env['bs.approval.reminder.snooze.wizard'].create({'days': 3})
        self.assertEqual(wizard.days, 3)
        for bad in (0, -1, 15, 100):
            with self.assertRaises(ValidationError):
                self.env['bs.approval.reminder.snooze.wizard'].create({'days': bad})


@tagged('post_install', '-at_install')
class TestFallbackChain(CommonApprovalReminderCase):

    def test_configured_backup_takes_precedence(self):
        config = self._make_config('purchase_order', 1, 3, backup=self.manager_user)
        po = self._create_po(user=self.approver_user)
        self._backdate(po, self.FRI_9)
        recipient = po._bs_resolve_escalation_recipient(config, self.approver_user)
        self.assertEqual(recipient.id, self.manager_user.id)

    def test_manager_fallback_when_no_backup(self):
        config = self._make_config('purchase_order', 1, 3)
        po = self._create_po(user=self.approver_user)
        recipient = po._bs_resolve_escalation_recipient(config, self.approver_user)
        self.assertEqual(recipient.id, self.manager_user.id)

    def test_final_fallback_when_no_backup_and_no_manager(self):
        config = self._make_config('expense_report', 1, 3)
        lonely_user = new_test_user(self.env, login='bs_lonely', groups='base.group_user')
        expense = self.env['hr.expense'].sudo().create({
            'name': 'Test Expense',
            'employee_id': self.employee_approver.id,
            'total_amount_currency': 100.0,
        })
        expense.sudo().manager_id = lonely_user.id
        expense.sudo().approval_state = 'submitted'
        # lonely user has no employee, no parent, no configured backup,
        # no fallback admin -> the chain must still resolve a recipient.
        recipient = expense._bs_resolve_escalation_recipient(config, lonely_user)
        self.assertTrue(recipient)
        self.assertNotEqual(recipient.id, lonely_user.id)


@tagged('post_install', '-at_install')
class TestRaceAndInactiveApprover(CommonApprovalReminderCase):

    def test_inactive_approver_escalates_immediately(self):
        config = self._make_config('purchase_order', 1, 5)
        inactive_user = new_test_user(self.env, login='bs_inactive', groups='base.group_user')
        inactive_user.active = False
        po = self._create_po(user=inactive_user)
        self._backdate(po, self.FRI_9)
        result = po._bs_check_and_act(config, self.MON_17)
        self.assertEqual(result, 'escalated')
        logs = self._logs('purchase.order,%s' % po.id, 'escalated')
        self.assertEqual(len(logs), 1)
        self.assertTrue(logs.escalated_to_id)

    def test_approved_between_query_and_send_gets_no_reminder(self):
        config = self._make_config('purchase_order', 1, 3)
        po = self._create_po(user=self.approver_user)
        self._backdate(po, self.FRI_9)
        po.sudo().state = 'purchase'  # approved in the meantime
        result = po._bs_check_and_act(config, self.MON_17)
        self.assertEqual(result, 'none')
        self.assertEqual(len(self._activities(po)), 0)
        self.assertEqual(len(self._logs('purchase.order,%s' % po.id)), 0)

    def test_full_run_never_changes_approval_state(self):
        self._make_config('purchase_order', 1, 2)
        self._make_config('expense_report', 1, 2)
        self._make_config('time_off', 1, 2)
        po = self._create_po(user=self.approver_user)
        expense = self._create_expense()
        leave = self._create_leave()
        backdated_since = fields.Datetime.now() - timedelta(days=20)
        for record in (po, expense, leave):
            self._backdate(record, backdated_since)
        self.env['bs.approval.reminder.config'].sudo()._cron_approval_reminder_check()
        # Regression: no approval decision was changed by the reminder bot.
        self.assertEqual(po.state, 'to approve')
        self.assertEqual(expense.state, 'submitted')
        self.assertEqual(leave.state, 'confirm')
        # And the actions were recorded.
        self.assertTrue(self._logs('purchase.order,%s' % po.id))
        self.assertTrue(self._logs('hr.expense,%s' % expense.id))
        self.assertTrue(self._logs('hr.leave,%s' % leave.id))
