from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_simple_invoicing_view = fields.Boolean(
        compute='_compute_is_simple_invoicing_view',
        help="True when the current user should see the simplified invoice "
             "form: member of Simple Invoicing User and not of Accounting "
             "Administrator (accountant-wins precedence). Depends only on "
             "the current user, never stored.",
    )

    # edge case (spec 9): a user in both Simple Invoicing and the
    # Accounting Administrator group must always get the full view --
    # tested in tests/test_simple_invoicing.py::test_accountant_wins_precedence
    @api.depends_context('uid')
    def _compute_is_simple_invoicing_view(self):
        simple = self.env.user.has_group('bs_simple_invoice.simple_invoicing_group') \
            and not self.env.user.has_group('account.group_account_manager')
        for move in self:
            move.is_simple_invoicing_view = simple

    # edge case (spec 9): credit notes (move_type == 'out_refund') get no
    # special-casing anywhere in this module -- they flow through the same
    # simplified form/list/status/buttons as invoices, per spec's own
    # recommendation to show them, not hide the concept.

    simple_status = fields.Selection(
        selection=[
            ('draft', "Draft"),
            ('sent', "Sent"),
            ('paid', "Paid"),
            ('overdue', "Overdue"),
            ('cancelled', "Cancelled"),
        ],
        string="Simple Status",
        compute='_compute_simple_status',
        help="Plain-language status shown to Simple Invoicing users, mapped "
             "from the native status_in_payment/invoice_date_due fields. "
             "Never stored, so it can never drift from the source of truth.",
    )

    @api.depends('status_in_payment', 'invoice_date_due')
    def _compute_simple_status(self):
        today = fields.Date.context_today(self)
        for move in self:
            status = move.status_in_payment
            if status == 'draft':
                move.simple_status = 'draft'
            elif status == 'cancel':
                move.simple_status = 'cancelled'
            elif status in ('paid', 'in_payment', 'reversed'):
                move.simple_status = 'paid'
            elif move.invoice_date_due and move.invoice_date_due < today:
                # edge case (spec 9): partial/blocked/sent-but-unpaid past
                # the due date must show Overdue, never collapse into Paid
                move.simple_status = 'overdue'
            else:
                move.simple_status = 'sent'

    def action_simple_mark_as_sent(self):
        """One-click 'Mark as Sent': posts + emails the standard invoice
        template in one action. Thin wrapper over native action_post() /
        message_post_with_source() -- no new posting or send logic."""
        for move in self:
            if move.state == 'draft':
                move.action_post()
            move.message_post_with_source(
                move._get_mail_template(),
                subtype_xmlid='mail.mt_comment',
            )
            move.is_move_sent = True

    def action_simple_register_payment(self):
        """One-click 'Record Payment': thin wrapper opening the native
        account.payment.register wizard, pre-filled as usual."""
        return self.action_register_payment()
