from odoo import models


class HrLeave(models.Model):
    _name = 'hr.leave'
    _inherit = ['hr.leave', 'bs.approval.reminder.mixin']

    # Snooze field + reminder logic come from bs.approval.reminder.mixin.

    def _bs_is_pending(self):
        return self.state in ('confirm', 'validate1')

    def _bs_get_approval_type(self):
        return 'time_off'

    def _bs_get_primary_approver(self):
        self.ensure_one()
        return self.sudo()._get_responsible_for_approval()[:1]

    def _bs_pending_domain(self):
        return [('state', 'in', ('confirm', 'validate1'))]
