from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestWinRate(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.won_stage = cls.env.ref('crm.stage_lead4')
        cls.reason = cls.env['crm.lost.reason'].create({'name': 'Pricing (test)', 'category': 'pricing'})

    def test_zero_leads_returns_false(self):
        domain = [('name', '=', 'Nonexistent Test Lead XYZ')]
        self.assertFalse(self.env['crm.lead'].get_win_rate(domain))

    def test_pending_only_returns_false(self):
        lead = self.env['crm.lead'].create({'name': 'Still Open Test Lead'})
        self.assertFalse(self.env['crm.lead'].get_win_rate([('id', '=', lead.id)]))

    def test_mixed_won_lost_ratio(self):
        won_leads = self.env['crm.lead'].create([{'name': 'Won 1'}, {'name': 'Won 2'}, {'name': 'Won 3'}])
        won_leads.write({'stage_id': self.won_stage.id, 'probability': 100})
        lost_lead = self.env['crm.lead'].create({'name': 'Lost 1'})
        lost_lead.action_set_lost(lost_reason_id=self.reason.id)

        domain = [('id', 'in', (won_leads + lost_lead).ids)]
        win_rate = self.env['crm.lead'].get_win_rate(domain)
        self.assertAlmostEqual(win_rate, 75.0)
