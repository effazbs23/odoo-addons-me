from odoo import models


class HrExpense(models.Model):
    _name = 'hr.expense'
    _inherit = ['hr.expense', 'bs.approval.reminder.mixin']

    # Snooze field + reminder logic come from bs.approval.reminder.mixin.
    # NOTE: Odoo 19 merged hr.expense.sheet into hr.expense; the "submitted"
    # state is the pending-approval state (computed from approval_state).

    def _bs_is_pending(self):
        return self.state == 'submitted'

    def _bs_get_approval_type(self):
        return 'expense_report'

    def _bs_get_primary_approver(self):
        self.ensure_one()
        if self.manager_id:
            return self.manager_id
        return self.sudo()._get_default_responsible_for_approval()

    def _bs_pending_domain(self):
        return [('state', '=', 'submitted')]
