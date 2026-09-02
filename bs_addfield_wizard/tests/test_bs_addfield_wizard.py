import re
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


def _slug(label):
    return 'x_studio_' + re.sub(r'[^a-z0-9]+', '_', label.lower()).strip('_')


@tagged('post_install', '-at_install')
class TestBsAddfieldWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env['bs.addfield.wizard']
        cls.partner_model = cls.env.ref('base.model_res_partner')
        cls.admin = cls.env.ref('base.user_admin')

    def _make_wizard(self, **vals):
        vals.setdefault('target_model_id', self.partner_model.id)
        vals.setdefault('field_type', 'char')
        vals.setdefault('field_label', 'Test Field')
        vals.setdefault('field_name', _slug(vals['field_label']))
        return self.env['bs.addfield.wizard'].create(vals)

    def _run_full_flow(self, **vals):
        wizard = self._make_wizard(**vals)
        wizard.action_next_to_field()
        wizard.action_next_to_preview()
        wizard.action_confirm()
        return wizard

    # -- Unit: field creation per type (spec 10 bullet 1) --------------------
    def test_field_creation_char(self):
        wizard = self._make_wizard(field_type='char', field_label='Nickname')
        field = wizard._create_field('res.partner', 'x_studio_nickname')
        self.assertEqual(field.ttype, 'char')
        self.assertEqual(field.model, 'res.partner')
        self.assertFalse(field.relation)

    def test_field_creation_many2one(self):
        wizard = self._make_wizard(
            field_type='many2one', field_label='Backup Contact',
            relation_model_id=self.partner_model.id)
        field = wizard._create_field('res.partner', 'x_studio_backup_contact')
        self.assertEqual(field.ttype, 'many2one')
        self.assertEqual(field.relation, 'res.partner')

    def test_field_creation_selection_deduplicates_option_keys(self):
        wizard = self._make_wizard(
            field_type='selection', field_label='Tier',
            selection_options='Bronze\nSilver\nGold')
        field = wizard._create_field('res.partner', 'x_studio_tier')
        self.assertEqual(field.ttype, 'selection')
        self.assertEqual(set(field.selection_ids.mapped('name')), {'Bronze', 'Silver', 'Gold'})
        values = field.selection_ids.mapped('value')
        self.assertEqual(len(values), len(set(values)))

    def test_selection_options_reject_duplicates(self):
        wizard = self._make_wizard(
            field_type='selection', field_label='Tier',
            selection_options='Gold\ngold')
        with self.assertRaises(UserError):
            wizard._parse_selection_options()

    # -- Unit: field name validation (explicit, user-editable now) -----------
    def test_field_name_must_have_x_prefix(self):
        wizard = self._make_wizard(field_name='studio_bad')
        with self.assertRaises(UserError):
            wizard._validate_field_name('res.partner')

    def test_field_name_collision_rejected(self):
        wizard = self._make_wizard(field_name='x_name')  # 'name' isn't a real collision by
        # itself (technical names are model-scoped); force a genuine collision instead:
        existing = self.env['ir.model.fields'].create({
            'name': 'x_studio_taken', 'model_id': self.partner_model.id,
            'field_description': 'Taken', 'ttype': 'char',
        })
        self.addCleanup(existing.unlink)
        wizard.field_name = 'x_studio_taken'
        with self.assertRaises(UserError):
            wizard._validate_field_name('res.partner')

    def test_field_name_onchange_suggests_from_label(self):
        wizard = self.env['bs.addfield.wizard'].new({'field_label': 'VIP Tier'})
        wizard._onchange_field_label_suggest_name()
        self.assertEqual(wizard.field_name, 'x_studio_vip_tier')

    # -- Unit: placement detection + fallback (spec 10 bullet 2) -------------
    def test_placement_detects_named_group(self):
        arch = '<form><sheet><group name="main"><field name="x"/></group></sheet></form>'
        name, expr, _position, is_fallback = self.Wizard._detect_placement_from_arch(arch)
        self.assertEqual(name, 'main')
        self.assertEqual(expr, "//group[@name='main']")
        self.assertFalse(is_fallback)

    def test_placement_falls_back_to_sheet(self):
        arch = '<form><sheet><group><field name="x"/></group></sheet></form>'
        name, expr, _position, is_fallback = self.Wizard._detect_placement_from_arch(arch)
        self.assertFalse(name)
        self.assertEqual(expr, '//sheet')
        self.assertTrue(is_fallback)

    def test_placement_skips_layout_only_wrapper_groups(self):
        # A <group> whose only children are other <group> elements (used purely to lay
        # them out side by side, e.g. res.partner's "container_row_2") is not a valid
        # field-insertion target -- a field placed directly in it doesn't render.
        # Confirmed by testing in a real browser: the field was created but invisible.
        arch = (
            '<form><sheet><group name="wrapper">'
            '<group name="left" string="Left"><field name="a"/></group>'
            '<group name="right" string="Right"><field name="b"/></group>'
            '</group></sheet></form>'
        )
        name, expr, _position, is_fallback = self.Wizard._detect_placement_from_arch(arch)
        self.assertEqual(name, 'left')
        self.assertEqual(expr, "//group[@name='left']")
        self.assertFalse(is_fallback)

    def test_placement_falls_back_to_form_root(self):
        arch = '<form><field name="x"/></form>'
        name, expr, _position, is_fallback = self.Wizard._detect_placement_from_arch(arch)
        self.assertFalse(name)
        self.assertEqual(expr, '//form')
        self.assertTrue(is_fallback)

    # -- Unit: notebook-tab placement (requirement 6) -------------------------
    def test_placement_scoped_to_chosen_notebook_page(self):
        arch = (
            '<form><sheet><notebook>'
            '<page name="sales" string="Sales"><group name="g1"><field name="a"/></group></page>'
            '<page name="other" string="Other Info"><group name="g2"><field name="b"/></group></page>'
            '</notebook></sheet></form>'
        )
        name, expr, _position, is_fallback = self.Wizard._detect_placement_from_arch(arch, page_name='sales')
        self.assertEqual(name, 'g1')
        self.assertEqual(expr, "//page[@name='sales']//group[@name='g1']")
        self.assertFalse(is_fallback)
        # Choosing the OTHER tab must not silently land on the first-found group
        # elsewhere in the form -- this is exactly the "not other info always" requirement.
        name2, expr2, _position2, _is_fallback2 = self.Wizard._detect_placement_from_arch(arch, page_name='other')
        self.assertEqual(name2, 'g2')
        self.assertNotEqual(expr2, expr)

    def test_placement_falls_back_within_chosen_page_when_no_group(self):
        arch = (
            '<form><sheet><notebook>'
            '<page name="empty" string="Empty"><field name="a"/></page>'
            '</notebook></sheet></form>'
        )
        name, expr, _position, is_fallback = self.Wizard._detect_placement_from_arch(arch, page_name='empty')
        self.assertFalse(name)
        self.assertEqual(expr, "//page[@name='empty']")
        self.assertTrue(is_fallback)

    def test_list_notebook_pages_from_arch(self):
        arch = (
            '<form><sheet><notebook>'
            '<page name="sales" string="Sales"/><page name="other" string="Other Info"/>'
            '</notebook></sheet></form>'
        )
        pages = self.Wizard._list_notebook_pages_from_arch(arch)
        self.assertEqual(pages, [('sales', 'Sales'), ('other', 'Other Info')])

    def test_notebook_page_typed_value_validated_against_real_tabs(self):
        # notebook_page is a plain Char (not a dynamic Selection -- see the field's
        # docstring in the model for why), so an invalid typed tab name must be rejected
        # with a clear error rather than silently accepted.
        wizard = self._make_wizard(notebook_page='not_a_real_tab')
        with self.assertRaises(UserError):
            wizard._validate_field_definition()
        wizard.notebook_page = 'sales_purchases'  # a real res.partner tab
        wizard._validate_field_definition()  # does not raise

    # -- Unit: automation trigger value validation (spec 10 bullet 3) --------
    def test_automation_trigger_boolean_accepts_and_rejects(self):
        wizard = self._make_wizard(field_type='boolean', automation_trigger_value='true')
        wizard._validate_automation_trigger_value()  # does not raise
        wizard.automation_trigger_value = 'not-a-bool'
        with self.assertRaises(UserError):
            wizard._validate_automation_trigger_value()

    def test_automation_trigger_integer_rejects_non_numeric(self):
        wizard = self._make_wizard(field_type='integer', automation_trigger_value='abc')
        with self.assertRaises(UserError):
            wizard._validate_automation_trigger_value()

    def test_automation_trigger_selection_must_match_option(self):
        wizard = self._make_wizard(
            field_type='selection', selection_options='Bronze\nSilver\nGold',
            automation_trigger_value='Platinum')
        with self.assertRaises(UserError):
            wizard._validate_automation_trigger_value()
        wizard.automation_trigger_value = 'Gold'
        wizard._validate_automation_trigger_value()  # does not raise

    def test_automation_not_offered_for_many2one(self):
        wizard = self._make_wizard(
            field_type='many2one', relation_model_id=self.partner_model.id,
            add_automation=True, automation_notify_user_id=self.admin.id,
            automation_trigger_value='1')
        with self.assertRaises(UserError):
            wizard._validate_field_definition()

    # -- Edge cases (spec 9) ---------------------------------------------------
    def test_many2one_blocked_without_read_access(self):
        model = self.env['ir.model'].create({'name': 'x_no_access', 'model': 'x_no_access'})
        # A freshly created manual model has no ir.model.access rows at all.
        wizard = self._make_wizard(field_type='many2one', relation_model_id=model.id)
        with self.assertRaises(UserError):
            wizard._check_relation_accessible()

    def test_label_collision_warns_not_blocks(self):
        wizard = self._make_wizard(field_label='Name')  # collides with res.partner.name
        wizard._validate_field_definition()  # must not raise
        self.assertTrue(wizard.label_warning)

    # -- Integration: full flow (spec 10 bullet 4) ----------------------------
    def test_full_flow_creates_usable_field_immediately(self):
        wizard = self._run_full_flow(
            field_type='boolean', field_label='Full Flow Field',
            add_automation=True, automation_trigger_value='true',
            automation_notify_user_id=self.admin.id, automation_message='hello')
        self.assertEqual(wizard.state, 'done')
        registry = wizard.result_registry_id
        self.assertTrue(registry)
        field_name = registry.field_id.name
        # Usable immediately, no restart: field is in the live registry and writable.
        self.assertIn(field_name, self.env['res.partner']._fields)
        partner = self.env['res.partner'].create({'name': 'Addfield Test Partner', field_name: True})
        self.assertTrue(partner[field_name])
        # Automation created with the verified-correct (non-deprecated) trigger.
        self.assertEqual(registry.automation_id.trigger, 'on_create_or_write')
        self.assertIn(field_name, registry.automation_id.filter_domain)
        template = registry.automation_id.action_server_ids.template_id
        self.assertTrue(template)
        self.assertEqual(template.partner_to, str(self.admin.partner_id.id))

    def test_full_flow_places_field_in_chosen_tab(self):
        wizard = self._run_full_flow(
            field_type='char', field_label='Tabbed Field', notebook_page='sales_purchases')
        registry = wizard.result_registry_id
        self.assertEqual(registry.notebook_page, 'Sales & Purchase')
        arch = registry.view_id.arch
        self.assertIn("page[@name='sales_purchases']", arch)
        # Must land in a real content group (e.g. "sale"), never the page's outer
        # layout-only wrapper group ("container_row_2") -- see
        # test_placement_skips_layout_only_wrapper_groups for the isolated unit test.
        self.assertNotIn('container_row_2', arch)

    def test_disabled_at_creation_hides_from_view(self):
        wizard = self._run_full_flow(field_type='char', field_label='Off At Creation', field_enabled=False)
        registry = wizard.result_registry_id
        self.assertEqual(registry.state, 'disabled')
        self.assertFalse(registry.view_id.active)

    # -- Regression: metadata indistinguishable from a native field ----------
    def test_created_field_matches_native_shape(self):
        wizard = self._run_full_flow(field_type='char', field_label='Native Shape Field')
        field = wizard.result_registry_id.field_id
        self.assertEqual(field.state, 'manual')
        self.assertTrue(field.name.startswith('x_'))
        model_field = self.env['res.partner']._fields[field.name]
        self.assertEqual(model_field.type, 'char')
        self.assertEqual(model_field.string, 'Native Shape Field')

    # -- Chatter history (requirement 4): add / update / enable-disable / delete ---
    def test_chatter_logs_field_added(self):
        wizard = self._run_full_flow(field_type='char', field_label='Chatter Add Field')
        registry = wizard.result_registry_id
        self.assertTrue(registry.message_ids)
        self.assertIn('added', registry.message_ids[-1].body.lower())

    def test_chatter_logs_enable_disable_and_required_toggle(self):
        wizard = self._run_full_flow(field_type='char', field_label='Chatter Toggle Field')
        registry = wizard.result_registry_id
        before = len(registry.message_ids)
        registry.action_disable_field()
        self.assertEqual(registry.state, 'disabled')
        self.assertFalse(registry.view_id.active)
        registry.action_enable_field()
        self.assertEqual(registry.state, 'active')
        self.assertTrue(registry.view_id.active)
        registry.field_required = True
        self.assertTrue(registry.field_id.required)
        # tracking=True on state/field_required means mail.thread logged each change --
        # tracking messages are deferred to precommit, so flush it before checking.
        self.env.cr.precommit.run()
        self.assertGreater(len(registry.message_ids), before)

    def test_disable_blocked_with_data_uses_confirm_dialog_not_a_hard_block(self):
        # The plain (no-confirm) disable action is only reachable via a button that's
        # invisible when has_data is True in the view; the *confirmed* action must still
        # work programmatically once the warning is accepted -- i.e. it's a UI gate, not
        # a server-side UserError, since disabling never destroys data.
        wizard = self._run_full_flow(field_type='char', field_label='Data Toggle Field')
        registry = wizard.result_registry_id
        field_name = registry.field_id.name
        self.env['res.partner'].create({'name': 'Has Data For Toggle', field_name: 'x'})
        self.assertTrue(registry.has_data)
        registry.action_disable_field_confirmed()
        self.assertEqual(registry.state, 'disabled')

    # -- Integration: removal keeps an audit-log row + reverses field/view/automation --
    def test_remove_field_reverses_field_view_and_automation(self):
        wizard = self._run_full_flow(
            field_type='char', field_label='Removable Field',
            add_automation=True, automation_trigger_value='x',
            automation_notify_user_id=self.admin.id)
        registry = wizard.result_registry_id
        field_id, view_id, automation_id = registry.field_id.id, registry.view_id.id, registry.automation_id.id
        messages_before = len(registry.message_ids)

        remove_wizard = self.env['bs.addfield.remove.wizard'].create({'registry_id': registry.id})
        # Blocked until the dependent automation is explicitly opted into removal too.
        remove_wizard.remove_automation = False
        with self.assertRaises(UserError):
            remove_wizard.action_confirm()
        self.assertTrue(self.env['base.automation'].browse(automation_id).exists())

        remove_wizard.remove_automation = True
        remove_wizard.action_confirm()
        self.assertFalse(self.env['ir.model.fields'].browse(field_id).exists())
        self.assertFalse(self.env['ir.ui.view'].browse(view_id).exists())
        self.assertFalse(self.env['base.automation'].browse(automation_id).exists())
        # The registry row is kept as a permanent audit-log entry (chatter history),
        # not hard-deleted -- only its live links are cleared.
        self.assertTrue(registry.exists())
        self.assertEqual(registry.state, 'deleted')
        self.assertFalse(registry.field_id)
        self.assertFalse(registry.view_id)
        self.assertFalse(registry.automation_id)
        # tracking=True on `state` means the Active -> Deleted transition was chattered
        # (deferred to precommit, so flush it before checking).
        self.env.cr.precommit.run()
        self.assertGreater(len(registry.message_ids), messages_before)

    def test_remove_field_blocks_populated_data_without_confirmation(self):
        wizard = self._run_full_flow(field_type='char', field_label='Data Field')
        registry = wizard.result_registry_id
        field_name = registry.field_id.name
        self.env['res.partner'].create({'name': 'Has Data', field_name: 'something'})
        self.assertTrue(registry.has_data)

        remove_wizard = self.env['bs.addfield.remove.wizard'].create({'registry_id': registry.id})
        with self.assertRaises(UserError):
            remove_wizard.action_confirm()
        self.assertTrue(registry.field_id.exists())

        remove_wizard.confirm_data_loss = True
        remove_wizard.action_confirm()
        self.assertEqual(registry.state, 'deleted')

    def test_deleted_registry_cannot_be_removed_again_or_reenabled(self):
        wizard = self._run_full_flow(field_type='char', field_label='Double Delete Field')
        registry = wizard.result_registry_id
        remove_wizard = self.env['bs.addfield.remove.wizard'].create({'registry_id': registry.id})
        remove_wizard.action_confirm()
        with self.assertRaises(UserError):
            registry.action_open_remove_wizard()
        with self.assertRaises(UserError):
            registry.action_enable_field()

    # -- Partial failure never leaves orphaned metadata -----------------------
    def test_partial_failure_rolls_back_everything(self):
        wizard = self._make_wizard(field_type='char', field_label='Rollback Field')
        wizard.action_next_to_field()
        wizard.action_next_to_preview()
        with patch.object(type(wizard), '_create_view', side_effect=RuntimeError('boom')), \
                self.assertRaises(RuntimeError):
            wizard.action_confirm()
        leftover = self.env['ir.model.fields'].search([
            ('model', '=', 'res.partner'), ('field_description', '=', 'Rollback Field'),
        ])
        self.assertFalse(leftover)
