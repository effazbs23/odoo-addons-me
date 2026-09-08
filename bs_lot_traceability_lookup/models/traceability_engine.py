from markupsafe import Markup, escape

from odoo import models

INTERNAL_USAGES = ('internal', 'transit')


class TraceabilityEngine(models.AbstractModel):
    """Backward/forward lot lineage over native stock.move.line / mrp data.

    Key idea (verified against Odoo 19 core): a lot's own physical movement
    history (receipt -> relocation -> consumption/delivery) is one query,
    since the same lot_id persists across relocations. Recursion is only
    needed to hop *across* a manufacturing boundary, where a produced lot's
    identity differs from the component lots that made it - that hop is
    exactly what stock.move.line.consume_line_ids/produce_line_ids encode
    (populated by mrp when a production is validated). So "depth" here
    means lot-to-lot hops (MOs crossed), not individual stock moves.
    """
    _name = 'bs.traceability.engine'
    _description = 'Batch Traceability Engine'

    MAX_DEPTH_DEFAULT = 20
    # Cap on how many distinct next-hop lots/lines get expanded per node;
    # the rest are counted and summarized ("...and N more") instead of
    # being walked, so one very wide lot can't blow up the query/response.
    WIDE_RESULT_LIMIT = 20

    # ---------------------------------------------------------------- utils

    def _lot_lines(self, lot_ids):
        # Spec section 9: "multi-company data" - plain search() (never
        # sudo()) so normal stock.move.line record rules apply; a user
        # without access to a company's lines simply won't see them here.
        if not lot_ids:
            return self.env['stock.move.line']
        return self.env['stock.move.line'].search([
            ('lot_id', 'in', lot_ids),
            ('state', '=', 'done'),
        ])

    def _lines_by_lot(self, lines):
        by_lot = {}
        for line in lines:
            by_lot.setdefault(line.lot_id.id, self.env['stock.move.line'])
            by_lot[line.lot_id.id] |= line
        return by_lot

    def _reference(self, move_line):
        move = move_line.move_id
        if move.production_id:
            return move.production_id.display_name, 'mrp.production', move.production_id.id
        if move.raw_material_production_id:
            return move.raw_material_production_id.display_name, 'mrp.production', move.raw_material_production_id.id
        picking = move_line.picking_id or move.picking_id
        if picking:
            return picking.display_name, 'stock.picking', picking.id
        if move.scrap_id:
            return move.scrap_id.display_name, 'stock.scrap', move.scrap_id.id
        if move.is_inventory:
            return 'Inventory Adjustment', 'stock.move', move.id
        return move.display_name, 'stock.move', move.id

    def _partner_name(self, move_line):
        picking = move_line.picking_id or move_line.move_id.picking_id
        return picking.partner_id.display_name if picking and picking.partner_id else False

    def _sale_reference(self, move_line):
        """Best-effort SO reference. Only populated if sale_stock is
        installed - deliberately no hard dependency on 'sale'/'sale_stock'
        for a single optional field."""
        move = move_line.move_id
        if 'sale_line_id' in move._fields and move.sale_line_id:
            return move.sale_line_id.order_id.display_name
        picking = move_line.picking_id or move.picking_id
        if picking and 'sale_id' in picking._fields and picking.sale_id:
            return picking.sale_id.display_name
        return False

    def _base_node(self, lot, line, boundary):
        ref, res_model, res_id = self._reference(line) if line else (False, False, False)
        return {
            'lot_id': lot.id if lot else False,
            'lot_name': lot.name if lot else False,
            'product_name': (line.product_id.display_name if line else (lot.product_id.display_name if lot else False)),
            'quantity': line.quantity if line else 0.0,
            'uom_name': line.product_uom_id.name if line else False,
            'date': line.date if line else False,
            'boundary': boundary,
            'reference': ref,
            'res_model': res_model,
            'res_id': res_id,
            'partner_name': self._partner_name(line) if line else False,
            'sale_reference': self._sale_reference(line) if line else False,
            'children': [],
            'more_count': 0,
        }

    def _untracked_node(self, component_line):
        # Spec section 9: "partial/non-lot-tracked products in the same
        # chain" - a component with no lot_id must show plainly as such
        # rather than breaking the chain or implying false precision.
        node = self._base_node(False, component_line, 'not_tracked')
        node['lot_name'] = 'Not individually tracked'
        return node

    def _circular_node(self, lot):
        # Spec section 9: "very deep or circular-looking chains" - a lot
        # that reappears in its own ancestry (rework/reprocessing loop) is
        # flagged instead of being expanded again (see path-scoped `seen`
        # sets in _walk, which is what actually stops the recursion).
        node = self._base_node(lot, False, 'circular')
        return node

    def _more_node(self, count, label):
        # Spec section 9: "lot consumed into many manufacturing orders" -
        # once a node's fan-out exceeds WIDE_RESULT_LIMIT, the remainder is
        # summarized ("...and 47 more manufacturing orders") instead of
        # being rendered/queried in full.
        return {
            'lot_id': False, 'lot_name': False, 'product_name': False,
            'quantity': 0.0, 'uom_name': False, 'date': False,
            'boundary': 'truncated', 'reference': False, 'res_model': False,
            'res_id': False, 'partner_name': False, 'sale_reference': False,
            'children': [], 'more_count': count, 'more_label': label,
        }

    def _no_history_node(self, lot):
        # Spec section 9: "lot with no tracking history" (e.g. created via a
        # bare inventory adjustment) - show a clear message, not an error or
        # a silently empty branch.
        node = self._base_node(lot, False, 'no_history')
        return node

    def _max_depth_node(self):
        return self._more_node(0, 'max depth reached')

    # -------------------------------------------------------- shared walker
    #
    # Level-by-level BFS, not per-node recursion: every node whose expansion
    # is due at the current depth is collected first, then expanded with ONE
    # batched query/prefetch for the whole level (regardless of how many
    # sibling nodes are waiting on it). Per-node recursion here would mean a
    # lot consumed into 100 MOs triggers 100 separate recursive calls (and
    # queries) for their 100 produced lots instead of one - exactly the N+1
    # shape the performance test below is built to catch.
    #
    # "seen" is carried per-branch (a frozenset copy per frontier entry, not
    # one shared mutable set) so a cycle is only flagged when a lot reappears
    # in *its own* ancestry - two sibling branches that both legitimately
    # trace back to the same shared upstream lot (a normal DAG merge, e.g.
    # one raw batch split into two sub-assemblies that both feed the same
    # finished good) is not a cycle and must not be misreported as one.

    def backward_trace(self, lot, max_depth=None):
        return self._walk(
            lot, max_depth,
            is_boundary_line=lambda l: l.location_dest_id.usage in INTERNAL_USAGES and l.location_id.usage not in INTERNAL_USAGES,
            is_bridge=lambda l: bool(l.move_id.production_id),
            bridge_lines=lambda l: l.consume_line_ids,
            classify=self._classify_backward,
            more_label='source lots',
        )

    def forward_trace(self, lot, max_depth=None):
        return self._walk(
            lot, max_depth,
            is_boundary_line=lambda l: l.location_id.usage in INTERNAL_USAGES and l.location_dest_id.usage not in INTERNAL_USAGES,
            is_bridge=lambda l: bool(l.move_id.raw_material_production_id),
            bridge_lines=lambda l: l.produce_line_ids,
            classify=self._classify_forward,
            more_label='manufacturing orders',
        )

    def _classify_backward(self, line):
        if line.location_id.usage == 'supplier':
            return 'vendor'
        if line.location_id.usage == 'inventory':
            return 'adjustment'
        return 'unknown'

    def _classify_forward(self, line):
        if line.location_dest_id.usage == 'customer':
            return 'customer'
        if line.location_dest_id.usage == 'inventory':
            return 'scrap_or_adjustment'
        return 'unknown'

    def _walk(self, root_lot, max_depth, is_boundary_line, is_bridge, bridge_lines, classify, more_label):
        max_depth = max_depth if max_depth is not None else self.MAX_DEPTH_DEFAULT
        root_container = []
        # frontier entries: (lot_id, container to append this lot's nodes into, path-scoped seen set)
        frontier = [(root_lot.id, root_container, frozenset([root_lot.id]))]
        depth = 0
        while frontier:
            lot_ids = list({lid for lid, _c, _s in frontier})
            # Browse all of this level's lots as ONE recordset so later field
            # access (lot.name, ...) prefetches in one query instead of one
            # query per lot - individual browse(single_id) calls don't share
            # a prefetch batch even when done in the same loop.
            lots_by_id = {lot.id: lot for lot in self.env['stock.lot'].browse(lot_ids)}
            by_lot = self._lines_by_lot(self._lot_lines(lot_ids))
            pending = []  # (children_container, path_seen, bridge_lines) queued for batched expansion
            for lot_id, container, path_seen in frontier:
                lot = lots_by_id[lot_id]
                lot_lines = by_lot.get(lot_id, self.env['stock.move.line'])
                boundary_lines = lot_lines.filtered(is_boundary_line)
                if not boundary_lines:
                    container.append(self._no_history_node(lot))
                    continue
                # Wide fan-out cap (spec 9): a lot consumed into 100+ MOs, or received
                # across 100+ separate lines, must not dump an unbounded node list -
                # this caps THIS lot's own boundary lines, distinct from the cap below
                # on how many *further* lots get expanded from this level's children.
                line_overflow = len(boundary_lines) - self.WIDE_RESULT_LIMIT
                if line_overflow > 0:
                    boundary_lines = boundary_lines[:self.WIDE_RESULT_LIMIT]
                for line in boundary_lines:
                    if is_bridge(line):
                        node = self._base_node(lot, line, 'production')
                        container.append(node)
                        if depth + 1 > max_depth:
                            node['children'] = [self._max_depth_node()]
                        else:
                            pending.append((node['children'], path_seen, bridge_lines(line)))
                    else:
                        container.append(self._base_node(lot, line, classify(line)))
                if line_overflow > 0:
                    container.append(self._more_node(line_overflow, more_label))

            next_frontier = []
            if pending:
                all_lines = self.env['stock.move.line']
                for _container, _seen, lines in pending:
                    all_lines |= lines
                tracked_global = all_lines.filtered('lot_id')  # one batched prefetch for the whole level
                group_plans = []  # (container, circular_lot_ids, overflow)
                all_circular_ids = set()
                for container, path_seen, lines in pending:
                    tracked_lines = lines & tracked_global
                    untracked_lines = lines - tracked_lines
                    container.extend(self._untracked_node(line) for line in untracked_lines)

                    distinct_lot_ids = list(dict.fromkeys(tracked_lines.mapped('lot_id').ids))
                    new_lot_ids = [lid for lid in distinct_lot_ids if lid not in path_seen]
                    circular_lot_ids = [lid for lid in distinct_lot_ids if lid in path_seen]

                    to_expand = new_lot_ids[:self.WIDE_RESULT_LIMIT]
                    overflow = len(new_lot_ids) - len(to_expand)
                    for lid in to_expand:
                        next_frontier.append((lid, container, path_seen | {lid}))
                    group_plans.append((container, circular_lot_ids, overflow))
                    all_circular_ids.update(circular_lot_ids)

                circular_lots_by_id = {lot.id: lot for lot in self.env['stock.lot'].browse(list(all_circular_ids))}
                for container, circular_lot_ids, overflow in group_plans:
                    container.extend(self._circular_node(circular_lots_by_id[lid]) for lid in circular_lot_ids)
                    if overflow > 0:
                        container.append(self._more_node(overflow, more_label))
            frontier = next_frontier
            depth += 1
        return root_container

    # -------------------------------------------------------------- summary

    def _flatten(self, nodes):
        flat = []
        for node in nodes:
            flat.append(node)
            flat.extend(self._flatten(node.get('children') or []))
        return flat

    def build_summary(self, lot, backward_nodes=None, forward_nodes=None):
        parts = []
        if backward_nodes is not None:
            parts.append(self._backward_summary(lot, backward_nodes))
        if forward_nodes is not None:
            parts.append(self._forward_summary(lot, forward_nodes))
        return ' '.join(p for p in parts if p)

    def _backward_summary(self, lot, nodes):
        if not nodes or (len(nodes) == 1 and nodes[0]['boundary'] == 'no_history'):
            return ("No upstream history found for lot %s (e.g. a manual adjustment "
                    "with no receipt/production trail)." % lot.name)
        clauses = []
        for node in nodes:
            boundary = node['boundary']
            if boundary == 'vendor':
                when = ' on %s' % node['date'].date() if node.get('date') else ''
                clauses.append('received from %s%s' % (node['partner_name'] or 'an unspecified vendor', when))
            elif boundary == 'production':
                comp_count = len([c for c in node['children'] if c['boundary'] != 'truncated'])
                clauses.append('produced in %s from %d traceable component line(s)' % (node['reference'], comp_count))
            elif boundary == 'adjustment':
                clauses.append('created via inventory adjustment (%s)' % node['reference'])
            else:
                clauses.append('recorded via %s' % node['reference'])
        return 'Lot %s was %s.' % (lot.name, '; and '.join(clauses))

    def _forward_summary(self, lot, nodes):
        if not nodes:
            return "No downstream movement recorded for lot %s - it appears to still be in stock." % lot.name

        flat = self._flatten(nodes)
        customers, seen_customer = [], set()
        for node in flat:
            if node['boundary'] == 'customer':
                key = (node['partner_name'], node['sale_reference'])
                if key not in seen_customer:
                    seen_customer.add(key)
                    customers.append(node)

        mo_nodes, seen_mo, produced_lot_names = [], set(), []
        for node in flat:
            if node['boundary'] == 'production' and node['reference'] not in seen_mo:
                seen_mo.add(node['reference'])
                mo_nodes.append(node)
                for child in node['children']:
                    if child.get('lot_name') and child['boundary'] not in ('circular', 'truncated', 'not_tracked'):
                        if child['lot_name'] not in produced_lot_names:
                            produced_lot_names.append(child['lot_name'])

        still_in_stock = any(node['boundary'] == 'no_history' for node in nodes)

        clauses = []
        if mo_nodes:
            lot_txt = ''
            if produced_lot_names:
                lot_txt = ' producing lot(s) %s' % ', '.join(produced_lot_names[:5])
                extra = len(produced_lot_names) - 5
                if extra > 0:
                    lot_txt += ' and %d more' % extra
            clauses.append('consumed into %d manufacturing order(s)%s' % (len(mo_nodes), lot_txt))
        if customers:
            cust_txt = ', '.join(
                (c['partner_name'] or 'an unspecified customer') + (' (%s)' % c['sale_reference'] if c['sale_reference'] else '')
                for c in customers[:5]
            )
            extra = len(customers) - 5
            if extra > 0:
                cust_txt += ', and %d more' % extra
            clauses.append('delivered to %d customer(s): %s' % (len(customers), cust_txt))
        if still_in_stock and not clauses:
            clauses.append('still in stock, not yet consumed or shipped')
        if not clauses:
            clauses.append('has downstream movement recorded but no manufacturing consumption or customer delivery was found')
        return 'Lot %s was %s.' % (lot.name, '; and '.join(clauses))

    # ------------------------------------------------------------- html tree

    # boundary -> (fa-icon, short type label shown above the lot line)
    _NODE_META = {
        'vendor': ('fa-truck', 'Raw Material'),
        'production': ('fa-industry', 'Manufacturing Order'),
        'customer': ('fa-user', 'Customer Delivery'),
        'adjustment': ('fa-wrench', 'Inventory Adjustment'),
        'scrap_or_adjustment': ('fa-recycle', 'Scrap / Adjustment'),
        'not_tracked': ('fa-question-circle', 'Not Individually Tracked'),
        'unknown': ('fa-circle-o', 'Movement'),
    }

    def render_chain_html(self, nodes):
        """Timeline-styled nested list - built once in Python and reused for
        both the wizard's on-screen preview (CSS turns it into a vertical
        timeline) and the PDF export (renders as a plain nested list)."""
        if not nodes:
            return Markup('<p class="text-muted">No data.</p>')
        return Markup('<ul class="o_bs_trace_timeline">%s</ul>') % Markup('').join(
            self._render_node_html(n) for n in nodes)

    def _render_node_html(self, node):
        boundary = node['boundary']
        if boundary == 'truncated':
            label = '... and %d more %s' % (node['more_count'], node.get('more_label') or 'items')
            return Markup('<li class="o_bs_trace_node o_bs_trace_node-muted">'
                           '<span class="o_bs_trace_dot"><i class="fa fa-ellipsis-h"/></span>'
                           '<div class="o_bs_trace_node_body"><em>%s</em></div></li>') % escape(label)
        if boundary == 'circular':
            return Markup('<li class="o_bs_trace_node o_bs_trace_node-circular">'
                           '<span class="o_bs_trace_dot"><i class="fa fa-refresh"/></span>'
                           '<div class="o_bs_trace_node_body">%s <em>(circular reference - already shown above)</em></div></li>'
                           ) % escape(node['lot_name'] or '')
        if boundary == 'no_history':
            return Markup('<li class="o_bs_trace_node o_bs_trace_node-muted">'
                           '<span class="o_bs_trace_dot"><i class="fa fa-ban"/></span>'
                           '<div class="o_bs_trace_node_body"><em>No further history found.</em></div></li>')

        label_bits = []
        if node.get('lot_name'):
            label_bits.append('Lot <strong>%s</strong>' % escape(node['lot_name']))
        if node.get('product_name'):
            label_bits.append('(%s)' % escape(node['product_name']))
        if node.get('quantity'):
            label_bits.append('qty %s %s' % (node['quantity'], escape(node.get('uom_name') or '')))
        detail = {
            'vendor': 'received from %s' % escape(node.get('partner_name') or 'vendor'),
            'customer': 'delivered to %s' % escape(node.get('partner_name') or 'customer'),
            'production': 'via %s' % escape(node.get('reference') or 'manufacturing order'),
            'adjustment': 'via inventory adjustment',
            'scrap_or_adjustment': 'scrapped / adjusted out of stock',
            'not_tracked': 'component not individually tracked',
            'unknown': escape(node.get('reference') or ''),
        }.get(boundary, '')
        if node.get('sale_reference'):
            detail += ' - %s' % escape(node['sale_reference'])
        line = Markup(' ').join([Markup(b) for b in label_bits] + ([Markup('- %s' % detail)] if detail else []))
        children_html = ''
        if node.get('children'):
            children_html = Markup('<ul class="o_bs_trace_timeline o_bs_trace_timeline-nested">%s</ul>') % Markup('').join(
                self._render_node_html(c) for c in node['children'])

        icon, type_label = self._NODE_META.get(boundary, ('fa-circle-o', ''))
        type_html = Markup('<span class="o_bs_trace_node_type">%s</span>') % escape(type_label) if type_label else ''
        return Markup(
            '<li class="o_bs_trace_node o_bs_trace_node-%s">'
            '<span class="o_bs_trace_dot"><i class="fa %s"/></span>'
            '<div class="o_bs_trace_node_body">%s<div class="o_bs_trace_node_line">%s</div>%s</div></li>'
        ) % (boundary, icon, type_html, line, children_html)
