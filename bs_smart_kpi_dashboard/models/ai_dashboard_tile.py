# -*- coding: utf-8 -*-
import json
import logging

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AiDashboardTile(models.Model):
    """A saved KPI. Stores the VALIDATED spec, not raw text — the prompt is
    kept only for display/re-editing. Data is re-fetched live every time
    the dashboard loads (never cached to disk) and re-validated against the
    current allow-list every time too, in case an admin has since narrowed
    it — a tile can never outlive the permission that created it.
    """
    _name = 'ai.dashboard.tile'
    _description = 'Smart KPI Dashboard — Saved Tile'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    prompt = fields.Char(help="Original natural-language request, kept for display only.")
    spec_json = fields.Text(required=True, help="Validated query spec (JSON).")
    chart_type = fields.Selection(
        [('bar', 'Bar'), ('line', 'Line'), ('pie', 'Pie'), ('number', 'Single KPI')],
        required=True, default='bar')

    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, required=True)
    shared = fields.Boolean(
        default=False,
        help="If enabled, ALL users who pass the allow-list's own model/field "
             "access checks can see this tile on their dashboard, not just the owner.")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    @api.model
    def get_dashboard_tiles(self):
        """Tiles visible to the current user: their own + shared ones.
        Called once when the dashboard action opens."""
        domain = ['|', ('user_id', '=', self.env.uid), ('shared', '=', True)]
        tiles = self.search(domain)
        result = []
        for tile in tiles:
            try:
                result.append(tile._to_chart_payload())
            except ValidationError as e:
                # A tile can go stale if an admin narrows the allow-list
                # after it was saved — don't break the whole dashboard for
                # one bad tile, just flag it visibly instead.
                _logger.info("Stale dashboard tile %s: %s", tile.id, e)
                result.append({
                    'id': tile.id, 'name': tile.name, 'error': str(e),
                    'chart_type': tile.chart_type,
                    # Grouping only needs the model name, which is still
                    # readable straight off the stored spec even though the
                    # spec as a whole no longer validates.
                    'model': tile._spec_model(),
                })
            except Exception:
                # ValidationError is the expected staleness case; anything
                # else (corrupted spec_json, a field removed/retyped by an
                # unrelated module upgrade since the tile was saved, a DB
                # hiccup inside formatted_read_group) must degrade exactly
                # the same way — one bad row can never take down the whole
                # dashboard for every user who can see it.
                _logger.exception("Failed to render dashboard tile %s", tile.id)
                result.append({
                    'id': tile.id, 'name': tile.name,
                    'error': _("This tile could not be rendered — it may "
                               "reference data that no longer exists. Try "
                               "deleting and re-creating it."),
                    'chart_type': tile.chart_type,
                    'model': tile._spec_model(),
                })
        return result

    def _spec_model(self):
        self.ensure_one()
        try:
            return json.loads(self.spec_json).get('model')
        except ValueError:
            return None

    def _to_chart_payload(self):
        self.ensure_one()
        spec = json.loads(self.spec_json)
        # Re-validate every load — see class docstring.
        self.env['ai.dashboard.allowlist']._validate_spec(spec, self.env)
        data = self._run_spec(spec)
        return {
            'id': self.id,
            'name': self.name,
            'chart_type': self.chart_type,
            'model': spec.get('model'),
            'chart': self._format_for_chartjs(spec, data),
            **self._describe_spec(spec),
        }

    @api.model
    def _run_spec(self, spec):
        """The only place in the module that actually reaches the ORM's
        aggregation query. Always call via ai.dashboard.allowlist
        ._validate_spec() first — this method trusts its caller completely.
        """
        Model = self.env[spec['model']]
        return Model.formatted_read_group(
            domain=spec.get('domain', []),
            groupby=spec['groupby'],
            aggregates=spec['measures'],
            order=spec.get('orderby') or None,
            limit=spec.get('limit') or None,
        )

    def _format_for_chartjs(self, spec, raw_rows):
        """formatted_read_group's output -> {labels, datasets} that the
        OWL/Chart.js frontend can render directly with no further transform.
        """
        groupby = spec['groupby']
        measures = spec['measures']
        primary_group = groupby[0] if groupby else None
        field_labels = self._field_labels(spec)

        labels = []
        for row in raw_rows:
            if primary_group:
                val = row.get(primary_group)
                # many2one groupby values come back as (id, display_name)
                label = val[1] if isinstance(val, (list, tuple)) else (val or 'Undefined')
            else:
                label = 'Total'
            labels.append(str(label))

        datasets = []
        for measure in measures:
            # formatted_read_group keys each row by the exact aggregate
            # spec string ('amount_total:sum'), not the bare field name.
            field_name = measure.split(':')[0]
            datasets.append({
                'label': field_labels.get(field_name, field_name),
                'data': [row.get(measure, 0) for row in raw_rows],
            })

        return {'labels': labels, 'datasets': datasets}

    # ------------------------------------------------------------------ #
    # Human-readable title/description, derived ONLY from the validated
    # spec's model/field technical names — never from the user's raw
    # prompt text, so a typo or vague phrasing in what someone typed can
    # never leak into what the tile displays. Shared by every entry point
    # that can produce a chart (generate/run_manual in the controller,
    # and a saved tile's own re-fetch here) so the wording is consistent
    # everywhere, and always freshly computed (never stored) so it stays
    # correct even if a field gets relabeled after a tile was saved.
    # ------------------------------------------------------------------ #
    _AGG_LABELS = {'sum': 'Total', 'avg': 'Average', 'count': 'Count of'}
    _TIME_LABELS = {'month': 'Month', 'week': 'Week', 'quarter': 'Quarter', 'year': 'Year'}

    def _field_labels(self, spec):
        Model = self.env.get(spec.get('model'))
        if Model is None:
            return {}
        field_names = set()
        for m in spec.get('measures') or []:
            field_names.add(m.split(':')[0])
        for g in spec.get('groupby') or []:
            field_names.add(g.split(':')[0])
        for clause in spec.get('domain') or []:
            if isinstance(clause, (list, tuple)) and len(clause) == 3:
                field_names.add(clause[0])
        if not field_names:
            return {}
        fields_info = Model.fields_get(list(field_names))
        return {name: info['string'] for name, info in fields_info.items()}

    def _describe_spec(self, spec):
        model_name = spec.get('model')
        Model = self.env.get(model_name)
        model_label = Model._description if Model is not None else (model_name or 'Unknown model')
        field_labels = self._field_labels(spec)

        measure_parts = []
        for m in spec.get('measures') or []:
            field_name, _, agg = m.partition(':')
            agg_label = self._AGG_LABELS.get(agg, agg.title() or 'Total')
            field_label = field_labels.get(field_name, field_name)
            # Some fields are themselves labeled e.g. "Total" (amount_total
            # on sale.order/account.move) — don't double up into "Total Total".
            if field_label.lower().startswith(agg_label.lower()):
                measure_parts.append(field_label)
            else:
                measure_parts.append(f"{agg_label} {field_label}")
        measure_text = ' & '.join(measure_parts) or 'Total'

        groupby_parts = []
        for g in spec.get('groupby') or []:
            field_name, _, granularity = g.partition(':')
            label = field_labels.get(field_name, field_name)
            if granularity:
                label = f"{label} ({self._TIME_LABELS.get(granularity, granularity.title())})"
            groupby_parts.append(label)

        if groupby_parts:
            groupby_text = ', '.join(groupby_parts)
            title = f"{measure_text} by {groupby_text}"
            description = f"{measure_text} for {model_label}, grouped by {groupby_text}."
        else:
            title = measure_text
            description = f"{measure_text} across all {model_label} records."

        description += self._describe_domain(spec, field_labels)
        return {'title': title, 'description': description}

    @staticmethod
    def _describe_domain(spec, field_labels):
        domain = spec.get('domain') or []
        if not domain:
            return ''
        fields_used = {c[0] for c in domain if isinstance(c, (list, tuple)) and len(c) == 3}
        ops_used = {c[1] for c in domain if isinstance(c, (list, tuple)) and len(c) == 3}
        if len(fields_used) == 1 and len(domain) == 2 and ops_used <= {'>=', '<='}:
            field_name = next(iter(fields_used))
            lo = next(c[2] for c in domain if c[1] == '>=')
            hi = next(c[2] for c in domain if c[1] == '<=')
            return f" Filtered to {field_labels.get(field_name, field_name)} between {lo} and {hi}."
        return ' Additional filters applied.'
