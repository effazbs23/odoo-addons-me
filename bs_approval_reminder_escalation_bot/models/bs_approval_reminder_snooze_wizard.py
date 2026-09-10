from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class BsApprovalReminderSnoozeWizard(models.TransientModel):
    _name = 'bs.approval.reminder.snooze.wizard'
    _description = 'Snooze Approval Reminder Wizard'

    days = fields.Integer(
        string='Snooze For (Days)',
        required=True,
        default=3,
        help='Number of days to postpone reminders for this record (1-14).',
    )

    snooze_preset = fields.Selection(
        selection=[
            ('1', '1 day'),
            ('2', '2 days'),
            ('3', '3 days'),
            ('5', '5 days'),
            ('7', '1 week'),
            ('10', '10 days'),
            ('14', '2 weeks'),
        ],
        string='Snooze For',
        default='3',
        required=True,
        help='Predefined snooze durations (1-14 days) shown as a dropdown in the wizard.',
    )

    @api.onchange('snooze_preset')
    def _onchange_snooze_preset(self):
        if self.snooze_preset:
            self.days = int(self.snooze_preset)

    @api.constrains('days')
    def _check_days_bounds(self):
        for wizard in self:
            # Edge case: prevent accidental indefinite or already-past snoozes.
            if not 1 <= wizard.days <= 14:
                raise ValidationError(
                    _('Snooze duration must be between 1 and 14 days.'),
                )

    def action_confirm(self):
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        record = self.env[active_model].browse(active_id)
        until = fields.Date.context_today(self) + timedelta(days=self.days)
        record.bs_reminder_snoozed_until = until
        if hasattr(record, '_bs_log'):
            record._bs_log('snoozed', record._bs_get_primary_approver())
        return {'type': 'ir.actions.act_window_close'}
