# -*- coding: utf-8 -*-
"""Regression coverage for the module's actual security boundary:
ai.dashboard.allowlist._validate_spec() — plus the per-tile resilience
contract in ai.dashboard.tile.get_dashboard_tiles().

_validate_spec is the ONLY path to formatted_read_group(), and every
client-supplied spec (guided form, tile save, tile reload) passes through
it, so each acceptance/rejection rule here is a security or stability
guarantee, not a nicety:

  - allow-list membership for groupby / measure / filter / order fields
  - ':suffix' validation (aggregation, time granularity, sort direction)
  - domain structure, including '&'/|/'!' operator tokens
  - cost caps (groupby dimension count, limit)
  - the requesting user's own read ACL on the target model

The tile tests pin H-2's contract: one stale/corrupted tile must degrade
to a visible per-tile error, never break the whole dashboard.
"""
import json

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestValidateSpec(TransactionCase):
    """Exercises the gate directly against the seeded allow-list
    (data/allowlist_data.xml): sale.order allows grouping by state/
    partner_id/user_id/team_id, measures amount_total/amount_untaxed,
    date field date_order."""

    def setUp(self):
        super().setUp()
        self.Allowlist = self.env['ai.dashboard.allowlist']
        self.entry = self.Allowlist.search([('model_name', '=', 'sale.order')])
        self.assertTrue(self.entry, "seeded sale.order allow-list entry missing")

    def _spec(self, **over):
        spec = {
            'model': 'sale.order',
            'groupby': ['team_id'],
            'measures': ['amount_total:sum'],
            'domain': [],
            'chart_type': 'bar',
            'limit': None,
            'orderby': None,
        }
        spec.update(over)
        return spec

    def _assert_invalid(self, spec, env=None):
        with self.assertRaises(ValidationError):
            self.Allowlist._validate_spec(spec, env or self.env)

    # --- acceptance -----------------------------------------------------

    def test_valid_spec_passes(self):
        self.assertTrue(self.Allowlist._validate_spec(self._spec(), self.env))

    def test_bare_measure_name_without_aggregation_passes(self):
        spec = self._spec(measures=['amount_total'])
        self.assertTrue(self.Allowlist._validate_spec(spec, self.env))

    def test_date_field_time_bucket_groupby_passes(self):
        """Regression: the parser emits '<date_field>:month' for prompts
        like 'sales by month', and the date field need not be listed in
        field_ids — its documented purpose IS time-trend grouping."""
        spec = self._spec(groupby=['date_order:month'])
        self.assertTrue(self.Allowlist._validate_spec(spec, self.env))

    def test_groupby_cap_boundary_of_three_passes(self):
        spec = self._spec(groupby=['team_id', 'state', 'user_id'])
        self.assertTrue(self.Allowlist._validate_spec(spec, self.env))

    def test_domain_logic_operators_accepted(self):
        spec = self._spec(domain=[
            '|', ('state', '=', 'sale'), ('state', '=', 'draft')])
        self.assertTrue(self.Allowlist._validate_spec(spec, self.env))

    def test_domain_on_date_field_accepted(self):
        spec = self._spec(domain=[('date_order', '>=', '2026-01-01')])
        self.assertTrue(self.Allowlist._validate_spec(spec, self.env))

    def test_orderby_with_valid_direction_passes(self):
        spec = self._spec(orderby='amount_total:sum desc')
        self.assertTrue(self.Allowlist._validate_spec(spec, self.env))

    # --- model ------------------------------------------------------------

    def test_missing_model_raises(self):
        spec = self._spec()
        del spec['model']
        self._assert_invalid(spec)

    def test_unknown_model_raises(self):
        self._assert_invalid(self._spec(model='no.such.model.anywhere'))

    def test_existing_but_not_allowlisted_model_raises(self):
        self._assert_invalid(self._spec(model='res.partner'))

    # --- required keys ------------------------------------------------------

    def test_missing_measures_key_raises(self):
        spec = self._spec()
        del spec['measures']
        self._assert_invalid(spec)

    def test_missing_groupby_key_raises(self):
        spec = self._spec()
        del spec['groupby']
        self._assert_invalid(spec)

    # --- groupby ------------------------------------------------------------

    def test_non_allowlisted_groupby_field_raises(self):
        self._assert_invalid(self._spec(groupby=['amount_total']))

    def test_granularity_on_non_date_field_raises(self):
        self._assert_invalid(self._spec(groupby=['partner_id:month']))

    def test_unknown_granularity_raises(self):
        self._assert_invalid(self._spec(groupby=['date_order:fortnight']))

    def test_too_many_groupby_dimensions_raises(self):
        self._assert_invalid(self._spec(
            groupby=['team_id', 'state', 'user_id', 'partner_id']))

    def test_groupby_wrong_value_type_raises(self):
        self._assert_invalid(self._spec(groupby='team_id'))

    # --- measures -----------------------------------------------------------

    def test_non_allowlisted_measure_raises(self):
        self._assert_invalid(self._spec(measures=['partner_id:sum']))

    def test_unknown_aggregator_raises(self):
        self._assert_invalid(self._spec(measures=['amount_total:bogus']))

    def test_measures_wrong_value_type_raises(self):
        self._assert_invalid(self._spec(measures='amount_total:sum'))

    # --- domain ---------------------------------------------------------------

    def test_malformed_domain_clause_rejected_not_skipped(self):
        """A clause that isn't a leaf tuple nor a known operator must be
        REJECTED — never silently passed through to the ORM."""
        self._assert_invalid(self._spec(domain=[('team_id', '=', 1), 'garbage']))

    def test_domain_unknown_operator_token_rejected(self):
        self._assert_invalid(self._spec(domain=['XOR', ('team_id', '=', 1)]))

    def test_domain_non_allowlisted_field_raises(self):
        self._assert_invalid(self._spec(domain=[('campaign_id', '!=', False)]))

    def test_domain_leaf_with_non_string_field_raises(self):
        self._assert_invalid(self._spec(domain=[(42, '=', 1)]))

    # --- orderby ---------------------------------------------------------------

    def test_orderby_non_allowlisted_field_raises(self):
        self._assert_invalid(self._spec(orderby='create_uid asc'))

    def test_orderby_bad_direction_raises(self):
        self._assert_invalid(self._spec(orderby='amount_total:sum sideways'))

    def test_orderby_trailing_garbage_raises(self):
        self._assert_invalid(self._spec(orderby='amount_total:sum desc extra'))

    def test_orderby_bad_aggregation_suffix_raises(self):
        self._assert_invalid(self._spec(orderby='amount_total:bogus desc'))

    # --- limit -----------------------------------------------------------------

    def test_limit_over_max_raises(self):
        self._assert_invalid(self._spec(limit=self.Allowlist._MAX_QUERY_LIMIT + 1))

    def test_zero_or_negative_limit_raises(self):
        self._assert_invalid(self._spec(limit=0))
        self._assert_invalid(self._spec(limit=-5))

    def test_boolean_limit_raises(self):
        self._assert_invalid(self._spec(limit=True))

    # --- user's own ACLs ---------------------------------------------------------

    def test_user_without_read_access_raises_even_if_allowlisted(self):
        # A user with NO groups holds no ACLs at all (portal/public still
        # get read on some business models like sale.order via their own
        # ACL rows — a bare user is the only guarantee of denial).
        bare_user = self.env['res.users'].create({
            'name': 'KPI No-Group Test',
            'login': 'kpi_nogroup_validate_spec_test',
            'group_ids': [(6, 0, [])],
        })
        self.assertFalse(
            self.env(user=bare_user)['sale.order'].has_access('read'),
            "precondition: a no-group user must not read sale.order")
        self._assert_invalid(self._spec(), self.env(user=bare_user))


@tagged('post_install', '-at_install')
class TestTileResilience(TransactionCase):
    """H-2 contract: get_dashboard_tiles() must return a payload for EVERY
    visible tile, degrading broken ones to a per-tile error instead of
    letting one bad row kill the whole dashboard."""

    def setUp(self):
        super().setUp()
        self.Tile = self.env['ai.dashboard.tile']

    def _good_spec(self):
        return {
            'model': 'sale.order',
            'groupby': ['team_id'],
            'measures': ['amount_total:sum'],
            'domain': [],
            'chart_type': 'bar',
            'limit': None,
            'orderby': None,
        }

    def _payload_for(self, tiles, tile):
        return next(t for t in tiles if t['id'] == tile.id)

    def test_valid_tile_renders_without_error(self):
        tile = self.Tile.create({
            'name': 'good',
            'spec_json': json.dumps(self._good_spec()),
            'chart_type': 'bar',
        })
        payload = self._payload_for(tile.get_dashboard_tiles(), tile)
        self.assertNotIn('error', payload)
        self.assertIn('chart', payload)

    def test_corrupted_spec_json_degrades_to_per_tile_error(self):
        tile = self.Tile.create({
            'name': 'corrupted',
            'spec_json': '{definitely not json',
            'chart_type': 'bar',
        })
        payload = self._payload_for(tile.get_dashboard_tiles(), tile)
        self.assertIn('error', payload)

    def test_stale_tile_referencing_disallowed_measure_degrades(self):
        """Simulates an admin narrowing the allow-list after save: the
        stored spec no longer validates, the tile flags itself instead of
        raising out of get_dashboard_tiles()."""
        stale_spec = {
            **self._good_spec(),
            'measures': ['expected_revenue:sum'],  # crm field, not sale.order's
        }
        tile = self.Tile.create({
            'name': 'stale',
            'spec_json': json.dumps(stale_spec),
            'chart_type': 'bar',
        })
        payload = self._payload_for(tile.get_dashboard_tiles(), tile)
        self.assertIn('error', payload)
        self.assertIn('allow-listed', payload['error'])

    def test_one_bad_tile_does_not_hide_good_tiles(self):
        good = self.Tile.create({
            'name': 'still-good',
            'spec_json': json.dumps(self._good_spec()),
            'chart_type': 'bar',
        })
        self.Tile.create({
            'name': 'broken',
            'spec_json': '{oops',
            'chart_type': 'bar',
        })
        tiles = good.get_dashboard_tiles()
        payload = self._payload_for(tiles, good)
        self.assertNotIn('error', payload)
