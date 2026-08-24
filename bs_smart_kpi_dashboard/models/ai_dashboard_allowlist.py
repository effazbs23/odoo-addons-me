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

    date_field_id = fields.Many2one(
        'ir.model.fields', string='Primary Date Field',
        domain="[('model_id', '=', model_id), ('ttype', 'in', ['date', 'datetime'])]",
        help="Used to resolve time-range phrases ('this quarter', 'last "
             "month') and time-trend groupings ('by month', 'over time') "
             "for this model.")

    active = fields.Boolean(default=True)

    # _validate_spec() below resolves a model to its allow-list entry with
    # search(..., limit=1) and no explicit order — if two ACTIVE entries
    # ever existed for the same model, whichever one the DB happened to
    # return first would silently decide what's queryable, and an empty/
    # stale duplicate could shadow the real, properly-configured entry.
    # Scoped to (model_id, active) rather than a bare unique(model_id) so
    # it doesn't conflict with the inactive draft rows _discover_new_models
    # creates alongside an already-configured active entry.
    _active_model_uniq = models.Constraint(
        'UNIQUE (model_id, active)',
        "Only one allow-list entry may be active for a given model at a time.",
    )

    discovered_field_ids = fields.Many2many(
        'ir.model.fields', 'ai_dashboard_allowlist_discovered_rel',
        'allowlist_id', 'field_id', string='Newly Discovered Fields (Pending Review)',
        help="Fields found on this model that aren't allow-listed yet — "
             "typically because a module installed or upgraded after this "
             "entry was configured added them. Purely informational: this "
             "list grants no query access by itself. Use 'Promote to "
             "Allow-List' to actually move a field into Groupable/"
             "Filterable or Measurable above (and activate its draft "
             "synonym), or ignore it if you don't want it queryable.")

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
    # Suffix allow-lists: run_manual / tile/save accept a client-supplied
    # spec wholesale, so every 'field:suffix' fragment is validated here —
    # not just the field name before the colon. Anything not listed below
    # is rejected BEFORE it can reach formatted_read_group() and blow up
    # there with an unhandled 500.
    _ALLOWED_AGGREGATORS = ('sum', 'avg', 'count', 'min', 'max')
    _ALLOWED_GRANULARITIES = ('day', 'week', 'month', 'quarter', 'year')
    _ALLOWED_ORDER_DIRECTIONS = ('asc', 'desc')
    # The only non-leaf tokens a domain may contain ('&'/'|' prefix two
    # clauses, '!' prefixes one); anything else that isn't a 3-element
    # leaf is rejected outright.
    _DOMAIN_LOGIC_OPERATORS = ('&', '|', '!')
    # Cost cap: each extra grouping dimension multiplies the number of
    # groups formatted_read_group must build, so a crafted spec can't ask
    # for an unbounded cross-product aggregation over a high-volume table.
    _MAX_GROUPBY = 3
    # Same cost-cap philosophy as _MAX_GROUPBY/_MAX_QUERY_LIMIT: nothing
    # else here bounds how many clauses a client-built domain (run_manual /
    # tile/save) may contain, even though every clause is individually
    # allow-listed.
    _MAX_DOMAIN_CLAUSES = 50

    @api.model
    def _validate_spec(self, spec, env=None):
        """Re-derive permission from the allow-list AND the current user's
        own ACLs, every single time — never trust a spec just because it
        was built by our own parser or loaded from a saved tile. This is
        called from three places (live generate, tile save, tile re-fetch)
        on purpose: it must be impossible to reach formatted_read_group()
        without passing through here.

        Validates the COMPLETE shape of the spec: model, every groupby /
        measure / filter / order field name AND its ':suffix' (aggregation,
        time granularity, sort direction), the domain's structure including
        its '&'/|/'!' operators, the groupby dimension count and the limit.
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
        date_field_name = entry.date_field_id.name if entry.date_field_id else None

        # Field types of everything we may group by — needed to enforce
        # that a ':granularity' suffix only ever lands on date/datetime
        # fields. Read off the allow-list entry itself (no fields_get()
        # round-trip): these are exactly the fields validation admits.
        field_types = {f.name: f.ttype for f in entry.field_ids}
        if date_field_name:
            field_types[date_field_name] = entry.date_field_id.ttype

        # --- groupby -------------------------------------------------------
        # Both aggregation keys must EXPLICITLY exist: _run_spec() indexes
        # them directly, so a spec that merely omits them would pass every
        # per-value check below and still blow up with a KeyError later.
        if 'groupby' not in spec or 'measures' not in spec:
            raise ValidationError(
                _("Query spec must define both 'groupby' and 'measures'."))
        # The entry's own date_field_id is implicitly groupable WHEN time-
        # bucketed ('date_order:month') — that is that field's documented
        # purpose ("time-trend groupings") even though admins don't have
        # to also list it under field_ids. A bare date_field_id with no
        # granularity still requires explicit field_ids membership.
        groupby = spec.get('groupby') or []
        if not isinstance(groupby, list) or not all(isinstance(g, str) for g in groupby):
            raise ValidationError(_("Invalid GROUP BY value in query spec."))
        if len(groupby) > self._MAX_GROUPBY:
            raise ValidationError(
                _("Too many GROUP BY dimensions (maximum %s).") % self._MAX_GROUPBY)
        for gb in groupby:
            field_name, _sep, granularity = gb.partition(':')
            if field_name not in allowed_fields and field_name != date_field_name:
                raise ValidationError(
                    _("Field '%s' is not allow-listed for grouping on %s.")
                    % (field_name, model_name))
            if granularity:
                if granularity not in self._ALLOWED_GRANULARITIES:
                    raise ValidationError(
                        _("Invalid time granularity '%s' in query spec.") % granularity)
                if field_types.get(field_name) not in ('date', 'datetime'):
                    raise ValidationError(
                        _("Field '%s' is not a date field and cannot be grouped "
                          "by '%s'.") % (field_name, granularity))

        # --- measures ------------------------------------------------------
        measures = spec.get('measures') or []
        if not isinstance(measures, list) or not all(isinstance(m, str) for m in measures):
            raise ValidationError(_("Invalid measure in query spec."))
        for m in measures:
            field_name, _sep, agg = m.partition(':')
            if field_name not in allowed_measures:
                raise ValidationError(
                    _("Field '%s' is not allow-listed as a measure on %s.")
                    % (field_name, model_name))
            if agg and agg not in self._ALLOWED_AGGREGATORS:
                raise ValidationError(
                    _("Invalid aggregation '%s' for measure '%s'.") % (agg, field_name))

        # --- domain --------------------------------------------------------
        # Every clause gets an explicit decision here — malformed entries
        # are REJECTED, never silently passed through to the ORM, and the
        # only accepted non-leaf tokens are the three structural operators.
        domain = spec.get('domain') or []
        if not isinstance(domain, list):
            raise ValidationError(_("Invalid filter in query spec."))
        if len(domain) > self._MAX_DOMAIN_CLAUSES:
            raise ValidationError(
                _("Too many filter clauses (maximum %s).") % self._MAX_DOMAIN_CLAUSES)
        # Arity balance: each token above is checked in isolation (a lone
        # '&'/'|'/'!' is itself a syntactically valid token, and a lone
        # 3-tuple leaf is itself a syntactically valid, allow-listed leaf),
        # but nothing yet verifies the domain as a WHOLE is a balanced
        # prefix expression. An unbalanced domain (e.g. ['&', (leaf,)])
        # passes every per-token check below and then raises a plain
        # ValueError deep inside formatted_read_group() — never an
        # odoo.exceptions.ValidationError — which nothing else in this
        # module catches. Verify arity here, before any clause reaches
        # the ORM, by walking the domain in reverse: each leaf pushes one
        # completed operand, '!' consumes/replaces one, and '&'/'|'
        # consume two and replace them with one. A balanced domain must
        # end with exactly one operand left on the stack.
        operand_count = 0
        for clause in reversed(domain):
            if isinstance(clause, str) and clause in ('&', '|'):
                if operand_count < 2:
                    raise ValidationError(
                        _("Malformed filter: '%s' is missing an operand.") % clause)
                operand_count -= 1
            elif isinstance(clause, str) and clause == '!':
                if operand_count < 1:
                    raise ValidationError(
                        _("Malformed filter: '!' is missing an operand."))
            else:
                operand_count += 1
        if domain and operand_count != 1:
            raise ValidationError(
                _("Malformed filter: operators and clauses are unbalanced."))
        for clause in domain:
            if isinstance(clause, str) and clause in self._DOMAIN_LOGIC_OPERATORS:
                continue
            if not isinstance(clause, (list, tuple)) or len(clause) != 3:
                raise ValidationError(_("Invalid filter clause in query spec."))
            field_name = clause[0]
            if not isinstance(field_name, str) or (
                    field_name not in allowed_fields and field_name != date_field_name):
                raise ValidationError(
                    _("Field '%s' is not allow-listed for filtering on %s.")
                    % (field_name, model_name))

        # --- orderby ---------------------------------------------------------
        # spec['orderby']/spec['limit'] are 100% client-controlled on the
        # run_manual and tile/save endpoints and were previously never
        # checked here — Odoo's own _read_group_orderby() accepts ANY
        # real field on the model as an order term (as 'field:agg'), not
        # just fields already in groupby/measures, so an unvalidated
        # orderby could silently order results by a field the allow-list
        # deliberately excluded (a side-channel on that field's values).
        # Order terms must reference only fields already vetted above,
        # with a known aggregation suffix and direction.
        allowed_order_fields = allowed_fields | allowed_measures
        orderby = spec.get('orderby')
        if orderby is not None and not isinstance(orderby, str):
            raise ValidationError(_("Invalid order in query spec."))
        if orderby:
            for part in orderby.split(','):
                tokens = part.strip().split()
                if not tokens:
                    raise ValidationError(_("Invalid order in query spec."))
                field_name, _sep, agg = tokens[0].partition(':')
                if not field_name or field_name not in allowed_order_fields:
                    raise ValidationError(
                        _("Field '%s' is not allow-listed for ordering on %s.")
                        % (field_name, model_name))
                if agg and agg not in self._ALLOWED_AGGREGATORS:
                    raise ValidationError(
                        _("Invalid aggregation '%s' in order term '%s'.")
                        % (agg, tokens[0]))
                if len(tokens) > 2 or (
                        len(tokens) == 2
                        and tokens[1] not in self._ALLOWED_ORDER_DIRECTIONS):
                    raise ValidationError(
                        _("Invalid sort direction in order term '%s'.") % part.strip())

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
        """Best-effort phrase suggestions for one freshly-discovered MODEL —
        the model's own name/label, plus (via _create_field_synonyms) each
        allow-listed field's label. Never overwrites or collides with a
        phrase that already exists anywhere (active or not): the parser
        resolves each phrase to exactly one row, so a silent duplicate
        would make matching arbitrary later. Rows are created inactive,
        same as the allow-list entry they belong to.
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

        if to_create:
            self.env['ai.dashboard.synonym'].sudo().create(to_create)

        return new_phrases | self._create_field_synonyms(
            entry.model_id, entry.field_ids, entry.measure_field_ids,
            existing_phrases | new_phrases)

    def _create_field_synonyms(self, model_id, groupby_fields, measure_fields, existing_phrases):
        """Inactive draft ai.dashboard.synonym rows for a set of fields.
        Shared by both discovery paths — a brand-new model's initial
        field_ids/measure_field_ids (via _create_draft_synonyms above) and
        _discover_new_fields()'s candidates on a model this dashboard
        already knows. Creating a synonym here never makes anything
        queryable by itself: KpiPromptParser only ever matches ACTIVE rows
        (_synonym_domain), and even an active match still has to clear
        _validate_spec()'s own field_ids/measure_field_ids check before any
        query can run. The one place that actually widens what's queryable
        is action_promote_discovered_fields, and only for fields an admin
        explicitly accepted.
        """
        new_phrases = set()
        to_create = []

        def add(phrase, values):
            phrase = self._clean_phrase(phrase)
            if len(phrase) < 3 or phrase in existing_phrases or phrase in new_phrases:
                return
            new_phrases.add(phrase)
            to_create.append({**values, 'phrase': phrase, 'active': False})

        for field in measure_fields:
            add(field.field_description, {
                'slot_type': 'measure', 'model_id': model_id.id,
                'value': f"{field.name}:sum",
            })

        for field in groupby_fields:
            add(field.field_description, {
                'slot_type': 'groupby', 'model_id': model_id.id,
                'value': field.name,
            })

        if to_create:
            self.env['ai.dashboard.synonym'].sudo().create(to_create)
        return new_phrases

    @api.model
    def _discover_new_fields(self):
        """For models this dashboard already knows about (an active
        allow-list entry exists), pick up fields added SINCE — typically
        because a newly installed/upgraded module extended that model.
        _discover_new_models() above only ever looks for models it has
        never seen; this is the sibling that keeps an already-configured
        model's vocabulary from going stale as your Odoo instance grows.

        Same safety posture throughout: nothing here ever adds a field to
        field_ids/measure_field_ids itself (see the class docstring —
        'never default-allow a field by omission'). It only records the
        field as a reviewable candidate (discovered_field_ids) and
        proposes an inactive draft synonym for it; both stay inert until
        action_promote_discovered_fields is used. Safe to call repeatedly.
        """
        entries = self.sudo().search([('active', '=', True)])
        if not entries:
            return self.browse()

        existing_phrases = set(
            self.env['ai.dashboard.synonym'].sudo().with_context(active_test=False)
            .search([]).mapped('phrase')
        )
        touched = self.browse()
        for entry in entries:
            Model = self.env.get(entry.model_name)
            if Model is None or not getattr(Model, '_auto', False):
                continue

            already_known = entry.field_ids | entry.measure_field_ids | entry.discovered_field_ids
            usable = entry.model_id.field_id.filtered(
                lambda f: f.store and f.id not in already_known.ids
                and f.name not in self._DISCOVERY_EXCLUDED_FIELD_NAMES)
            groupby_fields = usable.filtered(lambda f: f.ttype in self._DISCOVERY_GROUPBY_TTYPES)
            measure_fields = usable.filtered(lambda f: f.ttype in self._DISCOVERY_MEASURE_TTYPES)
            new_fields = groupby_fields | measure_fields
            if not new_fields:
                continue

            entry.discovered_field_ids = entry.discovered_field_ids | new_fields
            existing_phrases |= self._create_field_synonyms(
                entry.model_id, groupby_fields, measure_fields, existing_phrases)
            touched |= entry

        if touched:
            _logger.info(
                "Smart KPI Dashboard: found new field(s) on %d already-"
                "configured model(s) (%s) — review under Configuration ▸ "
                "Allowed Models ▸ Discovered Fields.", len(touched),
                ', '.join(touched.mapped('model_name')))
        return touched

    def action_promote_discovered_fields(self):
        """Admin-triggered: move every currently-discovered (pending-
        review) field on this entry into the real allow-list — split into
        field_ids or measure_field_ids by type — and activate the draft
        synonym rows _create_field_synonyms proposed for them. This is the
        one place in the module that turns a discovery candidate into
        something a prompt can actually use — local parsing reads straight
        off field_ids/measure_field_ids, so promoting here is enough to
        make the field usable.
        """
        for entry in self:
            if not entry.discovered_field_ids:
                continue
            groupby_add = entry.discovered_field_ids.filtered(
                lambda f: f.ttype in self._DISCOVERY_GROUPBY_TTYPES)
            measure_add = entry.discovered_field_ids.filtered(
                lambda f: f.ttype in self._DISCOVERY_MEASURE_TTYPES)

            synonym_domain = [
                ('model_id', '=', entry.model_id.id),
                ('active', '=', False),
                '|',
                '&', ('slot_type', '=', 'groupby'), ('value', 'in', groupby_add.mapped('name')),
                '&', ('slot_type', '=', 'measure'),
                ('value', 'in', [f"{f.name}:sum" for f in measure_add]),
            ]
            self.env['ai.dashboard.synonym'].sudo().search(synonym_domain).write({'active': True})

            entry.write({
                'field_ids': [(4, f.id) for f in groupby_add],
                'measure_field_ids': [(4, f.id) for f in measure_add],
                'discovered_field_ids': [(5, 0, 0)],
            })
        return True

    @api.model
    def _discover_new_fields_action(self):
        """Manual trigger, same relationship to _discover_new_fields() as
        _discover_new_models_action() has to _discover_new_models()."""
        touched = self._discover_new_fields()
        if not touched:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Smart KPI Dashboard"),
                    'message': _("No new fields found on any configured model."),
                    'type': 'info',
                },
            }
        return {
            'type': 'ir.actions.act_window',
            'name': _("Models With Newly Discovered Fields — Review & Promote"),
            'res_model': 'ai.dashboard.allowlist',
            'view_mode': 'list,form',
            'domain': [('id', 'in', touched.ids)],
        }

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
