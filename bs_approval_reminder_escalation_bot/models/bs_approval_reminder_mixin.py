from collections import defaultdict

from odoo import _, api, fields, models


class BsApprovalReminderMixin(models.AbstractModel):
    _name = 'bs.approval.reminder.mixin'
    _description = 'Approval Reminder & Escalation Bot Mixin'

    bs_reminder_snoozed_until = fields.Date(
        string='Reminder Snoozed Until',
        copy=False,
        help='While this date is in the future, no reminder or escalation fires for this record.',
    )

    def action_bs_snooze_reminder(self):
        """Open the bound-validated snooze wizard (1-14 days)."""
        self.ensure_one()
        return {
            'name': _('Snooze Approval Reminder'),
            'type': 'ir.actions.act_window',
            'res_model': 'bs.approval.reminder.snooze.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'active_ids': self.ids,
                'active_model': self._name,
            },
        }

    # ------------------------------------------------------------------
    # Abstract hooks — implemented by each target model.
    # ------------------------------------------------------------------

    def _bs_is_pending(self):
        """True if this record is currently awaiting an approval decision."""
        raise NotImplementedError()

    def _bs_get_approval_type(self):
        """Return the approval_type selection key for this record's model."""
        raise NotImplementedError()

    def _bs_get_primary_approver(self):
        """Return the primary user (res.users) responsible for this approval."""
        raise NotImplementedError()

    def _bs_get_approver_users(self):
        """Return all users responsible for this pending approval (res.users)."""
        return self._bs_get_primary_approver()

    def _bs_pending_domain(self):
        """Return the search domain selecting all pending records of this model."""
        raise NotImplementedError()

    def _bs_get_pending_since_dt(self):
        """Naive UTC datetime marking the start of the pending period."""
        return self.create_date or fields.Datetime.now()

    def _bs_record_label(self):
        return self.display_name

    # ------------------------------------------------------------------
    # Business-day calculation (reuses resource.calendar - no new math).
    # ------------------------------------------------------------------

    def _bs_business_days_pending(self, ref_dt=None):
        ref_dt = ref_dt or fields.Datetime.now()
        start_dt = self._bs_get_pending_since_dt()
        end_dt = ref_dt
        if start_dt > end_dt:
            return 0.0
        company = self.company_id if 'company_id' in self._fields else self.env.company
        calendar = company.sudo().resource_calendar_id if company else False
        if not calendar:
            calendar = self.env.company.sudo().resource_calendar_id
        if not calendar:
            # No configured calendar anywhere: raw calendar-day fallback.
            start_local = fields.Datetime.context_timestamp(self, start_dt)
            end_local = fields.Datetime.context_timestamp(self, end_dt)
            return float(max((end_local.date() - start_local.date()).days, 0))
        data = calendar.sudo().get_work_duration_data(
            start_dt, end_dt, compute_leaves=True,
        )
        return data.get('days', 0.0)

    # ------------------------------------------------------------------
    # Recipient resolution.
    # ------------------------------------------------------------------

    def _bs_resolve_escalation_recipient(self, config, approver):
        """Backup chain: configured backup -> approver's manager -> final fallback.

        Covers the "no backup approver configured AND no manager set" edge case:
        it must never silently fail to escalate.
        """
        recipient = self.env['res.users']
        if config.backup_approver_id:
            recipient = config.backup_approver_id
        if not recipient and approver:
            recipient = approver.employee_id.parent_id.user_id
        if not recipient:
            recipient = config.fallback_admin_id
        if not recipient:
            # Last-resort safe defaults rather than a silent no-op.
            group = self.env.ref(
                'base.group_erp_manager', raise_if_not_found=False,
            )
            if group:
                recipient = group.sudo().all_user_ids.filtered('active')[:1]
        if not recipient:
            recipient = self.env['res.users'].sudo().search([
                ('active', '=', True),
                ('share', '=', False),
            ], limit=1)
        return recipient

    # ------------------------------------------------------------------
    # Delivery + logging.
    # ------------------------------------------------------------------

    def _bs_schedule_activity(self, user, summary, note, escalation=False):
        xmlid = (
            'bs_approval_reminder_escalation_bot.bs_activity_type_escalation'
            if escalation
            else 'bs_approval_reminder_escalation_bot.bs_activity_type_reminder'
        )
        self.with_context(mail_activity_quick_update=True).activity_schedule(
            xmlid,
            summary=summary,
            note=note,
            user_id=user.id,
        )

    def _bs_log(self, action, approver, escalated_to=None):
        self.env['bs.approval.reminder.log']._log_action(
            self._bs_get_approval_type(), self, action, approver, escalated_to,
        )

    def _bs_send_reminder(self, config, approver):
        days = int(self._bs_business_days_pending())
        summary = _('Reminder: approval still pending')
        note = _(
            '<p>This %(kind)s has been waiting for %(days)s business days for '
            'your approval.</p><p>Please review it as soon as possible.</p>',
            kind=self._bs_record_label(),
            days=days,
        )
        self._bs_schedule_activity(approver, summary, note)
        self._bs_log('reminded', approver)

    def _bs_send_escalation(self, config, approver):
        days = int(self._bs_business_days_pending())
        recipient = self._bs_resolve_escalation_recipient(config, approver)
        summary = _('Escalation: approval waiting too long')
        note = _(
            '<p>This %(kind)s has been awaiting approval for %(days)s business days.</p>'
            '<p>The original approver (%(approver)s) has not acted. This pending '
            'approval is escalated to you for review.</p>',
            kind=self._bs_record_label(),
            days=days,
            approver=approver.name if approver else _('unknown'),
        )
        self._bs_schedule_activity(recipient, summary, note, escalation=True)
        self._bs_log('escalated', approver, escalated_to=recipient)

    # ------------------------------------------------------------------
    # Per-record decision logic (edge-case handlers are commented inline).
    # ------------------------------------------------------------------

    def _bs_check_and_act(self, config, ref_dt=None):
        """Decide (remind / escalate / snooze / nothing) for one pending record.

        ``ref_dt`` optionally pins "now" (used by tests for determinism).

        Returns 'reminded', 'escalated', 'snoozed' or 'none'.
        """
        ref_dt = ref_dt or fields.Datetime.now()
        ref_date = fields.Datetime.context_timestamp(self, ref_dt).date()
        # Race-condition guard: re-read the record from the database right now,
        # so a decision made (approved/rejected) between the cron's search and
        # this point never receives a stale reminder.
        fresh = self
        if self.id:
            fresh = self.env[self._name].browse(self.id)
            fresh.invalidate_recordset()
        if not fresh._bs_is_pending():
            return 'none'

        approver = fresh._bs_get_primary_approver()
        record_ref = '%s,%s' % (fresh._name, fresh.id)
        log_model = self.env['bs.approval.reminder.log']

        # Snooze check: while snoozed until (>=) today, no reminder/escalation.
        # Checked before the immediate-escalation edge cases so an explicit
        # snooze is never overridden by them.
        if fresh.bs_reminder_snoozed_until and fresh.bs_reminder_snoozed_until >= ref_date:
            return 'snoozed'

        # Edge cases that escalate immediately rather than waiting for the
        # threshold: no assignable approver at all, or an approver whose
        # account is archived (a reminder to them would go nowhere). Both run
        # through the same once-per-day guard as the threshold path, so a
        # long-stale record is not escalated again on every cron run.
        if not approver or not approver.active:
            if log_model._was_acted_today(record_ref, ('escalated',), ref_date):
                return 'none'
            fresh._bs_send_escalation(config, approver)
            return 'escalated'

        days = fresh._bs_business_days_pending(ref_dt)

        # Edge case: no duplicate reminder/escalation for the same record on
        # the same day (prevents daily spam on long-stale records).
        if days >= config.escalation_threshold_days:
            if not log_model._was_acted_today(record_ref, ('escalated',), ref_date):
                fresh._bs_send_escalation(config, approver)
                return 'escalated'
            return 'none'
        if days >= config.reminder_threshold_days:
            if not log_model._was_acted_today(record_ref, ('reminded', 'escalated'), ref_date):
                fresh._bs_send_reminder(config, approver)
                return 'reminded'
        return 'none'

    @api.model
    def _bs_process_pending(self, config):
        """Model-level cron entry: scan all pending records of this approval type.

        Emails are sent as one digest per recipient per run, so a user with
        several stale items gets a single message instead of an email burst.
        """
        records = self.search(self._bs_pending_domain())
        reminders_by_user = defaultdict(lambda: self.env[self._name])
        escalations_by_user = defaultdict(lambda: self.env[self._name])
        for record in records:
            result = record._bs_check_and_act(config)
            if result == 'reminded':
                approver = record._bs_get_primary_approver()
                if approver:
                    reminders_by_user[approver.id] |= record
            elif result == 'escalated':
                recipient = record._bs_resolve_escalation_recipient(
                    config, record._bs_get_primary_approver(),
                )
                if recipient:
                    escalations_by_user[recipient.id] |= record
        user_model = self.env['res.users']
        for user_id, user_records in reminders_by_user.items():
            self._bs_send_digest_email(
                user_model.browse(user_id), user_records, escalation=False,
            )
        for user_id, user_records in escalations_by_user.items():
            self._bs_send_digest_email(
                user_model.browse(user_id), user_records, escalation=True,
            )
        return True

    # ------------------------------------------------------------------
    # Digest email (single message per recipient instead of a burst).
    # ------------------------------------------------------------------

    def _bs_send_digest_email(self, recipient, records, escalation=False):
        if not recipient or not recipient.email:
            return False
        lines = ''.join(
            '<li>%s — pending since %s</li>' % (
                record._bs_record_label(),
                record._bs_get_pending_since_dt().date(),
            )
            for record in records
        )
        if escalation:
            subject = _('Approval Escalation (%(n)d item(s))') % {'n': len(records)}
            intro = _(
                'The following approvals have been pending too long and have been '
                'escalated to you:',
            )
        else:
            subject = _('Approvals Awaiting Your Review (%(n)d item(s))') % {'n': len(records)}
            intro = _('The following approvals are waiting for your review:')
        body = '<p>%s</p><ul>%s</ul>' % (intro, lines)
        mail = self.env['mail.mail'].sudo().create({
            'subject': subject,
            'body_html': body,
            'email_to': recipient.email,
            'auto_delete': True,
        })
        try:
            mail.send()
        except Exception:  # ruff: ignore[blind-except] - mail failure must never abort the cron
            # A mail delivery failure must never abort the remaining cron
            # (activities + logs are the source of truth for the audit trail).
            return False
        return True
