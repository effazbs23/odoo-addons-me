# Part of bs_typo_tolerant_product_search. See LICENSE file for full copyright and licensing details.
import logging
import re

from odoo.http import request, route

from odoo.addons.website.tools import similarity_score
from odoo.addons.website_sale.controllers.main import WebsiteSale

_logger = logging.getLogger(__name__)


class TypoTolerantWebsiteSale(WebsiteSale):
    """Extends the native storefront product search with word-by-word fuzzy
    correction for multi-word queries, a configurable sensitivity gate, and
    search-miss logging.

    Odoo 19 core (``website``/``website_sale``) already ships a fuzzy-search
    engine: ``Website._search_with_fuzzy()`` is called from
    ``_shop_lookup_products()`` below and already resolves the trigram-vs-
    Python decision internally (``registry.has_trigram`` -> pg_trgm GIST
    index lookup, else a pre-filtered Python edit-distance scan - see
    ``Website._trigram_enumerate_words`` / ``_basic_enumerate_words``). This
    override deliberately reuses those primitives rather than reimplementing
    a matching engine (see context.md "Key decisions").

    The one real gap core leaves open: ``Website._search_find_fuzzy_term()``
    explicitly refuses to correct any query containing a space, so a
    two-word typo such as "wireles mouse" (the spec's own motivating
    example) never gets a native suggestion at all. That's what this class
    adds.
    """

    # Sensitivity mapping (spec 6/7.3): minimum `similarity_score()` (see
    # odoo.addons.website.tools.similarity_score, ranges up to 1.0 for
    # identical strings) required to accept a per-word fuzzy correction.
    # Native core applies NO minimum at all - it always takes the single
    # best-scoring candidate, however weak. These are named, adjustable
    # constants (not scattered magic numbers) so tight/normal/loose have one
    # place to tune.
    FUZZY_SENSITIVITY_THRESHOLDS = {
        'tight': 0.55,
        'normal': 0.35,
        'loose': 0.15,
    }
    FUZZY_SENSITIVITY_DEFAULT = 'normal'

    # Edge case (spec 9 - very short search terms): a word shorter than this
    # is too short to fuzzy-match meaningfully (mirrors core's own 4-char
    # single-word cutoff in Website._search_find_fuzzy_term) - fuzzy-
    # matching "TV" against the whole catalog produces noise, not signal.
    FUZZY_MIN_WORD_LENGTH = 4

    # Edge case (spec 9 - legitimately correct but rare / numeric terms):
    # a word that's 80%+ digits is almost certainly a SKU/model number,
    # where a wrong fuzzy guess is worse than no results at all. Mirrors the
    # same 80%-digits guard core applies for single-word queries.
    FUZZY_MAX_DIGIT_RATIO = 0.8

    def _shop_lookup_products(self, options, post, search, website):
        # Fallback Only, Never a Replacement (spec 4.4): the exact/substring
        # search (including core's own single-word fuzzy attempt) always
        # runs first, completely unmodified.
        fuzzy_search_term, product_count, search_result = super()._shop_lookup_products(
            options, post, search, website
        )

        min_results = website.fuzzy_search_min_results or 1
        # Structural regression guarantee (not just tested): whenever the
        # native call above already clears the configured minimum, this
        # override is a no-op and returns native's own results/ranking
        # untouched - it never re-queries or re-scores anything.
        if not search or not options.get('allowFuzzy', True) or product_count >= min_results:
            return fuzzy_search_term, product_count, search_result

        corrected_search = self._fuzzy_correct_multi_word(search, options, website)

        final_fuzzy_term = fuzzy_search_term
        log_result_count = product_count
        if corrected_search and corrected_search.lower() != search.lower():
            # Edge case (spec 9 - search abuse/performance): this second
            # pass calls `super()` directly, not `self`, so it re-enters
            # native code only - never this override again. There is no
            # recursion and at most one extra native search per request, the
            # same cost order as core's own single-word fuzzy attempt above -
            # this extension doesn't give a scraper a cheaper way to load the
            # DB than native search already allows.
            __, widened_count, widened_result = super()._shop_lookup_products(
                options, post, corrected_search, website
            )
            # Results merging (spec 7.4): replace, never append, and only
            # when it's an actual improvement, so a bad guess can't make an
            # already-working (if sparse) result set worse.
            if widened_count > product_count:
                final_fuzzy_term = corrected_search
                log_result_count = widened_count
                search_result = widened_result
                product_count = widened_count

        # Search Term Miss Log (spec 5/6): only log when a correction
        # actually fired - never for a legitimately-correct-but-rare term
        # that just happens to have few/no results (spec 9).
        if final_fuzzy_term:
            self._log_fuzzy_search_miss(search, final_fuzzy_term, log_result_count)

        return final_fuzzy_term, product_count, search_result

    def _fuzzy_correct_multi_word(self, search, options, website):
        """Word-by-word fuzzy correction for multi-word queries (the real
        gap left open by core - see class docstring). Reuses
        ``Website._search_find_fuzzy_term()`` per word, which itself reuses
        core's pg_trgm/Python pre-filtered candidate lookup - no full-table
        scan is introduced here (spec 9 - large catalogs)."""
        # Edge case (spec 9 - multi-language catalogs): word-splitting on a
        # literal space is a Latin/space-delimited-script assumption. For a
        # space-less script (e.g. CJK) this degrades to treating the whole
        # query as one "word", which usually exceeds core's underlying
        # per-word matching sweet spot and yields fewer/no corrections
        # rather than a wrong one - a documented limitation, not a silent
        # failure: character-level similarity_score() still runs and the
        # sensitivity gate still applies, it just won't split a mistyped
        # multi-word CJK phrase the way it does for space-delimited scripts.
        words = search.split(' ')
        # Edge case (spec 9 - very short terms): nothing worth correcting.
        if not any(len(word) >= self.FUZZY_MIN_WORD_LENGTH for word in words):
            return None

        threshold = self.FUZZY_SENSITIVITY_THRESHOLDS.get(
            website.fuzzy_search_sensitivity, self.FUZZY_SENSITIVITY_THRESHOLDS[self.FUZZY_SENSITIVITY_DEFAULT]
        )
        search_details = website._search_get_details('products_only', 'name asc', options)

        corrected_words = []
        changed = False
        for word in words:
            lower_word = word.lower()
            digit_ratio = (len(re.findall(r'\d', lower_word)) / len(lower_word)) if lower_word else 0
            if len(lower_word) < self.FUZZY_MIN_WORD_LENGTH or digit_ratio >= self.FUZZY_MAX_DIGIT_RATIO:
                corrected_words.append(word)
                continue
            candidate = website._search_find_fuzzy_term(search_details, lower_word)
            if candidate and candidate != lower_word:
                score = similarity_score(lower_word, candidate)
                # Sensitivity gate: the one thing core doesn't do at all.
                if score >= threshold:
                    corrected_words.append(candidate)
                    changed = True
                    continue
            corrected_words.append(word)

        return ' '.join(corrected_words) if changed else None

    def _log_fuzzy_search_miss(self, search_term, corrected_term, result_count):
        """Best-effort, non-blocking (spec 6/11): a logging failure must
        never prevent search results from rendering, so any error here is
        caught and only logged server-side."""
        try:
            log = request.env['bs.search.fuzzy.log'].sudo().create({
                'search_term': search_term,
                'corrected_term': corrected_term,
                'result_count': result_count,
            })
            request.fuzzy_search_log_id = log.id
        except Exception:
            _logger.warning('bs_typo_tolerant_product_search: failed to log fuzzy search miss', exc_info=True)

    @route('/shop/fuzzy_search/click/<int:log_id>', type='http', auth='public', website=True,
           sitemap=False, csrf=False, methods=['GET', 'POST'])
    def fuzzy_search_log_click(self, log_id, **kwargs):
        """Best-effort click tracking (spec 6): fired fire-and-forget by a
        tiny JS asset when a visitor clicks a product on a fuzzy-fallback
        results page. Never raises - a tracking failure must not affect the
        visitor's navigation."""
        try:
            request.env['bs.search.fuzzy.log'].sudo().browse(log_id).write({'clicked': True})
        except Exception:
            _logger.warning('bs_typo_tolerant_product_search: failed to record fuzzy search click', exc_info=True)
        return request.make_json_response({'ok': True})
