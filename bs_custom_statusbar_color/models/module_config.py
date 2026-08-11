from lxml import etree

from odoo import Command, api, fields, models


class CustomStatusbarModuleConfig(models.Model):
    """A user-created statusbar coloring rule for a single model.

    The user creates one of these per model they want to color: name it,
    pick the model, and its statusbar states are discovered and shown for
    coloring. Nothing is pre-populated - there's no automatic list of
    installed modules.
    """

    _name = "custom.statusbar.module.config"
    _description = "Custom Statusbar Color Rule"
    _order = "name"

    name = fields.Char(required=True, help="A label for this rule, e.g. 'Sales Order Colors'.")
    # ondelete="cascade" is intentional: if the module defining this model
    # is later uninstalled, the ir.model record is removed and this rule
    # (plus its states, via the same cascade on state_config.model_id) is
    # deleted along with it rather than left dangling. This is a silent,
    # by-design data loss for any rule that targeted a since-uninstalled
    # module - there is nothing meaningful left to keep it pointed at.
    model_id = fields.Many2one(
        "ir.model",
        required=True,
        ondelete="cascade",
        index=True,
        help="The model whose statusbar states you want to color.",
    )
    enabled = fields.Boolean(
        help="Apply the colors configured below wherever this model's statusbar is shown.",
    )
    state_config_ids = fields.One2many(
        "custom.statusbar.state.config",
        "module_config_id",
    )
    state_count = fields.Integer(compute="_compute_state_count")

    @api.depends("state_config_ids")
    def _compute_state_count(self):
        """Count how many states have been discovered for this rule."""
        for rule in self:
            rule.state_count = len(rule.state_config_ids)

    @api.onchange("model_id")
    def _onchange_model_id(self):
        """Populate states for the newly picked model right away.

        Entirely in-memory (via Command tuples) since the rule may not be
        saved yet - this is what makes the states show up immediately
        after picking a model, without an extra button click.
        """
        self.state_config_ids = [Command.clear()]
        if not self.model_id:
            return None
        access_warning = self._check_model_readable(self.model_id.model)
        if access_warning:
            return access_warning
        model_obj = self.env.get(self.model_id.model)
        field_name = self._find_statusbar_field(model_obj)
        if not field_name:
            return {
                "warning": {
                    "title": "No statusbar field found",
                    "message": (
                        "%s doesn't have any field rendered with "
                        'widget="statusbar" in its views.'
                    )
                    % (self.model_id.name or self.model_id.model),
                }
            }
        field_description = model_obj.fields_get([field_name]).get(field_name, {})
        selection = field_description.get("selection") or []
        self.state_config_ids = [
            Command.create(
                {
                    "model_id": self.model_id.id,
                    "field_name": field_name,
                    "state_value": value,
                    "state_label": label,
                    "sequence": sequence,
                }
            )
            for sequence, (value, label) in enumerate(selection)
        ]
        return None

    def action_scan_states(self):
        """Re-sync this rule's states against the model's current statusbar field.

        Safe to call on an already-saved rule: creates newly appeared
        states, fixes sequence on existing ones, and removes states that
        no longer correspond to a real statusbar field. Existing colors
        are left untouched.
        """
        for rule in self:
            rule._scan_states()
        return True

    def _scan_states(self):
        """Sync statusbar states for this rule's model against what's really in views."""
        self.ensure_one()
        if not self.model_id:
            return
        if self._check_model_readable(self.model_id.model):
            # Caller can't read this model at all; don't touch its states
            # (leaves any existing colored-but-now-inaccessible states
            # untouched rather than deleting them, which would happen if
            # this fell through to the "no statusbar field" branch below).
            return
        model_obj = self.env.get(self.model_id.model)
        field_name = self._find_statusbar_field(model_obj)
        if not field_name:
            if self.state_config_ids:
                self.state_config_ids.unlink()
            return
        existing_by_key = {
            (state.model_id.id, state.field_name, state.state_value): state
            for state in self.state_config_ids
        }
        vals_list = self._sync_state_sequence(self.model_id, model_obj, field_name, existing_by_key)
        self._retire_stale_states(field_name)
        if vals_list:
            self.env["custom.statusbar.state.config"].create(vals_list)

    def _retire_stale_states(self, field_name):
        """Drop states tied to a field that's no longer the detected statusbar.

        If the model's views changed such that a different field now
        qualifies as the statusbar (e.g. a new higher-priority view was
        installed), states from the old field are stale. An uncolored
        stale state carries no information and is safe to delete
        outright. One that already has a color configured is instead
        disabled and kept rather than silently destroyed, so a rescan
        can never make a user's existing color choice vanish without a
        trace.
        """
        stale = self.state_config_ids.filtered(lambda state: state.field_name != field_name)
        if not stale:
            return
        colored_stale = stale.filtered(lambda state: state.default_color or state.in_state_color)
        uncolored_stale = stale - colored_stale
        if uncolored_stale:
            uncolored_stale.unlink()
        if colored_stale:
            colored_stale.write({"enabled": False})

    def _sync_state_sequence(self, model, model_obj, field_name, existing_by_key):
        """Create missing states and fix stale sequence values for existing ones.

        Returns create-vals for states not yet tracked for this model.
        """
        field_description = model_obj.fields_get([field_name]).get(field_name, {})
        selection = field_description.get("selection") or []
        vals_list = []
        for sequence, (value, label) in enumerate(selection):
            key = (model.id, field_name, value)
            existing_state = existing_by_key.get(key)
            if existing_state is not None:
                if existing_state.sequence != sequence:
                    existing_state.sequence = sequence
                continue
            vals_list.append(
                {
                    "module_config_id": self.id,
                    "model_id": model.id,
                    "field_name": field_name,
                    "state_value": value,
                    "state_label": label,
                    "sequence": sequence,
                }
            )
        return vals_list

    def _check_model_readable(self, model_name):
        """Return a warning dict if the current user cannot read model_name, else None.

        _find_statusbar_field()/fields_get() run with the calling user's
        privileges but don't themselves enforce model-level ACLs (schema
        introspection isn't row data), so without this check a user who
        merely has read access to this app's own models (granted broadly
        to base.group_user) could pick an arbitrary model_id - including
        one they have no rights to at all - and still get back that
        model's statusbar field name and selection labels. Blocking it
        here keeps the discovery feature scoped to models the user could
        already see.
        """
        if not self.env["ir.model.access"].check(model_name, "read", raise_exception=False):
            return {
                "warning": {
                    "title": "Access denied",
                    "message": (
                        "You don't have access to %s, so its statusbar "
                        "states can't be inspected."
                    )
                    % model_name,
                }
            }
        return None

    def _find_statusbar_field(self, model_obj):
        """Locate the selection field actually rendered as a statusbar widget.

        Only a field explicitly bound to widget="statusbar" in at least
        one form view for this model qualifies, so only real statusbars
        show up in this app - not every 'state'-named selection field.
        """
        if model_obj is None:
            return None
        views = self.env["ir.ui.view"].search(
            [
                ("model", "=", model_obj._name),
                ("type", "=", "form"),
                ("arch_db", "like", 'widget="statusbar"'),
            ],
            order="priority, id",
        )
        for view in views:
            field_name = self._extract_statusbar_field_name(view.arch_db or "")
            if not field_name:
                continue
            field = model_obj._fields.get(field_name)
            if field is not None and field.type == "selection":
                return field_name
        return None

    def _extract_statusbar_field_name(self, arch):
        """Return the name of the first real <field> element using widget="statusbar".

        Parses the arch as XML (lxml) rather than pattern-matching the
        raw text, so a widget="statusbar" string that merely appears
        inside some other attribute's value (e.g. a context or help
        string) can never be mistaken for an actual statusbar field.
        """
        if not arch:
            return None
        try:
            tree = etree.fromstring(arch.encode())
        except etree.XMLSyntaxError:
            return None
        for node in tree.iter("field"):
            if node.get("widget") == "statusbar":
                name = node.get("name")
                if name:
                    return name
        return None

    @api.model_create_multi
    def create(self, vals_list):
        """Create the rule, then (re)derive its states purely server-side.

        The onchange populates state_config_ids in-memory so the states
        show up live as soon as a model is picked, before the rule is
        even saved. But whatever the client sends for a brand-new
        one2many like that isn't reliably complete once it's turned into
        a create payload, which was tripping "mandatory field not set"
        errors on save. Since there are no pre-existing states worth
        preserving for a rule that doesn't exist yet, it's simplest and
        most robust to just drop whatever came in for state_config_ids
        and rebuild it with a real, fully-specified server-side create
        via _scan_states (the same path "Scan States" already uses).
        """
        for vals in vals_list:
            vals.pop("state_config_ids", None)
        records = super().create(vals_list)
        for record in records:
            if record.model_id:
                record._scan_states()
        records.filtered("enabled")._disable_conflicting_rules()
        records._notify_color_update()
        return records

    def write(self, vals):
        result = super().write(vals)
        if vals.get("enabled"):
            self.filtered("enabled")._disable_conflicting_rules()
        self._notify_color_update()
        return result

    def _disable_conflicting_rules(self):
        """Keep at most one enabled rule per model.

        Two enabled rules covering the same model would make the color
        lookup ambiguous (whichever one happens to load last silently
        wins). Enabling a rule for a model disables any other rule
        already enabled for that same model instead.
        """
        claimed_model_ids = set()
        for rule in self:
            if not rule.model_id:
                continue
            if rule.model_id.id in claimed_model_ids:
                # Another rule in this same batch already claimed the
                # model; this one loses rather than the two disabling
                # each other.
                rule.write({"enabled": False})
                continue
            claimed_model_ids.add(rule.model_id.id)
            conflicting = self.search(
                [
                    ("model_id", "=", rule.model_id.id),
                    ("id", "!=", rule.id),
                    ("enabled", "=", True),
                ]
            )
            if conflicting:
                conflicting.write({"enabled": False})

    def _notify_color_update(self):
        """Push a bus notification so open sessions refresh their color cache."""
        self.env["bus.bus"]._sendone(
            "custom_statusbar", "custom_statusbar.colors_updated", {}
        )
