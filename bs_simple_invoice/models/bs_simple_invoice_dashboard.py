from odoo import fields, models


class BsSimpleInvoiceDashboard(models.TransientModel):
    """Read-only summary card (spec 7.6): opened fresh (never saved) every
    time the Dashboard menu item is clicked, so the numbers are always
    current. All aggregation reuses account.move via read_group -- no new
    reporting engine, no stored state."""
    _name = 'bs.simple.invoice.dashboard'
    _description = "Simple Invoicing Dashboard"

    # Gives the ORM's default display_name/breadcrumb something readable
    # instead of falling back to "bs.simple.invoice.dashboard,NewId_xxx"
    # for this never-saved record -- caught by opening the Dashboard menu
    # in a real browser.
    name = fields.Char(default="Simple Invoicing Dashboard")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    awaiting_payment_count = fields.Integer(string="Invoices Awaiting Payment")
    amount_overdue = fields.Monetary(string="Overdue")
    amount_collected_this_month = fields.Monetary(string="Collected This Month")

    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        Move = self.env['account.move']
        base_domain = [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('state', '=', 'posted'),
            ('company_id', '=', self.env.company.id),
        ]
        today = fields.Date.context_today(self)
        month_start = today.replace(day=1)

        # 'blocked' (a payment_state for invoices with a blocked partial
        # reconciliation) counts as still-awaiting-payment here, matching
        # simple_status on account.move which falls through to the same
        # due-date-based Sent/Overdue classification for it.
        unpaid_states = ('not_paid', 'partial', 'blocked')
        if 'awaiting_payment_count' in fields_list:
            vals['awaiting_payment_count'] = Move.search_count(
                base_domain + [('payment_state', 'in', unpaid_states)]
            )
        if 'amount_overdue' in fields_list:
            groups = Move._read_group(
                base_domain + [
                    ('payment_state', 'in', unpaid_states),
                    ('invoice_date_due', '<', today),
                ],
                aggregates=['amount_residual:sum'],
            )
            vals['amount_overdue'] = groups[0][0] if groups else 0.0
        if 'amount_collected_this_month' in fields_list:
            # Approximation: sum of fully-paid invoices dated this month
            # (account.move has no separate "paid on" date; a precise
            # figure would need account.payment, which is outside the
            # "existing account.move aggregations, no new reporting
            # engine" scope for v1).
            groups = Move._read_group(
                base_domain + [
                    ('payment_state', '=', 'paid'),
                    ('invoice_date', '>=', month_start),
                    ('invoice_date', '<=', today),
                ],
                aggregates=['amount_total:sum'],
            )
            vals['amount_collected_this_month'] = groups[0][0] if groups else 0.0
        return vals
