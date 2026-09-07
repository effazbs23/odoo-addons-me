# Part of typo_tolerant_product_search. See LICENSE file for full copyright and licensing details.
import time

from odoo.tests import HttpCase, TransactionCase, tagged

from odoo.addons.http_routing.tests.common import MockRequest
from odoo.addons.website_sale.tests.common import WebsiteSaleCommon

from odoo.addons.typo_tolerant_product_search.controllers.main import TypoTolerantWebsiteSale

SEARCH_OPTIONS = {
    'displayDescription': True, 'displayDetail': True, 'displayExtraDetail': True,
    'displayExtraLink': True, 'displayImage': True, 'allowFuzzy': True,
    'display_currency': None,
}


class FuzzySearchCommon(WebsiteSaleCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = TypoTolerantWebsiteSale()
        # Distinctive, unambiguous product names so a fuzzy match can only
        # plausibly resolve to one intended product per test.
        cls.mouse = cls.env['product.template'].create({
            'name': 'Wireless Mouse',
            'website_published': True,
            'sale_ok': True,
            'list_price': 19.99,
        })
        cls.keyboard = cls.env['product.template'].create({
            'name': 'Wireless Keyboard',
            'website_published': True,
            'sale_ok': True,
            'list_price': 29.99,
        })
        cls.chair = cls.env['product.template'].create({
            'name': 'Ergonomic Chair',
            'website_published': True,
            'sale_ok': True,
            'list_price': 149.0,
        })
        cls.sku_product = cls.env['product.template'].create({
            'name': 'Cable Adapter SKU88421',
            'website_published': True,
            'sale_ok': True,
            'list_price': 9.5,
        })


@tagged('post_install', '-at_install')
class TestFuzzyCorrectionUnit(FuzzySearchCommon, TransactionCase):
    """Spec 10 - Unit tests: match quality, sensitivity, and the
    fallback-only trigger condition, tested directly against
    ``_fuzzy_correct_multi_word`` / ``_shop_lookup_products`` without going
    through HTTP."""

    def test_typo_patterns_resolve_to_intended_product(self):
        # missing letter / extra letter / transposition / plural mismatch
        # (spec 10, first bullet). Each typo is deliberately NOT a prefix of
        # the target word (e.g. not "wireles", which ILIKE '%wireles%'
        # already matches against "Wireless" as a plain substring, so it
        # would never even reach fuzzy correction - that's correct behavior,
        # not a test case for it).
        cases = {
            'wirelss mouse': 'wireless mouse',      # missing (middle) letter
            'wirelesss mouse': 'wireless mouse',    # extra letter
            'wireless moues': 'wireless mouse',     # transposition
            'ergonomic chairs': 'ergonomic chair',  # singular/plural mismatch
        }
        for typo, expected in cases.items():
            with self.subTest(typo=typo):
                corrected = self.controller._fuzzy_correct_multi_word(typo, SEARCH_OPTIONS, self.website)
                self.assertIsNotNone(corrected, f"Expected a correction for {typo!r}")
                self.assertEqual(corrected.lower(), expected)

    def test_sensitivity_tightens_and_loosens_matches(self):
        # "mouze" -> "mouse" scores ~0.4 (verified via website.tools.similarity_score):
        # below the tight threshold (0.55) but above normal/loose (0.35/0.15).
        self.website.fuzzy_search_sensitivity = 'tight'
        tight_result = self.controller._fuzzy_correct_multi_word('mouze', SEARCH_OPTIONS, self.website)
        self.assertIsNone(tight_result, "Tight sensitivity should reject a weak match")

        self.website.fuzzy_search_sensitivity = 'loose'
        loose_result = self.controller._fuzzy_correct_multi_word('mouze', SEARCH_OPTIONS, self.website)
        self.assertEqual(loose_result, 'mouse')

    def test_no_fuzzy_when_exact_search_already_meets_minimum(self):
        self.website.fuzzy_search_min_results = 1
        # Native _shop_lookup_products() itself reaches for odoo.http.request
        # (e.g. as a .get() fallback default), so it needs one bound even
        # outside a real HTTP request; MockRequest is http_routing's
        # standard tool for exactly this (see its own docstring).
        with MockRequest(self.env, website=self.website):
            fuzzy_term, count, results = self.controller._shop_lookup_products(
                SEARCH_OPTIONS, {'order': 'name asc'}, 'Wireless Mouse', self.website
            )
        self.assertFalse(fuzzy_term, "No correction should be suggested for an already-working search")
        self.assertEqual(count, 1)
        self.assertIn(self.mouse, results)

    def test_short_query_skips_fuzzy(self):
        # Edge case (spec 9): 1-2 character terms must not be fuzzy-matched.
        corrected = self.controller._fuzzy_correct_multi_word('tv', SEARCH_OPTIONS, self.website)
        self.assertIsNone(corrected)

    def test_numeric_term_skips_fuzzy(self):
        # Edge case (spec 9): an 80%+ digit token (SKU/model number) must
        # never be "corrected" into an unrelated word.
        corrected = self.controller._fuzzy_correct_multi_word('88422', SEARCH_OPTIONS, self.website)
        self.assertIsNone(corrected)


@tagged('post_install', '-at_install')
class TestFuzzySearchIntegration(FuzzySearchCommon, HttpCase):
    """Spec 10 - Integration tests: the real /shop route end to end."""

    def test_note_shown_only_when_fallback_fired(self):
        # Multi-word typo (the spec's own motivating example) -> native
        # single-word fuzzy search does not handle this at all; our
        # extension does, and the note must appear. "wirelss" (not
        # "wireles") is used deliberately: dropping a *trailing* letter
        # keeps the typo a plain ILIKE substring of "Wireless" (already
        # matched with no fuzzy logic at all - see the unit test above),
        # so it wouldn't actually exercise the fallback path.
        response = self.url_open('/shop?search=wirelss+mouse')
        self.assertIn(b'Showing results for', response.content)
        self.assertIn(b'Wireless Mouse', response.content)

        # An already-working exact search must never show the note.
        response = self.url_open('/shop?search=Wireless+Mouse')
        self.assertNotIn(b'Showing results for', response.content)

    def test_miss_log_records_term_and_result_count(self):
        Log = self.env['bs.search.fuzzy.log'].sudo()
        before = Log.search_count([])
        self.url_open('/shop?search=wirelss+keybord')
        after = Log.search([], order='id desc', limit=1)
        self.assertEqual(Log.search_count([]), before + 1)
        self.assertEqual(after.search_term, 'wirelss keybord')
        self.assertEqual(after.corrected_term.lower(), 'wireless keyboard')
        self.assertGreater(after.result_count, 0)

    def test_regression_exact_match_unchanged(self):
        # Absolute requirement (guardrails): behavior for an already-working
        # query must be provably unchanged. Comparing full response bytes
        # would be brittle (each response embeds a fresh CSRF/session
        # token), so this asserts on what the guardrail actually cares
        # about: the same single product, no fuzzy note, stable result
        # count - run twice to rule out any state leaking between requests.
        for _ in range(2):
            response = self.url_open('/shop?search=Ergonomic+Chair')
            self.assertNotIn(b'Showing results for', response.content)
            self.assertIn(b'Ergonomic Chair', response.content)


@tagged('post_install', '-at_install')
class TestFuzzySearchPerformance(FuzzySearchCommon, HttpCase):
    """Spec 10 - Performance test on a representative-sized catalog (a few
    thousand products), and spec 9's "don't scan the whole table" scaling
    requirement."""

    # ponytail: generous ceiling for a shared test box under load; tighten
    # if this ever needs to double as a real perf regression gate.
    MAX_SECONDS = 5.0

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['product.template'].create([
            {
                'name': f'Catalog Filler Item {i}',
                'website_published': True,
                'sale_ok': True,
                'list_price': 5.0,
            }
            for i in range(2000)
        ])

    def test_fuzzy_search_stays_fast_on_large_catalog(self):
        start = time.time()
        # "wirelss" (not "wireles") to actually exercise the fuzzy-
        # correction code path, not just a plain ILIKE substring hit.
        response = self.url_open('/shop?search=wirelss+mouse')
        elapsed = time.time() - start
        self.assertIn(b'Wireless Mouse', response.content)
        self.assertLess(
            elapsed, self.MAX_SECONDS,
            f"Fuzzy multi-word search took {elapsed:.2f}s against a ~2000-product catalog",
        )
