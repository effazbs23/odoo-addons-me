from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase, new_test_user


class TestModuleConfig(TransactionCase):
    """Regression coverage for the bug classes hit while building this module."""

    def setUp(self):
        super().setUp()
        self.partner_model = self.env["ir.model"]._get("res.partner")

    def test_no_statusbar_field_graceful(self):
        """A model with no widget=statusbar field yields zero states, no crash.

        res.partner has no statusbar field in base+web, so this also
        exercises the "no statusbar field found" branch of _scan_states
        without needing a dependency on any other module.
        """
        rule = self.env["custom.statusbar.module.config"].create(
            {"name": "No Statusbar Here", "model_id": self.partner_model.id}
        )
        self.assertFalse(rule.state_config_ids)
        self.assertEqual(rule.state_count, 0)

    def test_disable_conflicting_rules(self):
        """Enabling a rule disables any other enabled rule for the same model."""
        rule_model = self.env["custom.statusbar.module.config"]
        first = rule_model.create(
            {"name": "First Rule", "model_id": self.partner_model.id, "enabled": True}
        )
        second = rule_model.create(
            {"name": "Second Rule", "model_id": self.partner_model.id, "enabled": True}
        )
        self.assertFalse(first.enabled, "Enabling the second rule must disable the first")
        self.assertTrue(second.enabled)

    def test_disable_conflicting_rules_different_models(self):
        """Two enabled rules for different models must not affect each other."""
        rule_model = self.env["custom.statusbar.module.config"]
        user_model = self.env["ir.model"]._get("res.users")
        partner_rule = rule_model.create(
            {"name": "Partner Rule", "model_id": self.partner_model.id, "enabled": True}
        )
        user_rule = rule_model.create(
            {"name": "User Rule", "model_id": user_model.id, "enabled": True}
        )
        self.assertTrue(partner_rule.enabled)
        self.assertTrue(user_rule.enabled)

    def test_group_user_cannot_write(self):
        """A plain internal user (read-only access) cannot modify a rule."""
        rule = self.env["custom.statusbar.module.config"].create(
            {"name": "Protected Rule", "model_id": self.partner_model.id}
        )
        basic_user = new_test_user(self.env, login="statusbar_basic_user", groups="base.group_user")
        with self.assertRaises(AccessError):
            rule.with_user(basic_user).write({"enabled": True})

    def test_onchange_blocks_model_user_cannot_read(self):
        """Picking a model the user has no read access to must not leak its schema.

        base.group_user has broad read access to this app's own models,
        which would otherwise let a low-privileged user pick an arbitrary
        model_id and get back that model's statusbar field/selection
        labels via the onchange, even for a model they can't read at all.
        ir.cron is restricted to base.group_system by default, so it's a
        convenient stand-in for "a model this user shouldn't see".
        """
        basic_user = new_test_user(self.env, login="statusbar_no_access_user", groups="base.group_user")
        rule_model = self.env["custom.statusbar.module.config"].with_user(basic_user)
        warning = rule_model._check_model_readable("ir.cron")
        self.assertTrue(warning, "A model the user can't read must produce a warning")
        self.assertIn("warning", warning)

    def test_check_model_readable_allows_accessible_model(self):
        """A model the user can read should not be blocked."""
        basic_user = new_test_user(self.env, login="statusbar_access_user", groups="base.group_user")
        rule_model = self.env["custom.statusbar.module.config"].with_user(basic_user)
        self.assertIsNone(rule_model._check_model_readable("res.partner"))

    def test_extract_statusbar_field_name_order_independent(self):
        """The field-tag scan must find widget=statusbar regardless of attribute order."""
        rule_model = self.env["custom.statusbar.module.config"]
        name_then_widget = '<field name="state" widget="statusbar" options="{}"/>'
        widget_then_name = '<field widget="statusbar" name="state"/>'
        no_statusbar = '<field name="state"/>'
        self.assertEqual(
            rule_model._extract_statusbar_field_name(name_then_widget), "state"
        )
        self.assertEqual(
            rule_model._extract_statusbar_field_name(widget_then_name), "state"
        )
        self.assertIsNone(rule_model._extract_statusbar_field_name(no_statusbar))

    def test_retire_stale_states_preserves_colored_ones(self):
        """A rescan must disable, not delete, a stale state that already has a color.

        Simulates the field-name changing between scans (e.g. because a
        higher-priority view now wins) by manually creating a state
        under a fake field name, then asking the rule to retire it.
        """
        rule = self.env["custom.statusbar.module.config"].create(
            {"name": "Retire Test", "model_id": self.partner_model.id}
        )
        colored_state = self.env["custom.statusbar.state.config"].create(
            {
                "module_config_id": rule.id,
                "model_id": self.partner_model.id,
                "field_name": "old_field",
                "state_value": "draft",
                "state_label": "Draft",
                "default_color": "#FF0000",
            }
        )
        uncolored_state = self.env["custom.statusbar.state.config"].create(
            {
                "module_config_id": rule.id,
                "model_id": self.partner_model.id,
                "field_name": "old_field",
                "state_value": "done",
                "state_label": "Done",
            }
        )
        rule._retire_stale_states("new_field")
        self.assertTrue(colored_state.exists(), "A colored stale state must be kept")
        self.assertFalse(colored_state.enabled, "A colored stale state must be disabled")
        self.assertFalse(uncolored_state.exists(), "An uncolored stale state is safe to delete")

    def test_color_must_be_valid_hex(self):
        """default_color/in_state_color must be rejected server-side if not a hex color.

        Guards against any write path that bypasses the JS color picker's
        client-side validation (import, RPC, a future integration).
        """
        rule = self.env["custom.statusbar.module.config"].create(
            {"name": "Hex Validation", "model_id": self.partner_model.id}
        )
        state_model = self.env["custom.statusbar.state.config"]
        with self.assertRaises(ValidationError):
            state_model.create(
                {
                    "module_config_id": rule.id,
                    "model_id": self.partner_model.id,
                    "field_name": "state",
                    "state_value": "draft",
                    "state_label": "Draft",
                    "default_color": "javascript:alert(1)",
                }
            )

    def test_short_and_long_hex_colors_accepted(self):
        """Both 3-digit and 6-digit hex shorthand are valid."""
        rule = self.env["custom.statusbar.module.config"].create(
            {"name": "Hex Shorthand", "model_id": self.partner_model.id}
        )
        state = self.env["custom.statusbar.state.config"].create(
            {
                "module_config_id": rule.id,
                "model_id": self.partner_model.id,
                "field_name": "state",
                "state_value": "draft",
                "state_label": "Draft",
                "default_color": "#F00",
                "in_state_color": "#FF0000",
            }
        )
        self.assertEqual(state.default_color, "#F00")
        self.assertEqual(state.in_state_color, "#FF0000")
