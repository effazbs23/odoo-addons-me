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


@tagged('post_install', '-at_install')
class TestWinRateDashboardData(TransactionCase):
    """get_win_rate_dashboard_data() backs the custom OWL dashboard - no
    JS test harness here, so this is the one server-side check that its
    aggregation logic (funnel, lost-reason breakdown, per-salesperson
    rate) doesn't error and produces sane numbers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.won_stage = cls.env.ref('crm.stage_lead4')
        cls.qualified_stage = cls.env.ref('crm.stage_lead2')
        cls.reason = cls.env['crm.lost.reason'].create({'name': 'Pricing (test)', 'category': 'pricing'})
        cls.salesperson = cls.env['res.users'].create({
            'name': 'Dashboard Test Salesperson', 'login': 'dashboard_test_salesperson',
        })

        won = cls.env['crm.lead'].create({'name': 'Dash Won 1', 'user_id': cls.salesperson.id})
        won.write({'stage_id': cls.won_stage.id, 'probability': 100})
        lost = cls.env['crm.lead'].create({'name': 'Dash Lost 1', 'stage_id': cls.qualified_stage.id, 'user_id': cls.salesperson.id})
        lost.action_set_lost(lost_reason_id=cls.reason.id)
        cls.env['crm.lead'].create({'name': 'Dash Pending 1', 'stage_id': cls.qualified_stage.id, 'user_id': cls.salesperson.id})

    def test_filters_include_seeded_salesperson(self):
        filters = self.env['crm.lead'].get_win_rate_dashboard_filters()
        self.assertIn(self.salesperson.id, [u['id'] for u in filters['salespeople']])

    def test_dashboard_data_shape_and_totals(self):
        data = self.env['crm.lead'].get_win_rate_dashboard_data(date_range='all', user_id=self.salesperson.id)
        self.assertEqual(data['won'], 1)
        self.assertEqual(data['lost'], 1)
        self.assertAlmostEqual(data['win_rate'], 50.0)
        self.assertEqual(sum(r['count'] for r in data['lost_reasons']), 1)
        self.assertTrue(any(sp['id'] == self.salesperson.id for sp in data['salespeople']))
        won_row = next(r for r in data['funnel'] if r['label'] == 'Won')
        lost_row = next(r for r in data['funnel'] if r['label'] == 'Lost')
        self.assertEqual(won_row['count'], 1)
        self.assertEqual(lost_row['count'], 1)
        # 3 leads total (won + lost + pending) for this salesperson
        self.assertEqual(sum(s['count'] for s in data['sources']), 3)

    def test_dashboard_data_empty_period_no_crash(self):
        data = self.env['crm.lead'].get_win_rate_dashboard_data(date_range='last_7', user_id=self.env['res.users'].create({
            'name': 'Nobody Test User', 'login': 'nobody_test_user',
        }).id)
        self.assertFalse(data['win_rate'])
        self.assertEqual(data['won'], 0)
        self.assertEqual(data['lost'], 0)
        self.assertEqual(data['lost_reasons'], [])
        self.assertEqual(data['salespeople'], [])
