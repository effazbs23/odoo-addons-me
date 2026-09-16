# Changelog

## 17.0.1.0.0

Initial release.

### Deviations from `specs.md` / `prompt.md`

- **No vendored core `stock_landed_costs` source in this environment**: no
  Odoo source checkout, installed `odoo` package, or vendored addon copy
  could be found on this filesystem to read directly (checked common addons
  paths, `pip show odoo`, `import odoo`). All core field/method names used
  below therefore follow the well-documented, long-stable public behavior
  of `stock_landed_costs` rather than a verified reading of source:
  `stock.landed.cost.lines.split_method` (selection: `equal`,
  `by_quantity`, `by_current_cost_price`, `by_weight`, `by_volume`);
  `stock.valuation.adjustment.lines` fields `quantity`, `weight`, `volume`,
  `former_cost`, `additional_landed_cost`; `stock.landed.cost.picking_ids`
  and `compute_landed_cost()`; and the form view xmlid
  `stock_landed_costs.view_stock_landed_cost_form`. **Verify every one of
  these against the target Odoo 17 database before installing** and adjust
  the model/view code if any name differs.
- **Reused core `split_method` instead of adding a new `allocation_method`
  field**: `specs.md` design note 2 asks for a new selection field on
  `stock.landed.cost.lines`. Per this build's explicit instructions, since
  core's `stock_landed_costs` already ships a `split_method` field doing
  exactly this job, this module reuses it directly rather than introducing
  a parallel field the user would have to keep in sync with the one core
  actually uses for computation. UI labels/help text call it "Allocation
  Method"; no second field was added.
- **Auto-Allocate re-applies a matching rule's `split_method` every time it
  runs**: the module has no reliable way to tell "the user deliberately
  picked this method" apart from "this is just core's own product-driven
  default" without adding extra tracking state (e.g. a
  `split_method_manual` flag), which was not in scope. So `_apply_allocation_rules()`
  overwrites a cost line's `split_method` with the best-matching rule's
  value every time Auto-Allocate is clicked, when a match exists. A line
  with no matching rule is left as-is. If a user wants a one-off manual
  override to stick, don't re-run Auto-Allocate for that record, or narrow
  the rule so it no longer matches.
- **Data-quality check is a blocking `UserError`, not a non-blocking
  warning/wizard**: `specs.md` design note 3 only asks for a "warns"
  behavior. A blocking `UserError` was chosen deliberately (as this
  build's instructions anticipated) because bad weight/volume data used in
  a `by_weight`/`by_volume` split would otherwise silently corrupt the
  resulting inventory valuation once the landed cost is posted, and this
  check runs entirely *before* any core computation or posting happens -
  it does not touch or gate the accounting flow itself, only the
  Auto-Allocate convenience action. A softer "confirm anyway" wizard was
  considered simpler to skip than to build correctly without a live
  instance to test against, so it was not attempted this round.
- **`landed.cost.allocation.rule.product_id` assumption**: per the design
  note in this build's instructions, `stock.landed.cost.lines` is assumed
  to be keyed by a `product_id` (a service product representing the cost
  type, e.g. "Freight"/"Duty"/"Customs") since that is standard practice
  for `stock_landed_costs`. The rule model's `product_id` matches on that
  same field. If the target version keys cost lines differently, adjust
  `landed_cost_allocation_rule.py` and the join in
  `stock_landed_cost.py::_apply_allocation_rules`.
- **Rule-matching priority order**: documented and implemented in
  `LandedCostAllocationRule._find_matching_rule()` as (highest first):
  (1) exact vendor + cost-type match, (2) cost-type-only rule (no vendor
  set on the rule), (3) vendor-only rule (no cost type set on the rule).
  Ties within a tier are broken by `sequence` ascending, then `id`. Covered
  by `test_rule_matching_priority_order`.
- **Audit-trail formula surfaced via a "Details" popup, not inline text**:
  `allocation_breakdown` is a stored `Text` field on
  `stock.valuation.adjustment.lines`, but rather than trying to render
  multi-line text cleanly inside an embedded list column (fragile to build
  correctly without a live instance to check row height/wrapping against),
  a small "Details" button (`action_view_allocation_breakdown`) was added
  per row, opening a minimal read-only popup form
  (`view_stock_valuation_adjustment_lines_form_breakdown`) with the
  product, quantity, allocated cost and the full formula text. This was
  judged the more robust choice to build blind, per this build's
  instructions.
- **Allocation Preview implemented as computed, non-stored fields**: per
  design note 1 ("does not replace the flow"), no separate preview
  wizard/model was built. `preview_weight`, `preview_volume` and
  `preview_value` are computed Float fields added directly to
  `stock.valuation.adjustment.lines` and shown as extra columns on the
  existing embedded list on the landed cost form - the draft-state
  adjustment lines already *are* the pre-posting preview core provides.
- **Landed cost form button/xpath targets not verified against a live
  instance**: the "Auto-Allocate" button is inserted via
  `<xpath expr="//header" position="inside">` (assumes core's form already
  has a `<header>`, which is near-certain given the Compute/Validate
  buttons and status bar shown in `ui.png`), and the preview
  columns/Details button are inserted via
  `<xpath expr="//field[@name='valuation_adjustment_lines']/tree" position="inside">`
  (assumes the embedded list still uses the `<tree>` tag in the target
  Odoo 17 database, not the newer `<list>` tag). Adjust the xpaths if
  either assumption is wrong on the target version.
- **`split_method` column on the `cost_lines` embedded list left
  untouched**: core's own cost-lines tree is understood to already show
  `split_method` (needed for the manual entry workflow the spec says this
  module doesn't replace), so nothing was added there to avoid a
  duplicate-field view error if that assumption is right. Verify against
  the target version and add the field via xpath only if it turns out to
  be genuinely missing.
- **No new "Allocated" status**: `ui.png`'s status bar mockup shows
  Draft &rarr; Allocated &rarr; Posted. Core `stock.landed.cost` is
  understood to only have Draft/Posted (`draft`/`done`) states; adding a
  third, module-defined state would mean intercepting/wrapping core's own
  state transitions, which risks the accounting flow itself - explicitly
  out of scope per design note 1. Auto-Allocate instead works entirely
  within the Draft state, and the existing Draft/Posted status bar is left
  untouched.
- **Menu placement not verified**: the new "Landed Cost Allocation Rules"
  menu is placed under `stock.menu_stock_config_settings` (Inventory >
  Configuration), the conventional Odoo 17 xmlid for that menu, but this
  could not be confirmed against source in this environment. Update the
  `parent` in `views/landed_cost_allocation_rule_views.xml` if it differs
  on the target version.
- **Security group for the new model**: `landed.cost.allocation.rule` uses
  `stock.group_stock_user` (read-only) and `stock.group_stock_manager`
  (full CRUD), the safe default suggested for this build, since core
  `stock_landed_costs`'s own access group for managing landed costs could
  not be confirmed without source. Swap in an accounting-manager group
  instead if that better matches how landed costs are managed on the
  target instance.
- **Community Edition compatibility**: `stock_landed_costs` is a Community
  Edition module (landed costs are not an Enterprise-only feature in
  Odoo), so this module's Enterprise/Community compatibility badges in
  `index.html` reflect that; no Enterprise-only dependency was introduced.
- **Automated tests**: written
  (`tests/test_landed_cost_auto_allocator.py`), covering rule-matching
  priority order, the data-quality check raising for missing weight data
  and passing with complete data, mixed allocation (two lines, two
  different split methods, independently-correct per-line amounts summing
  back to each cost line's own total), rule application by Auto-Allocate,
  and non-empty method-appropriate `allocation_breakdown` text - but not
  executed against a live Odoo instance (none available in this
  environment). Run `--test-enable -i landed_cost_auto_allocator` before
  merging, and fix any field-name mismatch the run surfaces against the
  assumptions listed above.
- **Live-instance screenshots**: skipped per instruction for this build
  round; the supplied `ui.png` was copied to
  `static/description/assets/main_screenshot.png` and is reused across the
  Screenshots and Page Experience sections of `index.html` since it is the
  only screenshot asset available.
- **`icon.png`**: not supplied in the module brief folder
  (`09-landed-cost-auto-allocator/`), so `static/description/icon.png` was
  not created and the manifest has no `icon` key.
- **"Why Choose ERP23" listing icons**: the six standard `.webp` badge
  images referenced by the `erp23-module-index-generator` skill are not
  bundled with the skill in this environment. Used Font Awesome icon
  glyphs in the same card layout instead of `<img>` tags, matching the
  pattern already used in `lot_recall_report`, `mrp_variant_bom_manager`
  and `quality_tolerance_checks`.
- **Pricing**: left as TBD; run the `erp23-odoo-pricing-advisor` skill
  before listing on the Apps Store.

## 19.0.1.0.0

Ported to Odoo 19. Verified against the real `odoo/odoo` 19.0 source tree
(a sparse clone of `github.com/odoo/odoo` at the `19.0` branch) — every
field/method name this module assumed for core `stock_landed_costs` (which
was in fact vendored source in this pass, unlike a couple of sibling
modules whose core dependency is Enterprise-only) turned out correct
except one real bug:

- **Embedded list tag fixed**: the `valuation_adjustment_lines` one2many
  is rendered with a `<list>` tag in core's form view, not `<tree>` — this
  module's xpath (`//field[@name='valuation_adjustment_lines']/tree`)
  would have failed to match at install, breaking the whole view
  inheritance. Fixed to target `<list>`.
- **Removed redundant preview fields**: core's `stock.valuation.adjustment.lines`
  already has `weight` and `volume` fields (populated by
  `compute_landed_cost()`, `optional="hide"` in the default list) and an
  already-visible `former_cost`. The `preview_weight`/`preview_volume`/
  `preview_value` computed fields this module added were duplicating that
  data via a separate, independently-computed formula
  (`product.weight * quantity`) instead of just showing what core already
  stores — removed them, and the view now simply flips `weight`/`volume`
  to `optional="show"` via two small xpath attribute changes instead of
  adding new field nodes. `former_cost` needed no change (already
  visible). This is a simplification, not a version-porting fix — it
  would have applied equally to the 17.0.1.0.0 release.
- **Confirmed correct, unchanged**: `split_method` (and its five values),
  `stock.valuation.adjustment.lines`' `cost_line_id`/`quantity`/
  `additional_landed_cost` fields, `stock.landed.cost.compute_landed_cost()`,
  `stock.picking.move_ids`, `product.type` (`consu`/`service`/`combo`,
  confirming the `!= 'service'` filter in `_get_relevant_moves` is still
  correct), and `stock_landed_costs.view_stock_landed_cost_form`.
- Also noted for future reference: `product.template.split_method_landed_cost`
  exists in core (a per-product default split method) — this module's own
  `landed.cost.allocation.rule` model overlaps with it somewhat. Not
  changed in this pass since it works correctly as-is, but a future
  version could read this core field as an additional fallback layer
  before falling back to `equal`.
