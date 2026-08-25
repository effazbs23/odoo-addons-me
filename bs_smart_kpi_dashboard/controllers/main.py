# -*- coding: utf-8 -*-
import json
import logging

from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError

from ..logic.kpi_prompt_parser import KpiPromptParser

_logger = logging.getLogger(__name__)

# Every route below is meant for internal back-office users only (the
# dashboard menu is gated to base.group_user and isn't shown to portal
# contacts) — but auth='user' alone admits ANY authenticated res.users
# record, portal included. Enforced explicitly here so all six routes
# fail the same clean way instead of some silently working (via the
# module's own sudo()'d metadata reads) and others crashing with an
# unhandled AccessError deep in the ORM (e.g. ai.dashboard.tile has no
# ir.model.access grant for portal users at all).
_INTERNAL_GROUP = 'base.group_user'

# Hard cap on free-text prompt length: KpiPromptParser's fuzzy-match
# fallback runs a Levenshtein DP per synonym per prompt, unconditionally,
# on every /generate and /suggest call — an unbounded prompt is a cheap
# CPU-cost amplification vector for any authenticated user. Comfortably
# above any realistic KPI request.
_MAX_PROMPT_LENGTH = 300


class SmartKpiDashboardController(http.Controller):

    @staticmethod
    def _check_internal_user(env):
        if not env.user.has_group(_INTERNAL_GROUP):
            raise AccessError(
                _("Smart KPI Dashboard is only available to internal users."))

    @staticmethod
    def _check_prompt_length(prompt):
        if not isinstance(prompt, str) or len(prompt) > _MAX_PROMPT_LENGTH:
            raise ValidationError(
                _("Prompt is too long (maximum %s characters).") % _MAX_PROMPT_LENGTH)

    # -------------------------------------------------------------- #
    # Parse a prompt with the local, deterministic parser. Confident
    # results run immediately; anything below the confidence threshold
    # (or missing a measure) drops to the guided form instead. Every
    # spec, however it was produced, still has to clear the same
    # _validate_spec() gate before anything executes.
    # -------------------------------------------------------------- #
    @http.route('/bs_smart_kpi_dashboard/generate', type='jsonrpc', auth='user')
    def generate(self, prompt):
        env = request.env
        self._check_internal_user(env)
        try:
            self._check_prompt_length(prompt)
        except ValidationError as e:
            return {'error': str(e)}

        parser = KpiPromptParser(env)
        spec = parser.parse(prompt)

        if spec['confidence'] < 0.5 or not spec.get('measures'):
            self._log_unmatched_phrase(env, spec)
            return {
                'needs_manual_input': True,
                'partial_spec': spec,
                'options': self._guided_options(env),
            }

        try:
            env['ai.dashboard.allowlist']._validate_spec(spec, env)
        except ValidationError as e:
            return {'error': str(e)}

        chart = self._run_and_format(env, spec)
        desc = env['ai.dashboard.tile']._describe_spec(spec)
        return {'spec': spec, 'chart': chart, 'source': 'local', **desc}

    # -------------------------------------------------------------- #
    # Telemetry only, for the low-confidence branch above. Wrapped so a
    # bug or DB hiccup here can NEVER prevent the guided form from being
    # returned to the user — that response has already been earned by
    # this point, this is just bookkeeping for admins to review later
    # (ai.dashboard.unmatched_phrase).
    # -------------------------------------------------------------- #
    @staticmethod
    def _log_unmatched_phrase(env, spec):
        try:
            leftover = (spec.get('leftover_text') or '').strip()
            if leftover:
                env['ai.dashboard.unmatched_phrase'].sudo().log_unmatched(
                    leftover, spec.get('model'))
        except Exception:
            _logger.exception(
                "Smart KPI Dashboard: failed to log unmatched phrase "
                "(non-fatal, request continues)")

    # -------------------------------------------------------------- #
    # Typeahead suggestions for the ask bar, built from active vocabulary
    # only — see KpiPromptParser.suggest() for what "active" excludes
    # (inactive allow-list entries / synonyms, e.g. auto-discovery drafts
    # awaiting review).
    # -------------------------------------------------------------- #
    @http.route('/bs_smart_kpi_dashboard/suggest', type='jsonrpc', auth='user')
    def suggest(self, prompt=''):
        env = request.env
        self._check_internal_user(env)
        self._check_prompt_length(prompt or '')
        parser = KpiPromptParser(env)
        return parser.suggest(prompt)

    # -------------------------------------------------------------- #
    # Run a spec assembled by the guided form (user picked every slot
    # by hand instead of, or after, typing a prompt)
    # -------------------------------------------------------------- #
    @http.route('/bs_smart_kpi_dashboard/run_manual', type='jsonrpc', auth='user')
    def run_manual(self, spec):
        env = request.env
        self._check_internal_user(env)
        try:
            env['ai.dashboard.allowlist']._validate_spec(spec, env)
        except ValidationError as e:
            return {'error': str(e)}
        chart = self._run_and_format(env, spec)
        desc = env['ai.dashboard.tile']._describe_spec(spec)
        return {'spec': spec, 'chart': chart, 'source': 'manual', **desc}

    # -------------------------------------------------------------- #
    # Options for the guided-form dropdowns — only allow-listed data,
    # same as everything else in this module. Called from generate()'s
    # low-confidence branch; not exposed as its own route (nothing in
    # the frontend fetches options independently of a generate() call).
    # -------------------------------------------------------------- #
    def _guided_options(self, env):
        entries = env['ai.dashboard.allowlist'].sudo().search([])
        result = []
        for entry in entries:
            # Respect field-level security: don't offer a field in the
            # dropdown that this particular user can't actually read.
            # fields_get() already filters to fields this user can read —
            # cross-check against it instead of trusting the allow-list's
            # own field list.
            Model = env[entry.model_name]
            if not Model.has_access('read'):
                continue
            readable = set(Model.fields_get().keys())

            result.append({
                'model': entry.model_name,
                'label': entry.name,
                'groupby_fields': [
                    {'name': f.name, 'label': f.field_description}
                    for f in entry.field_ids if f.name in readable
                ],
                'measure_fields': [
                    {'name': f.name, 'label': f.field_description}
                    for f in entry.measure_field_ids if f.name in readable
                ],
                'default_measure': entry.default_measure_spec(),
                'has_date_field': bool(entry.date_field_id),
            })
        return result

    # -------------------------------------------------------------- #
    # Saved tiles
    # -------------------------------------------------------------- #
    @http.route('/bs_smart_kpi_dashboard/tiles', type='jsonrpc', auth='user')
    def list_tiles(self):
        env = request.env
        self._check_internal_user(env)
        return env['ai.dashboard.tile'].get_dashboard_tiles()

    @http.route('/bs_smart_kpi_dashboard/tile/save', type='jsonrpc', auth='user')
    def save_tile(self, name, prompt, spec, chart_type, shared=False):
        env = request.env
        self._check_internal_user(env)
        try:
            env['ai.dashboard.allowlist']._validate_spec(spec, env)
        except ValidationError as e:
            return {'error': str(e)}

        tile = env['ai.dashboard.tile'].create({
            'name': name,
            'prompt': prompt,
            'spec_json': json.dumps(spec),
            'chart_type': chart_type,
            'shared': shared,
        })
        return {'id': tile.id}

    @http.route('/bs_smart_kpi_dashboard/tile/delete', type='jsonrpc', auth='user')
    def delete_tile(self, tile_id):
        env = request.env
        self._check_internal_user(env)
        tile = env['ai.dashboard.tile'].search(
            [('id', '=', tile_id), ('user_id', '=', env.uid)], limit=1)
        if not tile:
            return {'error': _("Tile not found or not owned by you.")}
        tile.unlink()
        return {'success': True}

    # -------------------------------------------------------------- #
    # Shared execution helper — routes through ai.dashboard.tile so
    # there is exactly one place in the module that calls
    # formatted_read_group(), not one per entry point.
    # -------------------------------------------------------------- #
    @staticmethod
    def _run_and_format(env, spec):
        Tile = env['ai.dashboard.tile']
        rows = Tile._run_spec(spec)
        return Tile._format_for_chartjs(spec, rows)
