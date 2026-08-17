# -*- coding: utf-8 -*-
"""Deterministic natural-language → query-spec parser.

No network calls, no ML dependency, nothing external. Coverage is a
function of the ai.dashboard.synonym table, not of this code — extend
vocabulary by adding rows, not by touching this file.

Design in three passes, on purpose:
  1. Consume every phrase in the prompt that matches ANY synonym, longest
     phrase first, regardless of which model it belongs to.
  2. Decide which MODEL the prompt is about (explicit "sales"/"invoices"
     mention, or — if none — vote by which model the matched measure/
     groupby phrases belong to).
  3. Re-filter step-1's matches down to only the ones consistent with the
     resolved model, then assemble the final spec.

Splitting model-resolution from slot-resolution like this is what lets a
prompt like "revenue by region this quarter" work without the word
"sales" ever appearing — "revenue" and "region" both happen to belong to
sale.order in the seed data, so the vote resolves the model implicitly.
"""
import re
from datetime import timedelta

from odoo import fields as odoo_fields
from odoo.tools import str2bool

TOP_N_RE = re.compile(r'\b(top|bottom)\s+(\d+)\b')
WORD_BOUNDARY = r'\b{}\b'
TOKEN_RE = re.compile(r'\S+')

FUZZY_MATCH_CONFIG_PARAM = 'bs_smart_kpi_dashboard.fuzzy_match_enabled'


def _levenshtein(a, b):
    """Plain DP edit distance — no external dependency, strings here are
    single words (a handful of characters), so O(len(a)*len(b)) is trivial.
    """
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[-1]


def _max_edits(word_len):
    """How many typos a word of this length may have and still count as a
    match. Short words stay exact-only — fuzzing a 2-3 letter word (e.g.
    'by') would swallow half the dictionary."""
    if word_len <= 3:
        return 0
    if word_len <= 5:
        return 1
    return 2


def _words_fuzzy_equal(a, b):
    if a == b:
        return True
    threshold = _max_edits(max(len(a), len(b)))
    return threshold > 0 and _levenshtein(a, b) <= threshold


class KpiPromptParser:

    def __init__(self, env):
        self.env = env
        # _synonym_domain() is the one hook an optional add-on (e.g. an AI-
        # assisted vocabulary-suggestion module) is meant to extend — see
        # its docstring. Everything else in this class is base-module-only.
        self._synonyms = env['ai.dashboard.synonym'].sudo().search(self._synonym_domain())
        self._allowlist = env['ai.dashboard.allowlist'].sudo().search([])
        self._allowlist_by_model = {a.model_name: a for a in self._allowlist}
        self._example_prompts_cache = None

    def _synonym_domain(self):
        """Which ai.dashboard.synonym rows this parser instance is allowed
        to match against. Empty domain == every active row (today's exact
        behavior — Odoo's own `active` field already excludes inactive/
        draft rows, e.g. auto-discovery drafts).

        An add-on that gives synonyms a review workflow (e.g. LLM-drafted
        suggestions awaiting human approval, tracked on a `state` field
        distinct from `active`) can override this single method to add
        `('state', '=', 'active')` — the ONLY change such an add-on should
        ever need to make to this file. Do not add matching logic here;
        this method only ever returns a search domain.
        """
        return []

    # ------------------------------------------------------------------ #
    # Public entry point
    # ------------------------------------------------------------------ #
    def parse(self, prompt):
        text = self._normalize(prompt)

        raw_matches, remaining_text = self._consume_matches(text)
        raw_matches, remaining_text = self._fuzzy_match_pass(raw_matches, remaining_text)
        model_name = self._resolve_model(raw_matches)

        spec = {
            'model': model_name,
            'groupby': [],
            'measures': [],
            'domain': [],
            'chart_type': None,
            'limit': None,
            'orderby': None,
        }

        if model_name:
            self._apply_model_scoped_matches(spec, raw_matches, model_name)

        # Score BEFORE any defaults are filled in — confidence must reflect
        # what the prompt actually gave us (e.g. bare "sales" resolves a
        # model but names no dimension or measure, so it must score low and
        # fall through to the guided form, not silently guess a measure).
        spec['confidence'] = self._score(spec)

        if model_name:
            # Default measure must be resolved before "top N" so a prompt
            # like "top 5 regions" (no explicit measure phrase) still
            # orders by the model's default measure, not arbitrarily.
            self._apply_default_measure(spec, model_name)
            self._apply_top_n(spec, remaining_text, model_name)
            self._apply_default_chart_type(spec)

        spec['leftover_text'] = remaining_text.strip()
        return spec

    # ------------------------------------------------------------------ #
    # Typeahead suggestions for the ask bar
    #
    # Built entirely from active vocabulary the current user can actually
    # use — same _synonyms/_allowlist this class already loads, so a
    # suggestion is never something the user would then hit a "not
    # allow-listed" / "no read access" error on. Nothing here is guessed;
    # every phrase either comes from an ai.dashboard.synonym row or, if a
    # field has no synonym yet, its own field label.
    # ------------------------------------------------------------------ #
    def suggest(self, prompt, limit=6):
        pool = self._example_prompts()
        text = (prompt or '').strip().lower()
        if not text:
            return pool[:limit]

        starts_with = [p for p in pool if p.lower().startswith(text)]
        if len(starts_with) >= limit:
            return starts_with[:limit]

        last_word = text.split()[-1] if text.split() else ''
        contains = []
        if last_word:
            pattern = WORD_BOUNDARY.format(re.escape(last_word))
            contains = [
                p for p in pool
                if p not in starts_with and re.search(pattern, p.lower())
            ]
        return (starts_with + contains)[:limit]

    def _example_prompts(self):
        """One-time-per-request build of ready-made prompts, one or two
        per queryable+readable model: '<measure> by <dimension>' and, if
        the model has a date field, the same with a time-range phrase
        appended."""
        if self._example_prompts_cache is not None:
            return self._example_prompts_cache

        time_phrases = ['this month', 'this quarter', 'this year']
        prompts = []
        for entry in self._allowlist:
            model_name = entry.model_name
            Model = self.env.get(model_name)
            if Model is None or not Model.has_access('read'):
                continue

            default_measure = entry.default_measure_spec()
            if not default_measure:
                continue
            measure_phrase = self._best_measure_phrase(
                model_name, default_measure, entry.default_measure_field_id)
            groupby_phrases = self._best_groupby_phrases(model_name, entry, limit=2)
            if not measure_phrase or not groupby_phrases:
                continue

            for gb_phrase in groupby_phrases:
                prompts.append(f"{measure_phrase} by {gb_phrase}")
            if entry.date_field_id:
                time_phrase = time_phrases[len(prompts) % len(time_phrases)]
                prompts.append(f"{measure_phrase} by {groupby_phrases[0]} {time_phrase}")

        self._example_prompts_cache = prompts
        return prompts

    def _best_measure_phrase(self, model_name, value, fallback_field):
        for syn in self._synonyms:
            if syn.slot_type == 'measure' and syn.model_name == model_name and syn.value == value:
                return syn.phrase
        return fallback_field.field_description.lower() if fallback_field else None

    def _best_groupby_phrases(self, model_name, entry, limit=2):
        """Up to `limit` distinct groupby phrases for this model — a
        synonym's phrase where one exists for an allow-listed field
        (self._synonyms is already priority-sorted, so the first synonym
        seen per field is its best one), the field's own label otherwise.
        """
        allowed = entry.allowed_field_names()
        phrase_by_field = {}
        for syn in self._synonyms:
            if syn.slot_type == 'groupby' and syn.model_name == model_name and syn.value in allowed:
                phrase_by_field.setdefault(syn.value, syn.phrase)

        phrases = list(phrase_by_field.values())
        if len(phrases) < limit:
            for f in entry.field_ids:
                if f.name in phrase_by_field:
                    continue
                phrases.append(f.field_description.lower())
                if len(phrases) >= limit:
                    break
        return phrases[:limit]

    # ------------------------------------------------------------------ #
    # Step 0: normalize
    # ------------------------------------------------------------------ #
    @staticmethod
    def _normalize(prompt):
        text = prompt.lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    # ------------------------------------------------------------------ #
    # Step 1: consume every phrase match, longest-first
    # ------------------------------------------------------------------ #
    def _consume_matches(self, text):
        matches = []
        # Longest phrase first so "this quarter" is claimed before a bare
        # "quarter" synonym (if one exists) gets a chance at it.
        ordered = sorted(self._synonyms, key=lambda s: (-len(s.phrase), -s.priority))
        for syn in ordered:
            pattern = WORD_BOUNDARY.format(re.escape(syn.phrase))
            m = re.search(pattern, text)
            span = (m.start(), m.end()) if m else self._fuzzy_span(text, syn.phrase)
            if not span:
                continue
            start, end = span
            matches.append({
                'slot_type': syn.slot_type,
                'model_name': syn.model_name or None,
                'value': syn.value,
                'phrase': syn.phrase,
            })
            # Blank out the matched span (keep length/spacing so later
            # matches' word boundaries aren't accidentally created/broken).
            text = text[:start] + (' ' * (end - start)) + text[end:]
        return matches, text

    @staticmethod
    def _fuzzy_span(text, phrase):
        """Typo-tolerant fallback for when the exact word-boundary regex
        finds nothing: slide a same-length word window across the text and
        accept it if every word is within its per-word edit-distance
        allowance of the synonym's word (see _max_edits). Catches things
        like 'revenu by regoin' without opening the door to matching
        unrelated short words."""
        phrase_words = phrase.split()
        k = len(phrase_words)
        tokens = list(TOKEN_RE.finditer(text))
        if len(tokens) < k:
            return None
        for i in range(len(tokens) - k + 1):
            window = tokens[i:i + k]
            if all(_words_fuzzy_equal(window[j].group(0), phrase_words[j])
                   for j in range(k)):
                return (window[0].start(), window[-1].end())
        return None

    # ------------------------------------------------------------------ #
    # Optional secondary pass: whole-phrase fuzzy matching.
    #
    # Off by default (kpi_dashboard_fuzzy_match_enabled in res.config.
    # settings / the bs_smart_kpi_dashboard.fuzzy_match_enabled config
    # parameter) — when disabled this is a single early-return and the
    # rest of parse() behaves byte-for-byte as it did before this pass
    # existed. When enabled, it only ever looks at `remaining_text`
    # (whatever step 1's exact + per-word-fuzzy pass left unmatched), so
    # it can never re-examine — let alone overturn — a span step 1 already
    # claimed. Within that leftover text it also refuses to add a second
    # match for any slot type step 1 already resolved a value for
    # (_FUZZY_SINGULAR_SLOTS) and refuses to add a duplicate (slot_type,
    # model, value) triple for the additive ones (measure/groupby) — so it
    # can only ever fill a slot step 1 left completely empty, never
    # compete with what step 1 found.
    # ------------------------------------------------------------------ #
    _FUZZY_SINGULAR_SLOTS = {'model', 'chart_type', 'sort', 'time_range', 'groupby_time'}
    _FUZZY_PHRASE_SIMILARITY_THRESHOLD = 0.86

    def _fuzzy_enabled(self):
        return str2bool(
            self.env['ir.config_parameter'].sudo().get_param(FUZZY_MATCH_CONFIG_PARAM, 'False'))

    def _fuzzy_match_pass(self, raw_matches, remaining_text):
        if not self._fuzzy_enabled():
            return raw_matches, remaining_text

        filled_singular = {
            m['slot_type'] for m in raw_matches if m['slot_type'] in self._FUZZY_SINGULAR_SLOTS
        }
        filled_values = {(m['slot_type'], m['model_name'], m['value']) for m in raw_matches}

        extra_matches = []
        text = remaining_text
        ordered = sorted(self._synonyms, key=lambda s: (-len(s.phrase), -s.priority))
        for syn in ordered:
            if syn.slot_type in self._FUZZY_SINGULAR_SLOTS and syn.slot_type in filled_singular:
                continue
            key = (syn.slot_type, syn.model_name or None, syn.value)
            if key in filled_values:
                continue

            span = self._fuzzy_whole_phrase_span(text, syn.phrase)
            if not span:
                continue
            start, end = span
            extra_matches.append({
                'slot_type': syn.slot_type,
                'model_name': syn.model_name or None,
                'value': syn.value,
                'phrase': syn.phrase,
            })
            if syn.slot_type in self._FUZZY_SINGULAR_SLOTS:
                filled_singular.add(syn.slot_type)
            filled_values.add(key)
            text = text[:start] + (' ' * (end - start)) + text[end:]

        return raw_matches + extra_matches, text

    @classmethod
    def _fuzzy_whole_phrase_span(cls, text, phrase):
        """Slide a same-word-count window across `text` and accept the
        first one whose whole-phrase similarity to `syn.phrase` clears
        _FUZZY_PHRASE_SIMILARITY_THRESHOLD — a stricter, holistic cousin
        of _fuzzy_span's per-word check, intentionally conservative since
        a false positive here silently returns the wrong chart instead of
        falling through to the guided form.
        """
        phrase_words = phrase.split()
        k = len(phrase_words)
        tokens = list(TOKEN_RE.finditer(text))
        if len(tokens) < k:
            return None
        for i in range(len(tokens) - k + 1):
            window = tokens[i:i + k]
            window_text = ' '.join(t.group(0) for t in window)
            if cls._similarity(window_text, phrase) >= cls._FUZZY_PHRASE_SIMILARITY_THRESHOLD:
                return (window[0].start(), window[-1].end())
        return None

    @staticmethod
    def _similarity(a, b):
        """rapidfuzz isn't a base-module dependency (see module docstring
        — zero external dependencies is the point) so this vendors the
        same ratio rapidfuzz.fuzz.ratio would give, off the Levenshtein
        distance this file already implements for _fuzzy_span."""
        if not a and not b:
            return 1.0
        return 1 - (_levenshtein(a, b) / max(len(a), len(b)))

    # ------------------------------------------------------------------ #
    # Step 2: resolve the model
    # ------------------------------------------------------------------ #
    @staticmethod
    def _resolve_model(matches):
        explicit = [m for m in matches if m['slot_type'] == 'model']
        if explicit:
            return explicit[0]['value']

        votes = {}
        for m in matches:
            if m['slot_type'] in ('measure', 'groupby') and m['model_name']:
                votes[m['model_name']] = votes.get(m['model_name'], 0) + 1
        if not votes:
            return None
        return max(votes, key=votes.get)

    # ------------------------------------------------------------------ #
    # Step 3: assemble the spec from matches consistent with that model
    # ------------------------------------------------------------------ #
    def _apply_model_scoped_matches(self, spec, matches, model_name):
        allowlist_entry = self._allowlist_by_model.get(model_name)
        date_field = (allowlist_entry.date_field_id.name
                      if allowlist_entry and allowlist_entry.date_field_id else None)

        for m in matches:
            slot = m['slot_type']

            if slot == 'measure' and m['model_name'] == model_name:
                if m['value'] not in spec['measures']:
                    spec['measures'].append(m['value'])

            elif slot == 'groupby' and m['model_name'] == model_name:
                if m['value'] not in spec['groupby']:
                    spec['groupby'].append(m['value'])

            elif slot == 'groupby_time':
                if date_field:
                    fragment = f"{date_field}:{m['value']}"
                    if fragment not in spec['groupby']:
                        spec['groupby'].append(fragment)

            elif slot == 'chart_type':
                spec['chart_type'] = m['value']

            elif slot == 'time_range':
                if date_field:
                    spec['domain'].extend(
                        self._resolve_time_range(m['value'], date_field))

            elif slot == 'sort' and spec['measures']:
                # formatted_read_group's `order` requires the full
                # aggregate spec ('amount_total:sum desc'), not the bare
                # field name, when ordering by a measure.
                spec['orderby'] = f"{spec['measures'][0]} {m['value']}"

    def _apply_top_n(self, spec, remaining_text, model_name):
        m = TOP_N_RE.search(remaining_text)
        if not m:
            return
        direction, n = m.group(1), int(m.group(2))
        spec['limit'] = n
        if spec['measures']:
            spec['orderby'] = "{} {}".format(
                spec['measures'][0], 'desc' if direction == 'top' else 'asc')

    def _apply_default_measure(self, spec, model_name):
        if spec['measures']:
            return
        entry = self._allowlist_by_model.get(model_name)
        if entry:
            default = entry.default_measure_spec()
            if default:
                spec['measures'].append(default)

    @staticmethod
    def _apply_default_chart_type(spec):
        if spec['chart_type']:
            return
        has_time_bucket = any(':' in g for g in spec['groupby'])
        if has_time_bucket:
            spec['chart_type'] = 'line'
        elif not spec['groupby']:
            spec['chart_type'] = 'number'
        else:
            spec['chart_type'] = 'bar'

    # ------------------------------------------------------------------ #
    # Time-range resolution
    # ------------------------------------------------------------------ #
    def _today(self):
        # Resolve "today" in the CURRENT USER's timezone, not the server's —
        # matters for "this quarter"/"this month" boundaries near midnight.
        return odoo_fields.Date.context_today(self.env['ai.dashboard.allowlist'])

    def _resolve_time_range(self, code, date_field):
        today = self._today()

        def domain(d_from, d_to):
            return [(date_field, '>=', d_from.isoformat()),
                    (date_field, '<=', d_to.isoformat())]

        if code == 'today':
            return domain(today, today)
        if code == 'yesterday':
            y = today - timedelta(days=1)
            return domain(y, y)
        if code == 'this_week':
            start = today - timedelta(days=today.weekday())
            return domain(start, today)
        if code == 'last_week':
            this_week_start = today - timedelta(days=today.weekday())
            start = this_week_start - timedelta(days=7)
            end = this_week_start - timedelta(days=1)
            return domain(start, end)
        if code == 'this_month':
            start = today.replace(day=1)
            return domain(start, today)
        if code == 'last_month':
            first_of_this_month = today.replace(day=1)
            end = first_of_this_month - timedelta(days=1)
            start = end.replace(day=1)
            return domain(start, end)
        if code == 'this_quarter':
            q_start_month = ((today.month - 1) // 3) * 3 + 1
            start = today.replace(month=q_start_month, day=1)
            return domain(start, today)
        if code == 'last_quarter':
            q_start_month = ((today.month - 1) // 3) * 3 + 1
            this_q_start = today.replace(month=q_start_month, day=1)
            end = this_q_start - timedelta(days=1)
            prev_q_start_month = ((end.month - 1) // 3) * 3 + 1
            start = end.replace(month=prev_q_start_month, day=1)
            return domain(start, end)
        if code == 'this_year':
            start = today.replace(month=1, day=1)
            return domain(start, today)
        if code == 'last_year':
            start = today.replace(year=today.year - 1, month=1, day=1)
            end = today.replace(year=today.year - 1, month=12, day=31)
            return domain(start, end)
        return []

    # ------------------------------------------------------------------ #
    # Confidence scoring
    # ------------------------------------------------------------------ #
    @staticmethod
    def _score(spec):
        """0.0-1.0. Below the controller's threshold, the UI shows a
        guided form instead of guessing — see controllers/main.py."""
        if not spec.get('model'):
            return 0.0
        have_dimension = bool(spec['groupby'])
        have_measure = bool(spec['measures'])
        # model is a hard requirement (already gated above); the other two
        # are what actually separate "confident" from "a fragment".
        return (int(have_dimension) + int(have_measure)) / 2
