from odoo import api, fields, models

CUSTOMER_MOVE_TYPES = ('out_invoice', 'out_refund')


class AccountMove(models.Model):
    _inherit = 'account.move'

    notify_log_count = fields.Integer(compute='_compute_notify_log_count')
    partner_has_valid_notify_number = fields.Boolean(related='partner_id.has_valid_notify_number')

    def _compute_notify_log_count(self):
        for move in self:
            move.notify_log_count = self.env['bs.notify.log'].search_count([
                ('source_record_ref', '=', 'account.move,%s' % move.id),
            ])

    def action_view_notify_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Notifications",
            'res_model': 'bs.notify.log',
            'view_mode': 'list,form',
            'domain': [('source_record_ref', '=', 'account.move,%s' % self.id)],
        }

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        for move in posted.filtered(lambda m: m.move_type in CUSTOMER_MOVE_TYPES):
            self.env['bs.notify.log']._send_notification('invoice_posted', move)
        return posted

    def _compute_payment_state(self):
        # Snapshot before recompute: only a genuine not-paid -> paid
        # transition should fire a notification. _compute_payment_state
        # can run many times for reasons unrelated to this invoice's own
        # payment (recompute batching, unrelated writes on dependent
        # fields) -- comparing against the pre-recompute value keeps this
        # correct regardless of how many times it's invoked, and partial
        # payments never reach 'paid' so they never fire (spec section 9).
        previous_state = {move.id: move.payment_state for move in self}
        super()._compute_payment_state()
        for move in self.filtered(lambda m: m.move_type in CUSTOMER_MOVE_TYPES):
            if previous_state.get(move.id) != 'paid' and move.payment_state == 'paid':
                self.env['bs.notify.log']._send_notification('payment_received', move)

    @api.model
    def _cron_notify_overdue_invoices(self):
        overdue = self.search([
            ('move_type', 'in', CUSTOMER_MOVE_TYPES),
            ('state', '=', 'posted'),
            ('payment_state', 'not in', ('paid', 'in_payment', 'reversed')),
            ('invoice_date_due', '<', fields.Date.context_today(self)),
        ])
        for move in overdue:
            self.env['bs.notify.log']._send_notification('invoice_overdue', move)
