from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSimpleInvoicing(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.simple_group = cls.env.ref('bs_simple_invoice.simple_invoicing_group')
        cls.manager_group = cls.env.ref('account.group_account_manager')
        cls.partner = cls.env['res.partner'].create({'name': 'Acme Corp'})

        cls.simple_user = cls.env['res.users'].create({
            'name': 'Simple User',
            'login': 'simple_invoicing_test_user',
            'email': 'simple_invoicing_test_user@example.com',
            'group_ids': [(6, 0, [cls.simple_group.id])],
        })
        cls.plain_user = cls.env['res.users'].create({
            'name': 'Plain Billing User',
            'login': 'plain_billing_test_user',
            'email': 'plain_billing_test_user@example.com',
            'group_ids': [(6, 0, [cls.env.ref('account.group_account_invoice').id])],
        })
        cls.dual_user = cls.env['res.users'].create({
            'name': 'Dual User',
            'login': 'dual_test_user_it',
            'email': 'dual_test_user_it@example.com',
            'group_ids': [(6, 0, [cls.simple_group.id, cls.manager_group.id])],
        })

    def _make_invoice(self, **vals):
        base = {
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {'name': 'Line', 'quantity': 1, 'price_unit': 100.0})],
        }
        base.update(vals)
        return self.env['account.move'].create(base)

    def _register_payment(self, move, amount=None):
        vals = {}
        if amount is not None:
            vals['amount'] = amount
        wizard = self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=move.ids,
        ).create(vals)
        wizard._create_payments()
        move.invalidate_recordset()

    # -- spec 10: plain-language status mapping, including partial+overdue --

    def test_simple_status_draft(self):
        move = self._make_invoice()
        self.assertEqual(move.simple_status, 'draft')

    def test_simple_status_sent(self):
        move = self._make_invoice(invoice_date_due=fields.Date.today() + timedelta(days=10))
        move.action_post()
        self.assertEqual(move.simple_status, 'sent')

    def test_simple_status_paid(self):
        move = self._make_invoice()
        move.action_post()
        self._register_payment(move)
        self.assertEqual(move.simple_status, 'paid')

    def test_simple_status_overdue_unpaid(self):
        move = self._make_invoice(invoice_date_due=fields.Date.today() - timedelta(days=5))
        move.action_post()
        self.assertEqual(move.simple_status, 'overdue')

    def test_simple_status_overdue_partial_payment(self):
        # edge case (spec 9): a partially-paid, overdue invoice must show
        # Overdue, never collapse into Paid
        move = self._make_invoice(invoice_date_due=fields.Date.today() - timedelta(days=5))
        move.action_post()
        self._register_payment(move, amount=40.0)
        self.assertEqual(move.payment_state, 'partial')
        self.assertEqual(move.simple_status, 'overdue')

    def test_simple_status_partial_not_yet_due(self):
        move = self._make_invoice(invoice_date_due=fields.Date.today() + timedelta(days=10))
        move.action_post()
        self._register_payment(move, amount=40.0)
        self.assertEqual(move.simple_status, 'sent')

    # -- spec 9: credit notes get no special-casing --

    def test_credit_note_gets_simple_status_too(self):
        credit_note = self._make_invoice(move_type='out_refund')
        self.assertEqual(credit_note.simple_status, 'draft')
        self.assertTrue(
            credit_note.with_user(self.simple_user).is_simple_invoicing_view
        )

    # -- spec 9: non-standard journal is never silently reassigned --

    def test_non_standard_journal_preserved_for_simple_user(self):
        other_journal = self.env['account.journal'].create({
            'name': 'Alt Sales Journal',
            'type': 'sale',
            'code': 'ALTSJ',
        })
        move = self._make_invoice(journal_id=other_journal.id)
        move_as_simple = move.with_user(self.simple_user)
        self.assertTrue(move_as_simple.is_simple_invoicing_view)
        move_as_simple.read(['journal_id'])
        self.assertEqual(move.journal_id, other_journal)

    # -- spec 10: group hides menu items/fields for members, unchanged for non-members --

    def test_simple_user_has_reduced_menu(self):
        Menu = self.env['ir.ui.menu'].with_user(self.simple_user)
        visible = set(Menu._visible_menu_ids())
        for xmlid in (
            'account.menu_finance_entries',
            'account.menu_finance_reports',
            'account.menu_finance_configuration',
        ):
            self.assertNotIn(self.env.ref(xmlid).id, visible)

    def test_plain_billing_user_menu_unaffected(self):
        # regression (spec 10): the override only ever filters for
        # simple_invoicing_group members, so a plain Billing user (not a
        # member) must see exactly what core account already grants,
        # including the menus that get hidden from simple-mode users.
        visible = set(self.env['ir.ui.menu'].with_user(self.plain_user)._visible_menu_ids())
        self.assertIn(self.env.ref('account.menu_finance_reports').id, visible)

    def test_simple_user_sees_simplified_fields_hidden(self):
        move = self._make_invoice()
        self.assertTrue(move.with_user(self.simple_user).is_simple_invoicing_view)

    def test_plain_user_sees_full_form(self):
        move = self._make_invoice()
        self.assertFalse(move.with_user(self.plain_user).is_simple_invoicing_view)

    # -- spec 9 / 10: Accountant-group-wins precedence, actually tested --

    def test_accountant_wins_precedence(self):
        move = self._make_invoice()
        self.assertFalse(move.with_user(self.dual_user).is_simple_invoicing_view)

        # dual_user (simple + manager) must see at least everything a
        # manager-only user sees -- the hide list must never apply to them.
        # (Can't assert the 3 hidden xmlids are visible outright: on a bare
        # `account` install, even group_account_manager alone doesn't carry
        # account.group_account_readonly, so those menus are natively
        # invisible to managers too, independent of this module.)
        manager_only = self.env['res.users'].create({
            'name': 'Manager Only',
            'login': 'manager_only_test_user_it',
            'email': 'manager_only_test_user_it@example.com',
            'group_ids': [(6, 0, [self.manager_group.id])],
        })
        visible_manager_only = set(self.env['ir.ui.menu'].with_user(manager_only)._visible_menu_ids())
        visible_dual = set(self.env['ir.ui.menu'].with_user(self.dual_user)._visible_menu_ids())
        self.assertTrue(visible_manager_only.issubset(visible_dual))

    # -- spec 10: Mark as Sent posts + emails in one action --

    def test_mark_as_sent_posts_and_sends(self):
        move = self._make_invoice()
        self.assertEqual(move.state, 'draft')
        message_count_before = len(move.message_ids)
        move.action_simple_mark_as_sent()
        self.assertEqual(move.state, 'posted')
        self.assertTrue(move.is_move_sent)
        self.assertGreater(len(move.message_ids), message_count_before)
        self.assertEqual(move.simple_status, 'sent')

    # -- spec 10: Record Payment opens the native wizard, pre-filled --

    def test_record_payment_opens_native_wizard(self):
        move = self._make_invoice()
        move.action_post()
        action = move.action_simple_register_payment()
        self.assertEqual(action['res_model'], 'account.payment.register')
        # native action_register_payment pre-fills via the move's *lines*,
        # not the move itself (account.move.line.action_register_payment)
        self.assertEqual(action['context']['active_model'], 'account.move.line')
        self.assertTrue(set(action['context']['active_ids']).issubset(set(move.line_ids.ids)))

    # -- simple mode is on by default, both for new companies and (via the
    # post_init_hook) for the company that already existed at install time --

    def test_simple_invoicing_mode_defaults_to_true_for_new_company(self):
        company = self.env['res.company'].create({'name': 'Fresh Co'})
        self.assertTrue(company.simple_invoicing_mode)

    # -- spec 4.1: company toggle syncs group membership --

    def test_company_toggle_syncs_group_membership(self):
        company = self.env.company
        user = self.env['res.users'].create({
            'name': 'Company Toggle User',
            'login': 'company_toggle_test_user',
            'email': 'company_toggle_test_user@example.com',
            'company_id': company.id,
            'company_ids': [(4, company.id)],
        })
        self.assertNotIn(user, self.simple_group.user_ids)
        company.write({'simple_invoicing_mode': True})
        self.assertIn(user, self.simple_group.user_ids)
        company.write({'simple_invoicing_mode': False})
        self.assertNotIn(user, self.simple_group.user_ids)

    # -- spec 7.6: dashboard aggregation --

    def test_dashboard_aggregation(self):
        overdue_move = self._make_invoice(invoice_date_due=fields.Date.today() - timedelta(days=3))
        overdue_move.action_post()
        paid_move = self._make_invoice()
        paid_move.action_post()
        self._register_payment(paid_move)

        dashboard = self.env['bs.simple.invoice.dashboard'].create({})
        self.assertGreaterEqual(dashboard.awaiting_payment_count, 1)
        self.assertGreaterEqual(dashboard.amount_overdue, 100.0)
        self.assertGreaterEqual(dashboard.amount_collected_this_month, 100.0)
