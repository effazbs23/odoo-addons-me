# -*- coding: utf-8 -*-
"""Unit-level coverage of the optional whole-phrase fuzzy-match safety net
(KpiPromptParser._fuzzy_match_pass / _fuzzy_whole_phrase_span / _similarity).

Deliberately isolated from the module's own seed vocabulary (own synonym
fixtures created per test) so these don't drift if synonym_data.xml
changes later, and so the exact edit-distance arithmetic below can be
hand-verified rather than depending on how synonym_data.xml's phrases
happen to tokenize.
"""
from odoo.tests import TransactionCase, tagged

from ..logic.kpi_prompt_parser import KpiPromptParser, FUZZY_MATCH_CONFIG_PARAM


@tagged('post_install', '-at_install')
class TestSimilarityHelper(TransactionCase):
    """_similarity vendors the same ratio rapidfuzz.fuzz.ratio would give
    (no rapidfuzz dependency in the base module) — these numbers are
    hand-computed, not just "whatever the code happens to return".
    """

    def setUp(self):
        super().setUp()
        self.parser = KpiPromptParser(self.env)

    def test_identical_strings_are_1(self):
        self.assertEqual(self.parser._similarity('bar chart', 'bar chart'), 1.0)

    def test_both_empty_is_1(self):
        self.assertEqual(self.parser._similarity('', ''), 1.0)

    def test_one_edit_on_a_nine_char_string_is_above_default_threshold(self):
        # 'quantity' (8) -> 'quantitty' (9, one inserted 't'): edit
        # distance 1, similarity = 1 - 1/9 = 0.8889 >= 0.86.
        ratio = self.parser._similarity('quantity', 'quantitty')
        self.assertAlmostEqual(ratio, 1 - 1 / 9, places=4)
        self.assertGreaterEqual(ratio, KpiPromptParser._FUZZY_PHRASE_SIMILARITY_THRESHOLD)

    def test_transposition_on_a_short_word_stays_below_default_threshold(self):
        # 'region' vs 'regoin': a transposition costs 2 under plain
        # Levenshtein (no transposition discount) -> 1 - 2/6 = 0.667,
        # comfortably below the conservative 0.86 default — proof the
        # default threshold does NOT treat this as a match.
        ratio = self.parser._similarity('region', 'regoin')
        self.assertAlmostEqual(ratio, 1 - 2 / 6, places=4)
        self.assertLess(ratio, KpiPromptParser._FUZZY_PHRASE_SIMILARITY_THRESHOLD)


@tagged('post_install', '-at_install')
class TestFuzzyMatchPass(TransactionCase):

    def setUp(self):
        super().setUp()
        self.ICP = self.env['ir.config_parameter'].sudo()
        self.ICP.set_param(FUZZY_MATCH_CONFIG_PARAM, 'False')

        Synonym = self.env['ai.dashboard.synonym']
        sale_model = self.env.ref('sale.model_sale_order')
        # 'quantitty' (typo'd leftover text below) is a clean one-edit
        # near-miss for this phrase — see TestSimilarityHelper above.
        self.syn_measure = Synonym.create({
            'phrase': 'quantity', 'slot_type': 'measure',
            'model_id': sale_model.id, 'value': 'qty:sum',
        })
        self.syn_chart_bar = Synonym.create({
            'phrase': 'bar chart', 'slot_type': 'chart_type', 'value': 'bar',
        })
        # 'regoin' (typo'd leftover text below) is the hand-verified
        # below-threshold transposition case from TestSimilarityHelper.
        self.syn_groupby_region = Synonym.create({
            'phrase': 'region', 'slot_type': 'groupby',
            'model_id': sale_model.id, 'value': 'team_id',
        })
        self.parser = KpiPromptParser(self.env)

    def test_disabled_by_default_is_a_pure_passthrough(self):
        matches_in = [{'slot_type': 'chart_type', 'model_name': None,
                       'value': 'pie', 'phrase': 'pie chart'}]
        matches_out, text_out = self.parser._fuzzy_match_pass(matches_in, 'quantitty')
        self.assertEqual(matches_out, matches_in)
        self.assertEqual(text_out, 'quantitty')

    def test_enabled_fills_a_slot_step_one_left_completely_empty(self):
        self.ICP.set_param(FUZZY_MATCH_CONFIG_PARAM, 'True')
        matches, _ = self.parser._fuzzy_match_pass([], 'quantitty')
        measure_matches = [m for m in matches if m['slot_type'] == 'measure']
        self.assertEqual(len(measure_matches), 1)
        self.assertEqual(measure_matches[0]['value'], 'qty:sum')

    def test_enabled_never_adds_a_second_match_for_an_already_filled_singular_slot(self):
        self.ICP.set_param(FUZZY_MATCH_CONFIG_PARAM, 'True')
        # chart_type is already resolved (by the exact pass, in the real
        # pipeline) to 'pie' — 'bar chart' must not sneak in and compete
        # with it even though the leftover text is an exact match for it.
        already = [{'slot_type': 'chart_type', 'model_name': None,
                    'value': 'pie', 'phrase': 'pie chart'}]
        matches, _ = self.parser._fuzzy_match_pass(already, 'bar chart')
        chart_matches = [m for m in matches if m['slot_type'] == 'chart_type']
        self.assertEqual(len(chart_matches), 1)
        self.assertEqual(chart_matches[0]['value'], 'pie')

    def test_enabled_does_not_duplicate_an_already_present_value(self):
        self.ICP.set_param(FUZZY_MATCH_CONFIG_PARAM, 'True')
        already = [{'slot_type': 'measure', 'model_name': 'sale.order',
                    'value': 'qty:sum', 'phrase': 'quantity'}]
        matches, _ = self.parser._fuzzy_match_pass(already, 'quantitty')
        measure_matches = [m for m in matches if m['slot_type'] == 'measure']
        self.assertEqual(len(measure_matches), 1)  # not two

    def test_below_threshold_leftover_text_matches_nothing(self):
        self.ICP.set_param(FUZZY_MATCH_CONFIG_PARAM, 'True')
        matches, text = self.parser._fuzzy_match_pass([], 'regoin')
        self.assertEqual(matches, [])
        self.assertEqual(text, 'regoin')
