from odoo import Command
from odoo.tests import tagged

from .common import TraceabilityCommon


@tagged('post_install', '-at_install')
class TestTraceEngine(TraceabilityCommon):

    # -- Unit: backward trace, 3-level chain (raw -> sub-assembly -> finished)

    def test_backward_trace_three_level_chain(self):
        raw = self._make_product('Raw Material')
        sub = self._make_product('Sub Assembly')
        finished = self._make_product('Finished Good')

        raw_lot = self._receive_from_vendor(raw, 'RAW1', 10)
        sub_bom = self._make_bom(sub, [(raw, 2)])
        sub_lot, _ = self._produce(sub_bom, sub, {raw: raw_lot}, 'SUB1', qty=1)
        fin_bom = self._make_bom(finished, [(sub, 1)])
        fin_lot, _ = self._produce(fin_bom, finished, {sub: sub_lot}, 'FIN1', qty=1)

        result = self.engine.backward_trace(fin_lot)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['boundary'], 'production')

        sub_children = result[0]['children']
        self.assertEqual(len(sub_children), 1)
        self.assertEqual(sub_children[0]['lot_name'], 'SUB1')
        self.assertEqual(sub_children[0]['boundary'], 'production')

        raw_children = sub_children[0]['children']
        self.assertEqual(len(raw_children), 1)
        self.assertEqual(raw_children[0]['lot_name'], 'RAW1')
        self.assertEqual(raw_children[0]['boundary'], 'vendor')
        self.assertEqual(raw_children[0]['partner_name'], self.vendor.name)

    def test_backward_trace_no_history(self):
        """Lot with no receipt/production trail (e.g. created via inventory
        adjustment) - must show a clear 'no history' node, not error/blank."""
        product = self._make_product('Adjusted Product')
        lot = self.env['stock.lot'].create({'name': 'ADJ1', 'product_id': product.id})
        quant = self.env['stock.quant'].create({
            'product_id': product.id,
            'location_id': self.stock_location.id,
            'lot_id': lot.id,
            'inventory_quantity': 5,
        })
        quant.action_apply_inventory()

        result = self.engine.backward_trace(lot)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['boundary'], 'adjustment')

    def test_backward_trace_untracked_component(self):
        """A component not individually lot-tracked must show as such,
        not break the chain or silently vanish."""
        raw_tracked = self._make_product('Tracked Raw')
        raw_untracked = self._make_product('Untracked Raw', tracking='none')
        finished = self._make_product('Mixed Finished')

        raw_lot = self._receive_from_vendor(raw_tracked, 'MRAW1', 5)
        bom = self._make_bom(finished, [(raw_tracked, 1), (raw_untracked, 3)])
        fin_lot, _ = self._produce(bom, finished, {raw_tracked: raw_lot, raw_untracked: False}, 'MFIN1', qty=1)

        result = self.engine.backward_trace(fin_lot)
        children = result[0]['children']
        boundaries = sorted(c['boundary'] for c in children)
        self.assertEqual(boundaries, ['not_tracked', 'vendor'])

    # -- Unit: forward trace, one lot into multiple MOs + multiple customers

    def test_forward_trace_multi_destination(self):
        raw = self._make_product('Raw Multi')
        finished = self._make_product('Finished Multi')
        raw_lot = self._receive_from_vendor(raw, 'RAWM', 10)
        bom = self._make_bom(finished, [(raw, 1)])

        customer_x = self.env['res.partner'].create({'name': 'Customer X'})
        customer_y = self.env['res.partner'].create({'name': 'Customer Y'})
        fin_lot_1, _ = self._produce(bom, finished, {raw: raw_lot}, 'FINM-1', qty=1)
        fin_lot_2, _ = self._produce(bom, finished, {raw: raw_lot}, 'FINM-2', qty=1)
        fin_lot_3, _ = self._produce(bom, finished, {raw: raw_lot}, 'FINM-3', qty=1)
        self._deliver_to_customer(finished, fin_lot_1, 1, partner=customer_x)
        self._deliver_to_customer(finished, fin_lot_2, 1, partner=customer_x)
        self._deliver_to_customer(finished, fin_lot_3, 1, partner=customer_y)

        result = self.engine.forward_trace(raw_lot)
        self.assertEqual(len(result), 3)
        self.assertTrue(all(n['boundary'] == 'production' for n in result))

        flat_customers = {c['partner_name'] for n in result for c in n['children'] if c['boundary'] == 'customer'}
        self.assertEqual(flat_customers, {'Customer X', 'Customer Y'})

    # -- Unit: plain-language summary, simple + complex

    def test_summary_simple(self):
        raw = self._make_product('Raw Simple')
        finished = self._make_product('Finished Simple')
        raw_lot = self._receive_from_vendor(raw, 'RAWS', 5)
        bom = self._make_bom(finished, [(raw, 1)])
        fin_lot, _ = self._produce(bom, finished, {raw: raw_lot}, 'FINS', qty=1)
        self._deliver_to_customer(finished, fin_lot, 1)

        backward = self.engine.backward_trace(fin_lot)
        forward = self.engine.forward_trace(fin_lot)
        summary = self.engine.build_summary(fin_lot, backward, forward)
        self.assertIn('FINS', summary)
        self.assertIn('produced in', summary)
        self.assertIn('delivered to 1 customer', summary)
        self.assertIn(self.customer.name, summary)

    def test_summary_complex_multi_source_multi_destination(self):
        raw = self._make_product('Raw Complex')
        finished = self._make_product('Finished Complex')
        raw_lot = self._receive_from_vendor(raw, 'RAWC', 10)
        bom = self._make_bom(finished, [(raw, 1)])

        customer_x = self.env['res.partner'].create({'name': 'Customer Complex X'})
        customer_y = self.env['res.partner'].create({'name': 'Customer Complex Y'})
        lot_1, _ = self._produce(bom, finished, {raw: raw_lot}, 'FINC-1', qty=1)
        lot_2, _ = self._produce(bom, finished, {raw: raw_lot}, 'FINC-2', qty=1)
        lot_3, _ = self._produce(bom, finished, {raw: raw_lot}, 'FINC-3', qty=1)
        self._deliver_to_customer(finished, lot_1, 1, partner=customer_x)
        self._deliver_to_customer(finished, lot_2, 1, partner=customer_y)
        self._deliver_to_customer(finished, lot_3, 1, partner=customer_x)

        forward = self.engine.forward_trace(raw_lot)
        summary = self.engine.build_summary(raw_lot, backward_nodes=None, forward_nodes=forward)
        self.assertIn('consumed into 3 manufacturing order(s)', summary)
        self.assertIn('delivered to 2 customer(s)', summary)
        self.assertIn('Customer Complex X', summary)
        self.assertIn('Customer Complex Y', summary)

    # -- Integration: recursion depth cap, incl. a genuine rework/reprocessing loop

    def test_depth_cap_truncates_long_chain(self):
        raw = self._make_product('Raw Deep')
        mid = self._make_product('Mid Deep')
        finished = self._make_product('Finished Deep')
        raw_lot = self._receive_from_vendor(raw, 'RAWD', 5)
        mid_bom = self._make_bom(mid, [(raw, 1)])
        mid_lot, _ = self._produce(mid_bom, mid, {raw: raw_lot}, 'MIDD', qty=1)
        fin_bom = self._make_bom(finished, [(mid, 1)])
        fin_lot, _ = self._produce(fin_bom, finished, {mid: mid_lot}, 'FIND', qty=1)

        # depth=1 means: only follow one MO hop back from the finished lot -
        # it should reach MIDD but NOT the vendor receipt behind it, and must
        # show a truncation marker instead of silently stopping or erroring.
        result = self.engine.backward_trace(fin_lot, max_depth=1)
        self.assertEqual(result[0]['lot_name'], 'FIND')
        mid_node = result[0]['children'][0]
        self.assertEqual(mid_node['lot_name'], 'MIDD')
        self.assertEqual(len(mid_node['children']), 1)
        self.assertEqual(mid_node['children'][0]['boundary'], 'truncated')

    def test_rework_loop_does_not_infinite_loop(self):
        """Synthetic rework/reprocessing loop: a lot that (via injected
        consume_line_ids, mirroring what a byproduct-reprocessing flow would
        produce) ends up listed as one of the components that made itself.
        The engine must terminate and flag it as circular, not hang or error."""
        raw = self._make_product('Raw Loop')
        product_a = self._make_product('Loop Product A')
        raw_lot = self._receive_from_vendor(raw, 'RAWL', 5)
        bom_a = self._make_bom(product_a, [(raw, 1)])
        lot_a, production_a = self._produce(bom_a, product_a, {raw: raw_lot}, 'LOOPA', qty=1)

        finished_move_line = production_a.move_finished_ids.move_line_ids.filtered(lambda l: l.lot_id == lot_a)
        self_reference_line = self.env['stock.move.line'].create({
            'product_id': product_a.id,
            'lot_id': lot_a.id,
            'quantity': 1,
            'location_id': self.stock_location.id,
            'location_dest_id': self.stock_location.id,
            'product_uom_id': self.uom_unit.id,
            'move_id': production_a.move_raw_ids[:1].id,
            'state': 'done',
        })
        finished_move_line.consume_line_ids = [Command.link(self_reference_line.id)]

        result = self.engine.backward_trace(lot_a)
        flat = self.engine._flatten(result)
        self.assertTrue(any(n['boundary'] == 'circular' and n['lot_id'] == lot_a.id for n in flat))

    # -- Performance: wide lineage (one raw lot into 100+ MOs), no N+1

    def test_wide_lineage_no_n_plus_one(self):
        raw = self._make_product('Raw Wide Perf')
        finished = self._make_product('Finished Wide Perf')
        raw_lot = self._receive_from_vendor(raw, 'RAWWIDE', 200)
        bom = self._make_bom(finished, [(raw, 1)])

        for i in range(6):
            self._produce(bom, finished, {raw: raw_lot}, 'FINWIDE-SMALL-%d' % i, qty=1)
        self.env.flush_all()
        count_before = self.env.cr.sql_log_count
        self.engine.forward_trace(raw_lot)
        queries_small = self.env.cr.sql_log_count - count_before

        for i in range(6, 106):
            self._produce(bom, finished, {raw: raw_lot}, 'FINWIDE-BIG-%d' % i, qty=1)
        self.env.flush_all()
        count_before = self.env.cr.sql_log_count
        result = self.engine.forward_trace(raw_lot)
        queries_big = self.env.cr.sql_log_count - count_before

        # ~17x more MOs must not translate into anywhere near 17x more queries -
        # that would indicate a per-node query (N+1) rather than batching.
        self.assertLess(queries_big, queries_small * 3,
                         'Query count scaled with lineage width - looks like an N+1, not a batched fetch.')

        # Wide fan-out must be capped and summarized, not dumped unbounded.
        more_nodes = [n for n in result if n['boundary'] == 'truncated']
        self.assertEqual(len(more_nodes), 1)
        self.assertGreater(more_nodes[0]['more_count'], 0)
        self.assertEqual(len([n for n in result if n['boundary'] == 'production']), self.engine.WIDE_RESULT_LIMIT)
