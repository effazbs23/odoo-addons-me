# -*- coding: utf-8 -*-
import json
import logging

from odoo import fields, models, api
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

    @staticmethod
    def _format_for_chartjs(spec, raw_rows):
        """formatted_read_group's output -> {labels, datasets} that the
        OWL/Chart.js frontend can render directly with no further transform.
        """
        groupby = spec['groupby']
        measures = spec['measures']
        primary_group = groupby[0] if groupby else None

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
                'label': field_name,
                'data': [row.get(measure, 0) for row in raw_rows],
            })

        return {'labels': labels, 'datasets': datasets}
