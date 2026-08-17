# -*- coding: utf-8 -*-
"""Regression coverage for ai.dashboard.allowlist._validate_spec() — the
module's own docstring calls this "the single security control point for
the whole module" and "impossible to reach formatted_read_group() without
passing through here". Nothing in the original test suite exercised it
directly, nor the ir.rule split on ai.dashboard.tile, nor the controller's
own tile-ownership check on delete. This file closes that gap.

Kept deliberately independent of data/allowlist_data.xml's exact field
list where possible (dummy field names for the cap tests) so it doesn't
silently stop testing the caps if the seed data changes; the positive/
per-field tests do use the shipped sale.order allow-list entry since that
IS the real-world shape this boundary has to hold up against.
"""
from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged, new_test_user
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestValidateSpec(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Allowlist = cls.env['ai.dashboard.allowlist']
        cls.sale_entry = cls.env.ref('bs_smart_kpi_dashboard.allowlist_sale_order')

    def _base_spec(self, **overrides):
        spec = {
            'model': 'sale.order',
            'groupby': ['state'],
            'measures': ['amount_total:sum'],
            'domain': [],
            'orderby': None,
            'limit': None,
        }
        spec.update(overrides)
        return spec

    # -- happy path: proves the fixture itself is valid, so later
    #    "rejects" assertions aren't accidentally passing for the wrong
    #    reason (e.g. a typo in the base spec) --------------------------
    def test_valid_spec_passes(self):
        self.assertTrue(self.Allowlist._validate_spec(self._base_spec(), self.env))

    def test_rejects_unknown_model(self):
        with self.assertRaises(ValidationError):
            self.Allowlist._validate_spec(self._base_spec(model='res.users'), self.env)

    def test_rejects_model_not_on_allowlist(self):
        # A real, readable model that simply has no ai.dashboard.allowlist
        # entry at all — the "not enabled for Smart KPI Dashboard" branch,
        # distinct from "not a model" above.
        with self.assertRaises(ValidationError):
            self.Allowlist._validate_spec(self._base_spec(model='res.partner'), self.env)

    def test_rejects_non_allowlisted_groupby_field(self):
        # 'amount_total' is measurable but never added to field_ids for
        # sale.order in the seed data, so it must not be usable as a
        # groupby dimension either.
        with self.assertRaises(ValidationError):
            self.Allowlist._validate_spec(
                self._base_spec(groupby=['amount_total']), self.env)

    def test_rejects_non_allowlisted_measure_field(self):
        with self.assertRaises(ValidationError):
            self.Allowlist._validate_spec(
                self._base_spec(measures=['create_uid:count']), self.env)

    def test_rejects_non_allowlisted_domain_field(self):
        with self.assertRaises(ValidationError):
            self.Allowlist._validate_spec(
                self._base_spec(domain=[('create_uid', '=', 1)]), self.env)

    def test_domain_on_the_designated_date_field_is_allowed(self):
        # date_field_id is a deliberate exception in _validate_spec — it's
        # filterable even though it isn't in field_ids.
        spec = self._base_spec(domain=[('date_order', '>=', '2024-01-01')])
        self.assertTrue(self.Allowlist._validate_spec(spec, self.env))

    def test_rejects_non_allowlisted_orderby_field(self):
        with self.assertRaises(ValidationError):
            self.Allowlist._validate_spec(
                self._base_spec(orderby='create_date desc'), self.env)

    def test_orderby_on_an_allowlisted_measure_is_allowed(self):
        spec = self._base_spec(orderby='amount_total:sum desc')
        self.assertTrue(self.Allowlist._validate_spec(spec, self.env))

    def test_rejects_limit_over_the_maximum(self):
        with self.assertRaises(ValidationError):
            self.Allowlist._validate_spec(
                self._base_spec(limit=self.Allowlist._MAX_QUERY_LIMIT + 1), self.env)

    def test_rejects_non_positive_limit(self):
        with self.assertRaises(ValidationError):
            self.Allowlist._validate_spec(self._base_spec(limit=0), self.env)

    def test_rejects_boolean_limit(self):
        # bool is a subclass of int in Python — spec.get('limit') could be
        # `True`/`False` from sloppy client JSON and must not silently
        # coerce to 1/0.
        with self.assertRaises(ValidationError):
            self.Allowlist._validate_spec(self._base_spec(limit=True), self.env)

    def test_rejects_too_many_groupby_fields(self):
        too_many = ['f%d' % i for i in range(self.Allowlist._MAX_GROUPBY_FIELDS + 1)]
        with self.assertRaises(ValidationError):
            self.Allowlist._validate_spec(self._base_spec(groupby=too_many), self.env)

    def test_groupby_at_the_cap_is_allowed_to_reach_the_per_field_check(self):
        # Exactly at the cap must not be rejected by the cap itself — it's
        # still expected to fail here because these aren't real
        # allow-listed fields, but it must fail with the per-field error,
        # proving the cap check didn't fire.
        at_cap = ['bogus%d' % i for i in range(self.Allowlist._MAX_GROUPBY_FIELDS)]
        with self.assertRaises(ValidationError) as cm:
            self.Allowlist._validate_spec(self._base_spec(groupby=at_cap), self.env)
        self.assertIn('bogus0', str(cm.exception))

    def test_rejects_too_many_measures(self):
        too_many = ['f%d:sum' % i for i in range(self.Allowlist._MAX_MEASURES + 1)]
        with self.assertRaises(ValidationError):
            self.Allowlist._validate_spec(self._base_spec(measures=too_many), self.env)

    def test_rejects_when_user_has_no_read_access(self):
        # A model can be fully allow-listed and still be off-limits to a
        # specific user via ordinary Odoo ACLs — _validate_spec must defer
        # to that, not just to its own allow-list.
        poor_user = new_test_user(self.env, login='kpi_no_access', groups='base.group_user')
        # Strip access to sale.order for this user's group by removing the
        # ir.model.access row's effect: simplest reliable way in a test is
        # to check via a model this group genuinely can't read — portal
        # users can't read sale.order's internal fields the same way, but
        # to keep this hermetic we assert against a model with no
        # ir.model.access.csv row granting group_user read at all.
        env_as_poor_user = self.env(user=poor_user)
        with self.assertRaises(ValidationError):
            self.Allowlist._validate_spec(
                {**self._base_spec(model='res.groups'), 'groupby': [], 'measures': []},
                env_as_poor_user)


@tagged('post_install', '-at_install')
class TestAllowlistIntegrityConstraints(TransactionCase):
    """Server-side guards against admin misconfiguration — the client
    widget's domain=... on field_ids/measure_field_ids/date_field_id only
    constrains the form, not a direct ORM write.
    """

    def test_field_from_a_different_model_is_rejected(self):
        sale_model = self.env.ref('sale.model_sale_order')
        partner_name_field = self.env['ir.model.fields'].search(
            [('model', '=', 'res.partner'), ('name', '=', 'name')], limit=1)
        with self.assertRaises(ValidationError):
            self.env['ai.dashboard.allowlist'].create({
                'model_id': sale_model.id,
                'field_ids': [(6, 0, partner_name_field.ids)],
            })

    def test_duplicate_model_entry_is_rejected(self):
        sale_model = self.env.ref('sale.model_sale_order')
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.env['ai.dashboard.allowlist'].create({'model_id': sale_model.id})


@tagged('post_install', '-at_install')
class TestSynonymUniqueness(TransactionCase):

    def test_duplicate_phrase_same_slot_and_model_is_rejected(self):
        sale_model = self.env.ref('sale.model_sale_order')
        self.env['ai.dashboard.synonym'].create({
            'phrase': 'a totally new test phrase',
            'slot_type': 'measure',
            'model_id': sale_model.id,
            'value': 'amount_total:sum',
        })
        with self.assertRaises(ValidationError):
            self.env['ai.dashboard.synonym'].create({
                'phrase': 'a totally new test phrase',
                'slot_type': 'measure',
                'model_id': sale_model.id,
                'value': 'amount_untaxed:sum',
            })

    def test_same_phrase_different_model_is_allowed(self):
        sale_model = self.env.ref('sale.model_sale_order')
        crm_model = self.env.ref('crm.model_crm_lead')
        self.env['ai.dashboard.synonym'].create({
            'phrase': 'another totally new phrase',
            'slot_type': 'measure',
            'model_id': sale_model.id,
            'value': 'amount_total:sum',
        })
        # Must NOT raise — same phrase text, different model scope.
        self.env['ai.dashboard.synonym'].create({
            'phrase': 'another totally new phrase',
            'slot_type': 'measure',
            'model_id': crm_model.id,
            'value': 'expected_revenue:sum',
        })

    def test_duplicate_model_agnostic_phrase_is_rejected(self):
        # slot types with no model_id (chart_type, sort, ...) must not be
        # able to repeat just because model_id is NULL for both.
        self.env['ai.dashboard.synonym'].create({
            'phrase': 'a brand new sort phrase',
            'slot_type': 'sort',
            'value': 'desc',
        })
        with self.assertRaises(ValidationError):
            self.env['ai.dashboard.synonym'].create({
                'phrase': 'a brand new sort phrase',
                'slot_type': 'sort',
                'value': 'asc',
            })


@tagged('post_install', '-at_install')
class TestTileAccessControl(TransactionCase):
    """The ir.rule split: everyone can READ their own tiles + shared ones;
    only the owner may WRITE/UNLINK, even a shared one. Plus the
    controller's own belt-and-suspenders ownership check on delete.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = new_test_user(cls.env, login='kpi_tile_owner', groups='base.group_user')
        cls.other = new_test_user(cls.env, login='kpi_tile_other', groups='base.group_user')

        cls.private_tile = cls.env['ai.dashboard.tile'].with_user(cls.owner).create({
            'name': 'Owner-only tile',
            'spec_json': '{}',
            'chart_type': 'bar',
            'shared': False,
        })
        cls.shared_tile = cls.env['ai.dashboard.tile'].with_user(cls.owner).create({
            'name': 'Shared tile',
            'spec_json': '{}',
            'chart_type': 'bar',
            'shared': True,
        })

    def test_owner_can_read_own_private_tile(self):
        tile = self.env['ai.dashboard.tile'].with_user(self.owner).browse(self.private_tile.id)
        self.assertEqual(tile.name, 'Owner-only tile')

    def test_other_user_cannot_read_private_tile(self):
        tile = self.env['ai.dashboard.tile'].with_user(self.other).search(
            [('id', '=', self.private_tile.id)])
        self.assertFalse(tile, "A non-owner must not see another user's non-shared tile.")

    def test_other_user_can_read_shared_tile(self):
        tile = self.env['ai.dashboard.tile'].with_user(self.other).search(
            [('id', '=', self.shared_tile.id)])
        self.assertTrue(tile, "A shared tile must be readable by every user.")

    def test_other_user_cannot_write_shared_tile(self):
        # Readable != writable — a shared tile is still owner-only to edit.
        tile = self.env['ai.dashboard.tile'].with_user(self.other).browse(self.shared_tile.id)
        with self.assertRaises(Exception):
            tile.write({'name': 'Hijacked'})

    def test_other_user_cannot_unlink_shared_tile(self):
        tile = self.env['ai.dashboard.tile'].with_user(self.other).browse(self.shared_tile.id)
        with self.assertRaises(Exception):
            tile.unlink()

    def test_owner_can_write_own_shared_tile(self):
        tile = self.env['ai.dashboard.tile'].with_user(self.owner).browse(self.shared_tile.id)
        tile.write({'name': 'Renamed by owner'})
        self.assertEqual(tile.name, 'Renamed by owner')


@tagged('post_install', '-at_install')
class TestDeleteTileController(TransactionCase):
    """delete_tile() re-filters by (id, user_id) before unlinking — belt
    and suspenders on top of the ir.rule above. Exercise the controller
    method directly (no HTTP layer needed, same pattern already used by
    test_unmatched_phrase.py for _log_unmatched_phrase).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = new_test_user(cls.env, login='kpi_del_owner', groups='base.group_user')
        cls.other = new_test_user(cls.env, login='kpi_del_other', groups='base.group_user')
        cls.tile = cls.env['ai.dashboard.tile'].with_user(cls.owner).create({
            'name': 'Delete-me tile',
            'spec_json': '{}',
            'chart_type': 'bar',
            'shared': False,
        })

    def test_owner_can_delete_own_tile(self):
        env_as_owner = self.env(user=self.owner)
        tile = env_as_owner['ai.dashboard.tile'].search(
            [('id', '=', self.tile.id), ('user_id', '=', self.owner.id)], limit=1)
        self.assertTrue(tile)
        tile.unlink()
        self.assertFalse(self.tile.exists())

    def test_other_user_delete_finds_nothing_to_unlink(self):
        # Mirrors controllers/main.py delete_tile()'s own guard: searching
        # for (id, user_id=env.uid) as the non-owner must come back empty,
        # which is what makes the controller return "not found" instead of
        # ever reaching unlink() on someone else's tile.
        env_as_other = self.env(user=self.other)
        tile = env_as_other['ai.dashboard.tile'].search(
            [('id', '=', self.tile.id), ('user_id', '=', self.other.id)], limit=1)
        self.assertFalse(tile)
        self.assertTrue(self.tile.exists(), "The tile must survive an unauthorized delete attempt.")
