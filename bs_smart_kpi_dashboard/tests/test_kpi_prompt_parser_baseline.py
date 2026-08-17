# -*- coding: utf-8 -*-
"""Regression baseline for KpiPromptParser against the module's own seed
vocabulary (data/synonym_data.xml + data/allowlist_data.xml).

Every prompt exercised here resolved to a specific spec before this task
touched kpi_prompt_parser.py (the _synonym_domain() hook + the optional
fuzzy-match pass added in this task). These tests exist to prove that
work is additive: with the fuzzy-match config parameter left at its
default (unset / False), every one of these must keep resolving to
exactly the same spec as before. A failure here is a regression, full
stop, even if some other new feature "worked".
"""
from odoo.tests import TransactionCase, tagged

from ..logic.kpi_prompt_parser import KpiPromptParser, FUZZY_MATCH_CONFIG_PARAM


@tagged('post_install', '-at_install')
class TestKpiPromptParserBaseline(TransactionCase):

    def setUp(self):
        super().setUp()
        # Explicit, not assumed: prove the default really is "off".
        self.assertEqual(
            self.env['ir.config_parameter'].sudo().get_param(
                FUZZY_MATCH_CONFIG_PARAM, 'False'),
            'False',
            "fuzzy matching must default to OFF — a change to this "
            "default would silently break constraint 1 (zero behavior "
            "change for today's high-confidence prompts).")

    def _parse(self, prompt):
        return KpiPromptParser(self.env).parse(prompt)

    def test_revenue_by_region_this_quarter_bar_chart(self):
        spec = self._parse("revenue by region this quarter, bar chart")
        self.assertEqual(spec['model'], 'sale.order')
        self.assertEqual(spec['measures'], ['amount_total:sum'])
        self.assertIn('team_id', spec['groupby'])
        self.assertEqual(spec['chart_type'], 'bar')
        self.assertGreaterEqual(spec['confidence'], 0.5)

    def test_top_5_regions_by_total_sales(self):
        spec = self._parse("top 5 regions by total sales")
        self.assertEqual(spec['model'], 'sale.order')
        self.assertEqual(spec['measures'], ['amount_total:sum'])
        self.assertEqual(spec['limit'], 5)

    def test_expected_revenue_by_stage(self):
        spec = self._parse("expected revenue by stage")
        self.assertEqual(spec['model'], 'crm.lead')
        self.assertEqual(spec['measures'], ['expected_revenue:sum'])
        self.assertIn('stage_id', spec['groupby'])

    def test_quantity_by_product_by_month(self):
        spec = self._parse("quantity by product by month")
        self.assertEqual(spec['model'], 'stock.move')
        self.assertEqual(spec['measures'], ['product_qty:sum'])
        self.assertIn('product_id', spec['groupby'])

    def test_invoice_total_by_client_last_month(self):
        spec = self._parse("invoice total by client last month")
        self.assertEqual(spec['model'], 'account.move')
        self.assertEqual(spec['measures'], ['amount_total:sum'])
        self.assertIn('partner_id', spec['groupby'])

    def test_gibberish_prompt_falls_through_to_guided_form(self):
        spec = self._parse("zzz qqq flurbnorb")
        self.assertLess(spec['confidence'], 0.5)
        self.assertFalse(spec['measures'])
        self.assertEqual(spec['leftover_text'], 'zzz qqq flurbnorb')

    def test_full_pipeline_is_a_noop_whether_flag_is_absent_or_explicitly_false(self):
        """The config parameter may not exist yet on a fresh DB (get_param
        falls back to the default we pass) — confirm behavior is
        identical whether it's unset or explicitly 'False'."""
        prompt = "revenue by region this quarter, bar chart"
        spec_unset = self._parse(prompt)

        self.env['ir.config_parameter'].sudo().set_param(
            FUZZY_MATCH_CONFIG_PARAM, 'False')
        spec_explicit = self._parse(prompt)

        self.assertEqual(spec_unset, spec_explicit)
