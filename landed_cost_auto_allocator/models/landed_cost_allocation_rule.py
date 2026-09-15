# -*- coding: utf-8 -*-
from odoo import api, fields, models

# Mirrors core `stock.landed.cost.lines.split_method` (see stock_landed_cost.py
# for the verification caveat on these exact values/field name).
SPLIT_METHODS = [
    ('equal', 'Equal'),
    ('by_quantity', 'By Quantity'),
    ('by_current_cost_price', 'By Current Cost (Value)'),
    ('by_weight', 'By Weight'),
    ('by_volume', 'By Volume'),
]


class LandedCostAllocationRule(models.Model):
    """Reusable "always allocate X this way" template.

    Auto-Allocate looks these up per landed-cost line (keyed by the line's
    `product_id`, the service product used to represent the cost type -
    e.g. "Freight", "Duty", "Customs" - and the landed cost's `vendor_id`)
    to suggest a `split_method` before core computes the actual split.
    """
    _name = 'landed.cost.allocation.rule'
    _description = 'Landed Cost Allocation Rule'
    _order = 'sequence, id'

    name = fields.Char(string='Rule', compute='_compute_name', store=True)
    vendor_id = fields.Many2one(
        'res.partner', string='Vendor',
        help="Restrict this rule to landed costs from this vendor. Leave "
             "empty to match any vendor.")
    product_id = fields.Many2one(
        'product.product', string='Cost Type',
        help="Restrict this rule to this cost-type product (the service "
             "product used on the landed cost line, e.g. Freight, Duty, "
             "Customs). Leave empty to match any cost type.")
    split_method = fields.Selection(
        SPLIT_METHODS, string='Allocation Method', required=True,
        help="Allocation method suggested by this rule; written onto the "
             "matching landed cost line's own `split_method` field by "
             "Auto-Allocate.")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    @api.depends('vendor_id', 'product_id', 'split_method')
    def _compute_name(self):
        method_labels = dict(SPLIT_METHODS)
        for rule in self:
            parts = []
            if rule.vendor_id:
                parts.append(rule.vendor_id.name)
            if rule.product_id:
                parts.append(rule.product_id.name)
            scope = ' / '.join(parts) if parts else 'Any vendor / any cost type'
            rule.name = "%s -> %s" % (scope, method_labels.get(rule.split_method, ''))

    @api.model
    def _find_matching_rule(self, vendor_id, product_id):
        """Return the single best-matching active rule for (vendor, product).

        Priority order (highest first), as documented in the module
        CHANGELOG:
          1. An exact vendor_id + product_id match.
          2. A product_id-only rule (no vendor_id set on the rule).
          3. A vendor_id-only rule (no product_id set on the rule).
        Within a tier, ties are broken by `sequence` ascending, then id.
        A rule that restricts on a field the candidate doesn't have (e.g.
        a vendor-only rule when `vendor_id` is falsy) never matches.
        """
        domain_tiers = []
        if vendor_id and product_id:
            domain_tiers.append([
                ('vendor_id', '=', vendor_id), ('product_id', '=', product_id),
            ])
        if product_id:
            domain_tiers.append([
                ('vendor_id', '=', False), ('product_id', '=', product_id),
            ])
        if vendor_id:
            domain_tiers.append([
                ('vendor_id', '=', vendor_id), ('product_id', '=', False),
            ])
        for domain in domain_tiers:
            rule = self.search(domain, order='sequence asc, id asc', limit=1)
            if rule:
                return rule
        return self.browse()
