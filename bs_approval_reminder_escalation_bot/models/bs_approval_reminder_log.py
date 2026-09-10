from odoo import fields, models


class BsApprovalReminderLog(models.Model):
    _name = 'bs.approval.reminder.log'
    _description = 'Approval Reminder Log'
    _order = 'create_date desc'

    approval_type = fields.Selection([
        ('purchase_order', 'Purchase Order'),
        ('expense_report', 'Expense Report'),
        ('time_off', 'Time Off'),
    ], string='Approval Type', required=True)
    record_ref = fields.Reference([
        ('purchase.order', 'Purchase Order'),
        ('hr.expense', 'Expense'),
        ('hr.leave', 'Time Off'),
    ], string='Record', required=True)
    action_taken = fields.Selection([
        ('reminded', 'Reminded'),
        ('escalated', 'Escalated'),
        ('snoozed', 'Snoozed'),
    ], string='Action Taken', required=True)
    original_approver_id = fields.Many2one(
        'res.users', string='Original Approver', ondelete='set null',
    )
    escalated_to_id = fields.Many2one(
        'res.users', string='Escalated To', ondelete='set null',
    )
    create_date = fields.Datetime(string='Logged On', readonly=True, index=True)

    def _log_action(self, approval_type, record, action, original_approver, escalated_to=None):
        self.sudo().create({
            'approval_type': approval_type,
            'record_ref': '%s,%s' % (record._name, record.id),
            'action_taken': action,
            'original_approver_id': original_approver.id if original_approver else False,
            'escalated_to_id': escalated_to.id if escalated_to else False,
        })

    def _was_acted_today(self, record_ref, actions=('reminded', 'escalated'), ref_date=None):
        logs = self.sudo().search([
            ('record_ref', '=', record_ref),
            ('action_taken', 'in', list(actions)),
        ])
        ref_date = ref_date or fields.Date.context_today(self)
        for log in logs:
            log_local_date = fields.Datetime.context_timestamp(self, log.create_date).date()
            if log_local_date == ref_date:
                return True
        return False
