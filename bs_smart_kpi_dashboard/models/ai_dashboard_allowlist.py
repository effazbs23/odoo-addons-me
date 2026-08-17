# -*- coding: utf-8 -*-
import logging
import re

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AiDashboardAllowlist(models.Model):
    """The single security control point for the whole module.

    Nothing in the parser or the controller is ever allowed to query a
    model/field that isn't explicitly listed here. Admins maintain this
    like any other configuration record — no code changes needed to widen
    or narrow what the dashboard can report on.
    """
    _name = 'ai.dashboard.allowlist'
    _description = 'Smart KPI Dashboard — Queryable Model'
    _order = 'sequence, id'
    _sql_constraints = [
        ('model_uniq', 'unique(model_id)',
         "This model already has an Allowed Models entry — edit that one "
         "instead of creating a second, ambiguous entry for the same model."),
    ]

    name = fields.Char(related='model_id.name', store=True, readonly=True)
    sequence = fields.Integer(default=10)
    model_id = fields.Many2one(
        'ir.model', required=True, ondelete='cascade',
        help="The Odoo model this entry makes queryable.")
    model_name = fields.Char(
        string='Technical Name',
        related='model_id.model', store=True, readonly=True,
        help="Technical name, e.g. 'sale.order' — used everywhere in code "
             "instead of the model_id.id so the parser/controller stay simple.")

    field_ids = fields.Many2many(
        'ir.model.fields', string='Groupable / Filterable Fields',
        domain="[('model_id', '=', model_id), "
               "('ttype', 'in', ['many2one', 'selection', 'char', 'date', 'datetime', 'boolean'])]",
        help="Fields the parser/guided form may use as GROUP BY dimensions "
             "or in filters. Leave empty to disallow entirely — never "
             "default-allow a field by omission.")
    measure_field_ids = fields.Many2many(
        'ir.model.fields', 'ai_dashboard_allowlist_measure_rel',
        'allowlist_id', 'field_id', string='Measurable (Numeric) Fields',
        domain="[('model_id', '=', model_id), ('ttype', 'in', ['integer', 'float', 'monetary'])]",
        help="Fields that may be summed/averaged/counted as chart measures.")
    default_measure_field_id = fields.Many2one(
        'ir.model.fields', string='Default Measure',
        domain="[('id', 'in', measure_field_ids)]",
        help="Used when the user's prompt names a dimension but no measure "
             "— e.g. 'sales by region' defaults to sum(amount_total).")
    default_aggregation = fields.Selection(
        [('sum', 'Sum'), ('avg', 'Average'), ('count', 'Count')],
        default='sum', required=True)

    # Client-supplied 'limit' upper bound — a DoS-adjacent guard, not a
    # security boundary by itself (grouping fields are already allow-
    # listed): a huge limit on a query with several groupby dimensions
    # can still be an expensive aggregation.
    _MAX_QUERY_LIMIT = 1000

    # A spec's own domain/field checks already restrict WHICH fields can be
    # grouped/measured, but not HOW MANY at once — and a wide GROUP BY on a
    # large table is expensive regardless of whether every individual field
    # was legitimately allow-listed. These caps are a second, independent
    # guard against an authenticated user (or the guided form) building an
    # unreasonably wide aggregation, same spirit as _MAX_QUERY_LIMIT above.
    _MAX_GROUPBY_FIELDS = 4
    _MAX_MEASURES = 4

    date_field_id = fields.Many2one(
        'ir.model.fields', string='Primary Date Field',
        domain="[('model_id', '=', model_id), ('ttype', 'in', ['date', 'datetime'])]",
        help="Used to resolve time-range phrases ('this quarter', 'last "
             "month') and time-trend groupings ('by month', 'over time') "
             "for this model.")

    active = fields.Boolean(default=True)

    # --- integrity: a field can only ever be allow-listed for the model it
    # actually belongs to. The view's domain="[('model_id', '=', model_id)]"
    # on field_ids/measure_field_ids/date_field_id only constrains the
    # client widget — it does nothing to stop a direct ORM write, an XML
    # data record, or a future script from linking a field that belongs to
    # a *different* model. Because many unrelated models share a technical
    # field name ('name', 'state', 'partner_id', 'create_date', ...), that
    # mismatch wouldn't necessarily error in the ORM later — it could
    # silently let a query read a field through the wrong model. Enforce
    # it server-side so misconfiguration can never become data exposure.
    @api.constrains('model_id', 'field_ids', 'measure_field_ids', 'date_field_id')
    def _check_fields_belong_to_model(self):
        for rec in self:
            if not rec.model_id:
                continue
            mismatched = (rec.field_ids | rec.measure_field_ids | rec.date_field_id).filtered(
                lambda f: f.model_id != rec.model_id)
            if mismatched:
                raise ValidationError(
                    _("These fields don't belong to %s and can't be "
                      "allow-listed here: %s.")
                    % (rec.model_id.model, ', '.join(mismatched.mapped('name'))))

    # --- helpers used by the parser & controller ---------------------------
    def allowed_field_names(self):
        self.ensure_one()
        return set(self.field_ids.mapped('name'))

    def allowed_measure_names(self):
        self.ensure_one()
        return set(self.measure_field_ids.mapped('name'))

    def default_measure_spec(self):
        """Returns e.g. 'amount_total:sum' or None if no default configured."""
        self.ensure_one()
        if not self.default_measure_field_id:
            return None
        return f"{self.default_measure_field_id.name}:{self.default_aggregation}"

    # --- the real security boundary ----------------------------------------
    @api.model
    def _validate_spec(self, spec, env=None):
        """Re-derive permission from the allow-list AND the current user's
        own ACLs, every single time — never trust a spec just because it
        was built by our own parser or loaded from a saved tile. This is
        called from three places (live generate, tile save, tile re-fetch)
        on purpose: it must be impossible to reach formatted_read_group()
        without passing through here.
        """
        env = env or self.env
        model_name = spec.get('model')
        if not model_name or model_name not in env:
            raise ValidationError(_("Unknown or missing model in query spec."))

        entry = env['ai.dashboard.allowlist'].sudo().search(
            [('model_name', '=', model_name)], limit=1)
        if not entry:
            raise ValidationError(
                _("'%s' is not enabled for Smart KPI Dashboard. Ask an "
                  "administrator to add it under Settings ▸ Smart KPI "
                  "Dashboard ▸ Allowed Models.") % model_name)

        allowed_fields = entry.allowed_field_names()
        allowed_measures = entry.allowed_measure_names()

        groupby = spec.get('groupby', [])
        measures = spec.get('measures', [])
        if len(groupby) > self._MAX_GROUPBY_FIELDS:
            raise ValidationError(
                _("Too many group-by dimensions (max %s).") % self._MAX_GROUPBY_FIELDS)
        if len(measures) > self._MAX_MEASURES:
            raise ValidationError(
                _("Too many measures (max %s).") % self._MAX_MEASURES)

        for gb in spec.get('groupby', []):
            field_name = gb.split(':')[0]  # strip ':month' etc. granularity
            if field_name not in allowed_fields:
                raise ValidationError(
                    _("Field '%s' is not allow-listed for grouping on %s.")
                    % (field_name, model_name))

        for m in spec.get('measures', []):
            field_name = m.split(':')[0]
            if field_name not in allowed_measures:
                raise ValidationError(
                    _("Field '%s' is not allow-listed as a measure on %s.")
                    % (field_name, model_name))

        # Domain fields must also be allow-listed (either as a groupby-type
        # field or the model's own designated date field) — otherwise a
        # crafted spec could filter on a field it was never granted access to.
        date_field_name = entry.date_field_id.name if entry.date_field_id else None
        for clause in spec.get('domain', []):
            if not isinstance(clause, (list, tuple)) or len(clause) != 3:
                continue
            field_name = clause[0]
            if field_name not in allowed_fields and field_name != date_field_name:
                raise ValidationError(
                    _("Field '%s' is not allow-listed for filtering on %s.")
                    % (field_name, model_name))

        # spec['orderby']/spec['limit'] are 100% client-controlled on the
        # run_manual and tile/save endpoints and were previously never
        # checked here — Odoo's own _read_group_orderby() accepts ANY
        # real field on the model as an order term (as 'field:agg'), not
        # just fields already in groupby/measures, so an unvalidated
        # orderby could silently order results by a field the allow-list
        # deliberately excluded (a side-channel on that field's values).
        # Order terms must reference only fields already vetted above.
        allowed_order_fields = allowed_fields | allowed_measures
        orderby = spec.get('orderby')
        if orderby:
            for part in orderby.split(','):
                term = part.strip().split(' ')[0] if part.strip() else ''
                field_name = term.split(':')[0]
                if not field_name or field_name not in allowed_order_fields:
                    raise ValidationError(
                        _("Field '%s' is not allow-listed for ordering on %s.")
                        % (field_name, model_name))

        limit = spec.get('limit')
        if limit is not None:
            if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
                raise ValidationError(_("Invalid limit in query spec."))
            if limit > self._MAX_QUERY_LIMIT:
                raise ValidationError(
                    _("Limit exceeds the maximum allowed (%s).") % self._MAX_QUERY_LIMIT)

        # Finally: let Odoo's own field-level security have the last word.
        # formatted_read_group runs as env.user and already enforces
        # ACLs/record rules — this call surfaces a clean error early
        # instead of a confusing empty result set.
        Model = env[model_name]
        if not Model.has_access('read'):
            raise ValidationError(
                _("You don't have read access to %s.") % model_name)

        return True

    # ------------------------------------------------------------------ #
    # Vocabulary auto-discovery — scaffolding, not exposure.
    #
    # Every record this creates is born with active=False. Being inactive
    # means both search([]) here AND KpiPromptParser's own `search([])`
    # (models/ai_dashboard_synonym.py, __init__.py) silently skip it — so
    # a freshly-installed module can never become queryable or matchable
    # by a prompt until a human with base.group_system flips it on. This
    # method only ever widens the REVIEW QUEUE, never the allow-list
    # itself; _validate_spec() (above) remains the sole gate on live data.
    # ------------------------------------------------------------------ #
    _DISCOVERY_EXCLUDED_MODEL_PREFIXES = (
        'ir.', 'base.', 'base_import.', 'bus.', 'report.', 'web_editor.',
        'web_tour.', 'mail.', 'iap.', 'http_routing.', 'resource.',
        'digest.', 'gamification.', 'onboarding.', 'spreadsheet.',
        'ai.dashboard.',
    )
    _DISCOVERY_EXCLUDED_FIELD_NAMES = {
        'id', 'display_name', 'create_uid', 'write_uid', 'write_date',
        'access_token', 'activity_ids', 'message_ids',
        'message_follower_ids', 'website_message_ids',
    }
    _DISCOVERY_GROUPBY_TTYPES = ('many2one', 'selection', 'char', 'date', 'datetime', 'boolean')
    _DISCOVERY_MEASURE_TTYPES = ('integer', 'float', 'monetary')

    @api.model
    def _discover_new_models(self):
        """Create inactive draft allow-list (+ synonym) rows for any model
        this dashboard doesn't know about yet, so a human only has to
        REVIEW and switch things on instead of configuring from scratch.
        Safe to call repeatedly (idempotent — already-known models are
        skipped) and safe to call from a cron or right after a module
        install/upgrade/uninstall.
        """
        known_model_ids = self.sudo().with_context(active_test=False).search([]).model_id.ids
        existing_phrases = set(
            self.env['ai.dashboard.synonym'].sudo().with_context(active_test=False)
            .search([]).mapped('phrase')
        )

        domain = [('transient', '=', False), ('abstract', '=', False)]
        if known_model_ids:
            domain.append(('id', 'not in', known_model_ids))
        candidates = self.env['ir.model'].sudo().search(domain)

        created = self.browse()
        for model in candidates:
            if model.model.startswith(self._DISCOVERY_EXCLUDED_MODEL_PREFIXES):
                continue
            Model = self.env.get(model.model)
            if Model is None or not getattr(Model, '_auto', False):
                continue

            usable = model.field_id.filtered(
                lambda f: f.store and f.name not in self._DISCOVERY_EXCLUDED_FIELD_NAMES)
            groupby_fields = usable.filtered(lambda f: f.ttype in self._DISCOVERY_GROUPBY_TTYPES)
            measure_fields = usable.filtered(lambda f: f.ttype in self._DISCOVERY_MEASURE_TTYPES)
            if not groupby_fields or not measure_fields:
                continue  # nothing chartable — don't clutter the review queue

            date_fields = usable.filtered(lambda f: f.ttype in ('date', 'datetime'))
            date_field = date_fields.filtered(lambda f: f.name != 'create_date')[:1] or date_fields[:1]
            default_measure = (
                measure_fields.filtered(lambda f: f.ttype == 'monetary')[:1]
                or measure_fields.filtered(lambda f: 'total' in f.name)[:1]
                or measure_fields[:1]
            )

            entry = self.sudo().create({
                'model_id': model.id,
                'active': False,
                'field_ids': [(6, 0, groupby_fields[:10].ids)],
                'measure_field_ids': [(6, 0, measure_fields[:6].ids)],
                'default_measure_field_id': default_measure.id if default_measure else False,
                'default_aggregation': 'sum',
                'date_field_id': date_field.id if date_field else False,
            })
            created |= entry
            existing_phrases |= self._create_draft_synonyms(entry, existing_phrases)

        if created:
            _logger.info(
                "Smart KPI Dashboard: discovered %d new queryable model(s) as "
                "inactive drafts (%s) — review under Configuration ▸ Allowed "
                "Models.", len(created), ', '.join(created.mapped('model_name')))
        return created

    def _create_draft_synonyms(self, entry, existing_phrases):
        """Best-effort phrase suggestions for one freshly-discovered model —
        the model's own name/label plus each allow-listed field's label.
        Never overwrites or collides with a phrase that already exists
        anywhere (active or not): the parser resolves each phrase to
        exactly one row, so a silent duplicate would make matching
        arbitrary later. Rows are created inactive, same as the allow-list
        entry they belong to.
        """
        new_phrases = set()
        to_create = []

        def add(phrase, values):
            phrase = self._clean_phrase(phrase)
            if len(phrase) < 3 or phrase in existing_phrases or phrase in new_phrases:
                return
            new_phrases.add(phrase)
            to_create.append({**values, 'phrase': phrase, 'active': False})

        for phrase in self._model_phrases(entry.model_id):
            add(phrase, {'slot_type': 'model', 'value': entry.model_name})

        for field in entry.measure_field_ids:
            add(field.field_description, {
                'slot_type': 'measure', 'model_id': entry.model_id.id,
                'value': f"{field.name}:sum",
            })

        for field in entry.field_ids:
            add(field.field_description, {
                'slot_type': 'groupby', 'model_id': entry.model_id.id,
                'value': field.name,
            })

        if to_create:
            self.env['ai.dashboard.synonym'].sudo().create(to_create)
        return new_phrases

    @staticmethod
    def _model_phrases(model):
        """Candidate 'this prompt is about <model>' phrases: the model's
        own description ('Purchase Order') and its technical leaf name,
        singular and a naively-pluralized form ('purchase order(s)')."""
        phrases = set()
        desc = AiDashboardAllowlist._clean_phrase(model.name)
        if desc:
            phrases.add(desc)

        leaf = AiDashboardAllowlist._clean_phrase(model.model.split('.')[-1].replace('_', ' '))
        if leaf:
            phrases.add(leaf)
            words = leaf.split()
            words[-1] = AiDashboardAllowlist._pluralize(words[-1])
            phrases.add(' '.join(words))

        return {p for p in phrases if len(p) >= 3}

    @staticmethod
    def _pluralize(word):
        if word.endswith('y') and len(word) > 1 and word[-2] not in 'aeiou':
            return word[:-1] + 'ies'
        if word.endswith(('s', 'sh', 'ch', 'x', 'z')):
            return word + 'es'
        return word + 's'

    @staticmethod
    def _clean_phrase(text):
        """Same normalization the parser applies to prompts (kpi_prompt_
        parser.py `_normalize`) — a phrase with characters the parser
        strips out (parens, punctuation) could never match anyway."""
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text or '')
        return re.sub(r'\s+', ' ', text).strip().lower()

    @api.model
    def _discover_new_models_action(self):
        """Manual trigger (Action menu / Configuration menu) — same logic
        as the cron, but returns something visible instead of running
        silently in the background.
        """
        new_entries = self._discover_new_models()
        if not new_entries:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Smart KPI Dashboard"),
                    'message': _("No new queryable models found — everything "
                                 "installed is already configured or already "
                                 "queued for review."),
                    'type': 'info',
                },
            }
        return {
            'type': 'ir.actions.act_window',
            'name': _("Newly Discovered Models — Review & Activate"),
            'res_model': 'ai.dashboard.allowlist',
            'view_mode': 'list,form',
            'domain': [('id', 'in', new_entries.ids)],
            'context': {'active_test': False},
        }
