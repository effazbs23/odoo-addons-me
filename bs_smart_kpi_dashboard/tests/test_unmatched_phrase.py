# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged

from ..controllers.main import SmartKpiDashboardController


@tagged('post_install', '-at_install')
class TestUnmatchedPhraseLogging(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Unmatched = self.env['ai.dashboard.unmatched_phrase']

    def test_noise_phrase_is_skipped(self):
        row = self.Unmatched.log_unmatched('by the')
        self.assertFalse(row)
        self.assertEqual(self.Unmatched.search_count([('phrase', '=', 'by the')]), 0)

    def test_too_short_phrase_is_skipped(self):
        row = self.Unmatched.log_unmatched('x')
        self.assertFalse(row)

    def test_creates_a_new_row(self):
        row = self.Unmatched.log_unmatched('total widgets shipped')
        self.assertTrue(row)
        self.assertEqual(row.phrase, 'total widgets shipped')
        self.assertEqual(row.hit_count, 1)
        self.assertEqual(row.state, 'new')

    def test_repeat_bumps_hit_count_instead_of_duplicating(self):
        first = self.Unmatched.log_unmatched('total widgets shipped')
        second = self.Unmatched.log_unmatched('total widgets shipped')
        self.assertEqual(first.id, second.id)
        self.assertEqual(second.hit_count, 2)
        self.assertEqual(
            self.Unmatched.search_count([('phrase', '=', 'total widgets shipped')]), 1)

    def test_dismissed_row_does_not_absorb_further_hits(self):
        row = self.Unmatched.log_unmatched('total widgets shipped')
        row.action_dismiss()
        self.assertEqual(row.state, 'dismissed')
        again = self.Unmatched.log_unmatched('total widgets shipped')
        self.assertNotEqual(row.id, again.id)
        self.assertEqual(again.hit_count, 1)

    def test_candidate_model_resolved_when_given(self):
        row = self.Unmatched.log_unmatched('total widgets shipped', 'sale.order')
        self.assertEqual(row.candidate_model.model, 'sale.order')

    def test_candidate_model_empty_when_not_given(self):
        row = self.Unmatched.log_unmatched('total widgets shipped')
        self.assertFalse(row.candidate_model)

    def test_action_create_synonym_prefills_and_marks_reviewed(self):
        row = self.Unmatched.log_unmatched('total widgets shipped', 'sale.order')
        action = row.action_create_synonym()
        self.assertEqual(row.state, 'reviewed')
        self.assertEqual(action['res_model'], 'ai.dashboard.synonym')
        self.assertEqual(action['context']['default_phrase'], 'total widgets shipped')
        self.assertEqual(
            action['context']['default_model_id'], row.candidate_model.id)
        # Pure UI convenience — no synonym actually created by this call.
        self.assertFalse(self.env['ai.dashboard.synonym'].search(
            [('phrase', '=', 'total widgets shipped')]))


@tagged('post_install', '-at_install')
class TestControllerUnmatchedLoggingIsNonFatal(TransactionCase):
    """Constraint 1 from the task spec: a telemetry failure must never
    break the guided-form response. _log_unmatched_phrase is a
    @staticmethod taking `env` explicitly, precisely so it's testable
    with no HTTP request/registry lookup required.
    """

    def setUp(self):
        super().setUp()
        self.Unmatched = self.env['ai.dashboard.unmatched_phrase']

    def test_happy_path_logs_a_row(self):
        spec = {'leftover_text': 'total widgets shipped', 'model': None}
        SmartKpiDashboardController._log_unmatched_phrase(self.env, spec)
        self.assertEqual(
            self.Unmatched.search_count([('phrase', '=', 'total widgets shipped')]), 1)

    def test_blank_leftover_text_logs_nothing(self):
        spec = {'leftover_text': '   ', 'model': None}
        SmartKpiDashboardController._log_unmatched_phrase(self.env, spec)
        self.assertEqual(self.Unmatched.search_count([]), 0)

    def test_missing_leftover_text_key_logs_nothing_and_does_not_raise(self):
        SmartKpiDashboardController._log_unmatched_phrase(self.env, {})
        self.assertEqual(self.Unmatched.search_count([]), 0)

    def test_exception_inside_logging_is_swallowed(self):
        def _boom(*args, **kwargs):
            raise RuntimeError("simulated failure — bad field name, DB hiccup, etc.")

        # Patch the exact call _log_unmatched_phrase makes, at the class
        # the registry serves requests through, so this proves the SAME
        # code path a real failure would hit is caught.
        Model = self.env.registry['ai.dashboard.unmatched_phrase']
        self.patch(Model, 'log_unmatched', _boom)

        spec = {'leftover_text': 'total widgets shipped', 'model': None}
        # The whole point of the try/except in _log_unmatched_phrase: this
        # must not raise, proving the guided-form response it precedes
        # would still be returned to the user.
        SmartKpiDashboardController._log_unmatched_phrase(self.env, spec)

        self.assertEqual(self.Unmatched.search_count([]), 0)
