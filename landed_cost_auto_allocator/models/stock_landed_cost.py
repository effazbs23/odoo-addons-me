# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError

# NOTE ON VERIFICATION: the field/method names below (`split_method` on
# `stock.landed.cost.lines`; `quantity` / `weight` / `volume` /
# `former_cost` / `additional_landed_cost` on
# `stock.valuation.adjustment.lines`; `compute_landed_cost()` on
# `stock.landed.cost`) follow the well-documented, long-stable public
# behavior of core `stock_landed_costs`. No vendored copy of that addon's
# source was available in this environment to confirm them directly - see
# CHANGELOG.md. Double check against the target Odoo 17 database before
# installing, and adjust here if any name differs.

METHOD_UNIT_LABEL = {
    'by_weight': 'kg',
    'by_volume': 'm3',
}


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    def action_auto_allocate(self):
        """One-click Auto-Allocate (see features.md #1):

        1. Apply the best-matching allocation-rule template's split_method
           to each cost line (`_apply_allocation_rules`).
        2. Run the weight/volume data-quality pre-flight check, blocking
           with a clear UserError if data is missing
           (`_check_allocation_data_quality`).
        3. Call core's own `compute_landed_cost()` so the split math itself
           stays core's, not reimplemented.
        4. Populate the `allocation_breakdown` audit-trail text per
           valuation adjustment line (`_populate_allocation_breakdown`).
        """
        for cost in self:
            cost._apply_allocation_rules()
            cost._check_allocation_data_quality()
        self.compute_landed_cost()
        for cost in self:
            cost._populate_allocation_breakdown()
        return True

    def _apply_allocation_rules(self):
        """Suggest a `split_method` per cost line from the best-matching
        `landed.cost.allocation.rule`.

        The module has no reliable way to distinguish "the user manually
        picked this method" from "this is just core's product-driven
        default" without adding extra tracking state (see CHANGELOG). So a
        matching rule's method is (re)applied every time Auto-Allocate is
        run; a cost line with no matching rule keeps whatever split_method
        it already has.
        """
        self.ensure_one()
        Rule = self.env['landed.cost.allocation.rule']
        for line in self.cost_lines:
            rule = Rule._find_matching_rule(self.vendor_id.id, line.product_id.id)
            if rule:
                line.split_method = rule.split_method

    def _get_relevant_moves(self):
        """Stock moves affected by this landed cost's receipt(s).

        Tries the Odoo 17 field name (`move_ids`) first and falls back to
        the older `move_lines` alias for cross-version safety, since this
        could not be confirmed against real source. Service products are
        excluded - they carry no weight/volume/stock valuation to split
        landed cost onto.
        """
        self.ensure_one()
        pickings = self.picking_ids
        if not pickings:
            return self.env['stock.move']
        moves = pickings.move_ids if 'move_ids' in pickings._fields else pickings.move_lines
        return moves.filtered(
            lambda m: m.state == 'done' and m.product_id.type != 'service')

    def _check_allocation_data_quality(self):
        """Pre-flight data-quality check (specs.md design note 3).

        Blocks with a `UserError` listing every product missing the
        weight/volume a `by_weight`/`by_volume` cost line needs, *before*
        allocating - a blocking check here is deliberately preferred over a
        soft/ignorable warning, since bad weight/volume data would
        otherwise silently corrupt the resulting inventory valuation once
        the landed cost is posted. See CHANGELOG.md for the reasoning.
        """
        self.ensure_one()
        weight_needed = any(l.split_method == 'by_weight' for l in self.cost_lines)
        volume_needed = any(l.split_method == 'by_volume' for l in self.cost_lines)
        if not (weight_needed or volume_needed):
            return

        moves = self._get_relevant_moves()
        products = moves.mapped('product_id')
        missing_weight = products.filtered(lambda p: not p.weight) if weight_needed else self.env['product.product']
        missing_volume = products.filtered(lambda p: not p.volume) if volume_needed else self.env['product.product']

        if not (missing_weight or missing_volume):
            return

        message_parts = []
        if missing_weight:
            message_parts.append(_(
                "Missing weight (used by a 'By Weight' cost line): %s"
            ) % ', '.join(missing_weight.mapped('display_name')))
        if missing_volume:
            message_parts.append(_(
                "Missing volume (used by a 'By Volume' cost line): %s"
            ) % ', '.join(missing_volume.mapped('display_name')))

        raise UserError(_(
            "Auto-Allocate cannot allocate by weight/volume: some products "
            "on this receipt have no weight/volume set.\n\n%s\n\n"
            "Set the missing data on the product(s), or choose a different "
            "allocation method for the affected cost line(s), then run "
            "Auto-Allocate again."
        ) % '\n'.join(message_parts))

    def _populate_allocation_breakdown(self):
        """Fill in the `allocation_breakdown` audit-trail text on every
        valuation adjustment line, per cost line, after core has computed
        the split (`compute_landed_cost()` must have already run).
        """
        self.ensure_one()
        currency_name = self.currency_id.name if self.currency_id else ''
        for line in self.cost_lines:
            adj_lines = self.valuation_adjustment_lines.filtered(
                lambda a: a.cost_line_id.id == line.id)
            if not adj_lines:
                continue
            totals = {
                'quantity': sum(adj_lines.mapped('quantity')),
                'weight': sum(adj_lines.mapped('weight')),
                'volume': sum(adj_lines.mapped('volume')),
                'value': sum(adj_lines.mapped('former_cost')),
                'count': len(adj_lines),
            }
            for adj in adj_lines:
                adj.allocation_breakdown = adj._build_allocation_breakdown(
                    line, currency_name, totals)


class StockValuationAdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    allocation_breakdown = fields.Text(
        string='Allocation Breakdown', copy=False,
        help="Human-readable formula showing exactly how this line's "
             "share of the cost was calculated. Populated by Auto-Allocate.")
    preview_weight = fields.Float(
        string='Weight (kg)', compute='_compute_allocation_preview_fields',
        digits='Stock Weight',
        help="Total weight of this move's quantity, for the Allocation "
             "Preview panel.")
    preview_volume = fields.Float(
        string='Volume (m3)', compute='_compute_allocation_preview_fields',
        digits='Volume',
        help="Total volume of this move's quantity, for the Allocation "
             "Preview panel.")
    preview_value = fields.Float(
        string='Value', compute='_compute_allocation_preview_fields',
        digits='Product Price',
        help="Value of this move's quantity before the landed cost is "
             "added, for the Allocation Preview panel.")

    @api.depends('move_id', 'move_id.product_id', 'quantity', 'former_cost')
    def _compute_allocation_preview_fields(self):
        for line in self:
            product = line.move_id.product_id if line.move_id else line.product_id
            qty = line.quantity or 0.0
            line.preview_weight = (product.weight or 0.0) * qty if product else 0.0
            line.preview_volume = (product.volume or 0.0) * qty if product else 0.0
            line.preview_value = line.former_cost or 0.0

    def action_view_allocation_breakdown(self):
        """Open a small read-only popup showing this line's audit-trail
        formula text (Allocation Preview / Audit Trail panel, ui.png)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Allocation Breakdown'),
            'res_model': 'stock.valuation.adjustment.lines',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'landed_cost_auto_allocator.'
                'view_stock_valuation_adjustment_lines_form_breakdown').id,
            'target': 'new',
        }

    def _build_allocation_breakdown(self, cost_line, currency_name, totals):
        """Human-readable formula string for this adjustment line,
        mirroring ui.png's Audit Trail panel style, e.g. for a by-quantity
        line:

            Customs (700.00 USD) allocated by quantity:
            Total quantity: 500
            Unit rate: 1.40 USD per unit
            Formula: Allocated = Item Qty / 500 x 700.00
        """
        self.ensure_one()
        method = cost_line.split_method
        amount = cost_line.price_unit
        allocated = self.additional_landed_cost
        header = "%s (%s %s) allocated %s:" % (
            cost_line.name or cost_line.product_id.display_name,
            '%.2f' % amount, currency_name, self._method_label(method))

        if method == 'by_quantity':
            total_qty = totals['quantity']
            rate = amount / total_qty if total_qty else 0.0
            body = (
                "Total quantity: %s\n"
                "Unit rate: %.2f %s per unit\n"
                "Formula: Allocated = Item Qty / %s x %.2f"
            ) % (self._fmt(total_qty), rate, currency_name,
                 self._fmt(total_qty), amount)
        elif method == 'by_current_cost_price':
            total_value = totals['value']
            rate_pct = (self.former_cost / total_value * 100.0) if total_value else 0.0
            body = (
                "Total value: %.2f %s\n"
                "This item's share: %.2f%% of total value\n"
                "Formula: Allocated = Item Value / %.2f x %.2f"
            ) % (total_value, currency_name, rate_pct, total_value, amount)
        elif method == 'by_weight':
            total_weight = totals['weight']
            rate = amount / total_weight if total_weight else 0.0
            body = (
                "Total weight: %s kg\n"
                "Unit rate: %.2f %s per kg\n"
                "Formula: Allocated = Item Weight / %s x %.2f"
            ) % (self._fmt(total_weight), rate, currency_name,
                 self._fmt(total_weight), amount)
        elif method == 'by_volume':
            total_volume = totals['volume']
            rate = amount / total_volume if total_volume else 0.0
            body = (
                "Total volume: %s m3\n"
                "Unit rate: %.2f %s per m3\n"
                "Formula: Allocated = Item Volume / %s x %.2f"
            ) % (self._fmt(total_volume), rate, currency_name,
                 self._fmt(total_volume), amount)
        else:  # equal
            count = totals['count'] or 1
            share = amount / count
            body = (
                "Number of items: %s\n"
                "Per-item share: %.2f %s\n"
                "Formula: Allocated = %.2f / %s"
            ) % (count, share, currency_name, amount, count)

        return "%s\n%s\n(Allocated to this line: %.2f %s)" % (
            header, body, allocated, currency_name)

    @staticmethod
    def _method_label(method):
        return {
            'equal': 'equally',
            'by_quantity': 'by quantity',
            'by_current_cost_price': 'by value',
            'by_weight': 'by weight',
            'by_volume': 'by volume',
        }.get(method, method or '')

    @staticmethod
    def _fmt(value):
        # Whole numbers print without a trailing ".00" (matches ui.png's
        # "Total quantity: 500" style); fractional totals keep 2 decimals.
        if float(value).is_integer():
            return '%d' % value
        return '%.2f' % value
