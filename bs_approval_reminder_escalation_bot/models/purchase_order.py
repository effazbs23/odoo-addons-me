from odoo import models


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = ['purchase.order', 'bs.approval.reminder.mixin']

    # Snooze field + reminder logic come from bs.approval.reminder.mixin.

    def _bs_is_pending(self):
        return self.state == 'to approve'

    def _bs_get_approval_type(self):
        return 'purchase_order'

    def _bs_get_primary_approver(self):
        self.ensure_one()
        if self.user_id:
            return self.user_id
        # No buyer set: fall back to an active purchase manager to own reminders.
        group = self.env.ref('purchase.group_purchase_manager', raise_if_not_found=False)
        if not group:
            return self.env['res.users']
        return group.sudo().all_user_ids.filtered('active')[:1]

    def _bs_pending_domain(self):
        return [('state', '=', 'to approve')]
