# -*- coding: utf-8 -*-
from odoo import fields, models


class AiDashboardSynonym(models.Model):
    """Maps a phrase to a concrete query fragment. This table IS the
    module's 'intelligence' — it's just data, editable by an admin without
    touching code, which is the whole point of not using an LLM: coverage
    grows by adding rows, not by prompt engineering.
    """
    _name = 'ai.dashboard.synonym'
    _description = 'Smart KPI Dashboard — Phrase Mapping'
    _order = 'priority desc, id'

    phrase = fields.Char(
        required=True, index=True,
        help="Lowercase phrase to match, e.g. 'revenue', 'by region', "
             "'bar chart'. Matched as a whole-word/phrase boundary, "
             "longest phrases are tried first so 'this quarter' beats "
             "a bare 'quarter'.")
    slot_type = fields.Selection([
        ('model', 'Model'),
        ('measure', 'Measure (numeric field + aggregation)'),
        ('groupby', 'Group By Dimension (specific field)'),
        ('groupby_time', 'Group By Time Bucket (month/week/quarter/year)'),
        ('chart_type', 'Chart Type'),
        ('time_range', 'Time Range Filter'),
        ('sort', 'Sort Direction (top/bottom N)'),
    ], required=True, index=True)

    # Only meaningful (and required) for 'measure' and 'groupby' — those
    # field names differ per model, so the match must be scoped to a model.
    # Left empty for 'chart_type' / 'groupby_time' / 'time_range' / 'sort',
    # which are model-agnostic by design.
    model_id = fields.Many2one('ir.model', ondelete='cascade')
    model_name = fields.Char(
        string='Technical Name', related='model_id.model', store=True, readonly=True)

    value = fields.Char(
        required=True,
        help="model: technical model name (e.g. 'sale.order')\n"
             "measure: 'field:aggregation' (e.g. 'amount_total:sum')\n"
             "groupby: field name (e.g. 'state_id')\n"
             "groupby_time: one of month/week/quarter/year\n"
             "chart_type: bar/line/pie/number\n"
             "time_range: one of today/yesterday/this_week/last_week/"
             "this_month/last_month/this_quarter/last_quarter/this_year/last_year\n"
             "sort: 'asc' or 'desc'")
    priority = fields.Integer(
        default=10, help="Higher wins if two phrases of equal length overlap.")
    active = fields.Boolean(default=True)
