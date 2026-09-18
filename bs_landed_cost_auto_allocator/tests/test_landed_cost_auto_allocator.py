# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestLandedCostAutoAllocator(TransactionCase):
    """NOTE: written against the assumed core `stock_landed_costs` field
    names documented in models/stock_landed_cost.py and CHANGELOG.md
    (`split_method`, `quantity`/`weight`/`volume`/`former_cost`/
    `additional_landed_cost`, `compute_landed_cost()`). Not executed
    against a live Odoo instance in this environment - run
    `--test-enable -i bs_landed_cost_auto_allocator` and fix any field-name
    mismatch against the target Odoo 17 database before merging.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.vendor = cls.env['res.partner'].create({'name': 'Global Logistics Ltd'})
        cls.other_vendor = cls.env['res.partner'].create({'name': 'Other Vendor'})

        cls.freight_product = cls.env['product.product'].create({
            'name': 'Freight', 'type': 'service',
        })
        cls.duty_product = cls.env['product.product'].create({
            'name': 'Duty', 'type': 'service',
        })

        # Two products, equal weight (1000 = weight 10.0 * qty 100 vs.
        # weight 10.0 * qty 50 -> not equal on purpose below); kept simple:
        # equal per-unit weight, different quantities/values so weight-
        # based and value-based allocation produce different, independently
        # verifiable splits (mixed-allocation test).
        cls.prod_a = cls.env['product.product'].create({
            'name': 'PRD-001', 'type': 'consu', 'is_storable': True,
            'weight': 10.0, 'volume': 0.02, 'standard_price': 100.0,
        })
        cls.prod_b = cls.env['product.product'].create({
            'name': 'PRD-002', 'type': 'consu', 'is_storable': True,
            'weight': 10.0, 'volume': 0.03, 'standard_price': 120.0,
        })
        cls.prod_no_weight = cls.env['product.product'].create({
            'name': 'PRD-NOWEIGHT', 'type': 'consu', 'is_storable': True,
            'weight': 0.0, 'volume': 0.0, 'standard_price': 50.0,
        })

        cls.picking_type = cls.env.ref('stock.picking_type_in')
        cls.location_supplier = cls.env.ref('stock.stock_location_suppliers')
        cls.location_stock = cls.env.ref('stock.stock_location_stock')

    def _make_picking(self, product_qtys):
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type.id,
            'location_id': self.location_supplier.id,
            'location_dest_id': self.location_stock.id,
        })
        for product, qty in product_qtys:
            self.env['stock.move'].create({
                'name': product.name,
                'product_id': product.id,
                'product_uom_qty': qty,
                'product_uom': product.uom_id.id,
                'picking_id': picking.id,
                'location_id': self.location_supplier.id,
                'location_dest_id': self.location_stock.id,
            })
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            # Field name for "done quantity" varies across Odoo 17 point
            # releases (quantity / quantity_done); set whichever exists.
            if 'quantity' in move._fields:
                move.quantity = move.product_uom_qty
            elif 'quantity_done' in move._fields:
                move.quantity_done = move.product_uom_qty
        picking.button_validate()
        return picking

    def test_rule_matching_priority_order(self):
        Rule = self.env['landed.cost.allocation.rule']
        vendor_and_product_rule = Rule.create({
            'vendor_id': self.vendor.id,
            'product_id': self.freight_product.id,
            'split_method': 'by_weight',
        })
        product_only_rule = Rule.create({
            'product_id': self.freight_product.id,
            'split_method': 'by_volume',
        })
        vendor_only_rule = Rule.create({
            'vendor_id': self.vendor.id,
            'split_method': 'equal',
        })

        # vendor + product both match -> highest priority tier wins.
        self.assertEqual(
            Rule._find_matching_rule(self.vendor.id, self.freight_product.id),
            vendor_and_product_rule,
        )
        # Different vendor, same product -> product-only tier.
        self.assertEqual(
            Rule._find_matching_rule(self.other_vendor.id, self.freight_product.id),
            product_only_rule,
        )
        # Same vendor, different (unrelated) product -> vendor-only tier.
        self.assertEqual(
            Rule._find_matching_rule(self.vendor.id, self.duty_product.id),
            vendor_only_rule,
        )
        # Neither matches -> empty recordset.
        self.assertFalse(
            Rule._find_matching_rule(self.other_vendor.id, self.duty_product.id))

    def test_data_quality_check_blocks_missing_weight(self):
        picking = self._make_picking([(self.prod_no_weight, 5.0)])
        landed_cost = self.env['stock.landed.cost'].create({
            'picking_ids': [(6, 0, picking.ids)],
            'vendor_id': self.vendor.id,
            'cost_lines': [(0, 0, {
                'product_id': self.freight_product.id,
                'name': 'Freight',
                'price_unit': 500.0,
                'split_method': 'by_weight',
            })],
        })
        with self.assertRaises(UserError):
            landed_cost.action_auto_allocate()

    def test_data_quality_check_passes_with_complete_data(self):
        picking = self._make_picking([(self.prod_a, 10.0), (self.prod_b, 10.0)])
        landed_cost = self.env['stock.landed.cost'].create({
            'picking_ids': [(6, 0, picking.ids)],
            'vendor_id': self.vendor.id,
            'cost_lines': [(0, 0, {
                'product_id': self.freight_product.id,
                'name': 'Freight',
                'price_unit': 2000.0,
                'split_method': 'by_weight',
            })],
        })
        landed_cost.action_auto_allocate()
        self.assertTrue(landed_cost.valuation_adjustment_lines)

    def test_mixed_allocation_independent_amounts(self):
        # PRD-001: qty 10 @ weight 10 = 100 kg, value 10*100 = 1000
        # PRD-002: qty 10 @ weight 10 = 100 kg, value 10*120 = 1200
        picking = self._make_picking([(self.prod_a, 10.0), (self.prod_b, 10.0)])
        landed_cost = self.env['stock.landed.cost'].create({
            'picking_ids': [(6, 0, picking.ids)],
            'vendor_id': self.vendor.id,
            'cost_lines': [
                (0, 0, {
                    'product_id': self.freight_product.id,
                    'name': 'Freight',
                    'price_unit': 2500.0,
                    'split_method': 'by_weight',
                }),
                (0, 0, {
                    'product_id': self.duty_product.id,
                    'name': 'Duty',
                    'price_unit': 1800.0,
                    'split_method': 'by_current_cost_price',
                }),
            ],
        })
        landed_cost.action_auto_allocate()

        freight_line = landed_cost.cost_lines.filtered(
            lambda l: l.product_id == self.freight_product)
        duty_line = landed_cost.cost_lines.filtered(
            lambda l: l.product_id == self.duty_product)

        freight_adj = landed_cost.valuation_adjustment_lines.filtered(
            lambda a: a.cost_line_id == freight_line)
        duty_adj = landed_cost.valuation_adjustment_lines.filtered(
            lambda a: a.cost_line_id == duty_line)

        # Equal weight (100 kg each) -> equal freight split, and the two
        # lines' amounts sum back to the original cost line amount.
        freight_amounts = freight_adj.mapped('additional_landed_cost')
        self.assertEqual(len(freight_amounts), 2)
        self.assertAlmostEqual(freight_amounts[0], freight_amounts[1], places=2)
        self.assertAlmostEqual(sum(freight_amounts), 2500.0, places=2)

        # Value-weighted duty split: 1000 vs 1200 -> not equal, and still
        # sums back to the original cost line amount.
        duty_amounts = duty_adj.mapped('additional_landed_cost')
        self.assertEqual(len(duty_amounts), 2)
        self.assertNotAlmostEqual(duty_amounts[0], duty_amounts[1], places=2)
        self.assertAlmostEqual(sum(duty_amounts), 1800.0, places=2)

    def test_allocation_breakdown_populated(self):
        picking = self._make_picking([(self.prod_a, 10.0), (self.prod_b, 10.0)])
        landed_cost = self.env['stock.landed.cost'].create({
            'picking_ids': [(6, 0, picking.ids)],
            'vendor_id': self.vendor.id,
            'cost_lines': [
                (0, 0, {
                    'product_id': self.freight_product.id,
                    'name': 'Freight',
                    'price_unit': 2500.0,
                    'split_method': 'by_weight',
                }),
                (0, 0, {
                    'product_id': self.duty_product.id,
                    'name': 'Duty',
                    'price_unit': 1800.0,
                    'split_method': 'by_current_cost_price',
                }),
            ],
        })
        landed_cost.action_auto_allocate()

        for adj in landed_cost.valuation_adjustment_lines:
            self.assertTrue(adj.allocation_breakdown)
            method = adj.cost_line_id.split_method
            if method == 'by_weight':
                self.assertIn('weight', adj.allocation_breakdown.lower())
            elif method == 'by_current_cost_price':
                self.assertIn('value', adj.allocation_breakdown.lower())

    def test_rule_applied_by_auto_allocate(self):
        self.env['landed.cost.allocation.rule'].create({
            'vendor_id': self.vendor.id,
            'product_id': self.freight_product.id,
            'split_method': 'by_weight',
        })
        picking = self._make_picking([(self.prod_a, 10.0), (self.prod_b, 10.0)])
        landed_cost = self.env['stock.landed.cost'].create({
            'picking_ids': [(6, 0, picking.ids)],
            'vendor_id': self.vendor.id,
            'cost_lines': [(0, 0, {
                'product_id': self.freight_product.id,
                'name': 'Freight',
                'price_unit': 2500.0,
                'split_method': 'equal',
            })],
        })
        landed_cost.action_auto_allocate()
        self.assertEqual(landed_cost.cost_lines.split_method, 'by_weight')
