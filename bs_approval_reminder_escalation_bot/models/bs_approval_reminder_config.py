from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class BsApprovalReminderConfig(models.Model):
    _name = 'bs.approval.reminder.config'
    _description = 'Approval Reminder Configuration'
    _rec_name = 'approval_type'
    _order = 'approval_type'

    approval_type = fields.Selection([
        ('purchase_order', 'Purchase Order'),
        ('expense_report', 'Expense Report'),
        ('time_off', 'Time Off'),
    ], string='Approval Type', required=True)
    reminder_threshold_days = fields.Integer(
        string='Reminder Threshold (Business Days)',
        default=3,
        required=True,
        help='Number of business days a request can sit pending before the first reminder fires.',
    )
    escalation_threshold_days = fields.Integer(
        string='Escalation Threshold (Business Days)',
        default=5,
        required=True,
        help='Number of business days before escalation to a backup approver. Must be greater than the reminder threshold.',
    )
    backup_approver_id = fields.Many2one(
        'res.users',
        string='Backup Approver',
        ondelete='set null',
        help='Who receives an escalation. If unset, falls back to the original approver\'s manager, then the configured fallback admin.',
    )
    fallback_admin_id = fields.Many2one(
        'res.users',
        string='Final Fallback Recipient',
        ondelete='set null',
        help='Last-resort recipient when no backup approver is configured and the original approver has no manager.',
    )
    active = fields.Boolean(string='Active', default=True)

    _unique_type = models.Constraint(
        'UNIQUE(approval_type)',
        'A configuration already exists for this approval type.',
    )

    @api.constrains('reminder_threshold_days', 'escalation_threshold_days')
    def _check_thresholds(self):
        for config in self:
            if config.reminder_threshold_days < 1:
                raise ValidationError(
                    _('Reminder threshold must be at least 1 business day.'),
                )
            if config.escalation_threshold_days <= config.reminder_threshold_days:
                raise ValidationError(
                    _('Escalation threshold must be greater than the reminder threshold.'),
                )

    @api.model
    def _get_target_model(self, approval_type):
        return {
            'purchase_order': 'purchase.order',
            'expense_report': 'hr.expense',
            'time_off': 'hr.leave',
        }.get(approval_type)

    @api.model
    def _get_config_for_type(self, approval_type):
        return self.sudo().search([
            ('approval_type', '=', approval_type),
            ('active', '=', True),
        ], limit=1)

    @api.model
    def _cron_approval_reminder_check(self):
        """Cron entry point: runs the reminder/escalation check for every
        active configuration across the three supported approval types."""
        configs = self.sudo().search([('active', '=', True)])
        for config in configs:
            model_name = self._get_target_model(config.approval_type)
            if not model_name:
                continue
            model = self.env[model_name]
            if not hasattr(model, '_bs_process_pending'):
                continue
            model._bs_process_pending(config)
        return True
