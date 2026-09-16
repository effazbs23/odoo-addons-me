# Changelog

## 17.0.1.0.0

Initial release.

### Deviations from `specs.md` / `prompt.md`

- **No live POS-register / website-cart JavaScript hooks**: `ui.png` and
  `specs.md` design note 3 imply true sub-second, per-keystroke hooks into
  the POS Owl frontend and the website checkout cart JS. Building and
  testing that reliably needs a live Odoo instance with a running POS
  session and browser, which is not available in this environment. This
  release scopes the module to a solid backend mechanism instead: a
  `stock.soft.reservation` model that is created/updated from
  `sale.order.line` create/write (website and B2B orders) and from
  `pos.order` create/write (POS orders, see next point), plus native Odoo
  dashboard views approximating `ui.png`'s panels. True live-browser POS
  and website JS hooks are flagged here as the v2 item. This mirrors how
  `mrp_finite_capacity_scheduler` scoped its Gantt side panels to separate
  list views for the same reason.
- **POS soft reservations piggyback on the existing order sync, not a
  live frontend hook**: per spec design note 3, `pos.order` soft holds are
  created/refreshed from `create()`/`write()` on the backend model, which
  fires when the POS register syncs an order to the server -- in standard
  POS flows that is typically around payment/closing, not while the
  cashier is still building the cart. So, honestly, the soft hold mostly
  overlaps with the order becoming final rather than pre-empting it during
  cart-building. A true per-keystroke hold at the register needs a POS Owl
  JS patch and a live POS session to build/test against; noted in
  `models/pos_order.py` and flagged here as the v2 item.
- **Unverified core `pos.order` hook**: with no vendored copy of core
  `point_of_sale` in this environment to confirm the exact internal method
  that finalizes an order (e.g. `_process_order`), the safety-net oversell
  check and the reservation-graduation step are triggered from the most
  conservative, always-present hook available: a `write()` override that
  detects the `state` field transitioning into `('paid', 'done',
  'invoiced')`. Verify against the target instance's actual POS order
  lifecycle before relying on this in production; a version-specific
  `_process_order`/`_finalize_validation` override may be a cleaner hook if
  available.
- **Unverified `pos.config.picking_type_id.warehouse_id` chain**: same
  reason -- used based on the standard Odoo POS <-> stock link
  (`pos.config.picking_type_id` -> `stock.picking.type.warehouse_id`) but
  not confirmed against source in this environment.
- **B2B channel detection heuristic**: Odoo has no single flag meaning
  "this sale order is a B2B portal order". This release treats any
  non-website order created by a portal user (`create_uid.share` is
  `True`) as B2B; internal sales staff placing an order directly are not
  treated as a soft-reserved channel at all (their stock commitment goes
  through core's own reservation at confirmation, unchanged from before
  this module). See `SaleOrder._get_multichannel_channel()`.
- **Category-level guard/buffer inheritance heuristic**: per feature 5 and
  the design note to mirror a core-style recursive lookup,
  `product.category._is_overselling_guard_enabled()` and
  `_get_effective_default_buffer_qty()` climb to the parent category when
  the field is not set on the category itself. Both fields are plain
  Boolean/Float with no distinct "not configured" state, so `False`/`0.0`
  are treated as "not configured" and climbing continues. The known
  tradeoff: a sub-category cannot explicitly opt back OUT of guarding (or
  override a non-zero buffer down to zero) once an ancestor category has
  it set, since there is no way to distinguish "explicitly False" from
  "unset". A tri-state field would remove this ambiguity in a v2.
- **`multichannel.sellable.report` SQL view does not climb the category
  tree for its buffer fallback**: the Python helper
  (`product.product._get_reserved_buffer_qty` /
  `product.category._get_effective_default_buffer_qty`) climbs to parent
  categories, but the reporting SQL view only falls back to the product's
  *own* category's `default_reserved_buffer_qty` (no explicit buffer row
  -> that category's own default, not a recursive parent walk). Recursion
  in a plain SQL view would need a recursive CTE against `product_category`
  and was judged not worth the added complexity/risk for a reporting view
  that can't be tested against a live Postgres in this environment. Flagged
  as a known simplification, not expected to matter much in practice since
  categories with the guard enabled will typically set their own default.
- **Per-channel "Available to Promise" is approximated, not truly
  channel-attributed**: `ui.png`'s three "Available to Promise" cards (POS
  / eCommerce / B2B) imply sellable stock split by channel. Sellable stock
  itself has no channel -- only reservations do -- so a true per-channel
  breakdown would need to attribute physical stock allocation to a
  channel, which is out of scope here. The `multichannel.sellable.report`
  Sellable Now view instead reports one aggregate, warehouse-level
  "Sellable Now" figure per product, with its kanban grouped by warehouse
  rather than by channel. A genuine per-channel split (e.g. earmarking a
  slice of on-hand stock to each channel) is a good v2 idea.
- **`get_sellable_now` uses `qty_available` ("On Hand"), not
  `free_qty`**: `ui.png`'s Reserved Buffer / Sellable Now tables literally
  label a column "On Hand" separate from "Reserved", so `on_hand` is the
  raw physical on-hand quantity (`product.qty_available` scoped to the
  warehouse via context), with buffer and reservations subtracted
  separately to reach `sellable_now`. This matches the mockup but means
  `on_hand` does not itself reflect core Odoo's own stock reservations
  (`free_qty`/`virtual_available` already account for those); the module's
  guarding logic subtracts soft + confirmed reservations on top of raw
  on-hand instead of layering onto `free_qty`, to avoid double-subtracting
  core's own reservation against this module's own bookkeeping.
- **Oversell safety net only flags, never blocks or reverses**: an
  explicit, deliberate behavior decision per feature 3 and design note 4
  ("defense in depth, not the primary mechanism") -- `sale.order.
  action_confirm()` and the POS order finalization hook both call
  `super()`/proceed normally first, then create a
  `multichannel.oversell.alert` record if the confirmed quantity turns out
  to have oversold. The sale is never raised as an error, reversed, or
  held back.
- **Unverified core `product.category` form view/action external IDs**:
  no vendored copy of the core `product` module in this environment to
  confirm against. `views/product_category_views.xml` inherits
  `product.product_category_form_view` and `views/menus.xml` links to
  `product.product_category_action_form`, both based on standard Odoo 17
  Community naming convention. Verify and adjust if the target Odoo
  version uses different IDs (same caveat `quality_tolerance_checks` flagged
  for its own core `quality` view IDs).
- **Automated tests**: written
  (`tests/test_multichannel_overselling_guard.py`), covering soft
  reservation creation/expiry via the cron, `_get_active_reserved_qty`
  summation, `_sync_soft_reservation` create/update/release behavior,
  category guard/buffer inheritance (including the climb-to-parent
  tradeoff above), `get_sellable_now` arithmetic both with guarding
  enabled and disabled, the oversell alert's `_check_and_flag_oversell`
  helper called directly with contrived quantities (no live
  website/POS checkout flow needed), and the `multichannel.sellable.report`
  SQL view querying without error -- but not executed against a live Odoo
  instance (none available in this environment). Run `--test-enable -i
  multichannel_overselling_guard` before merging. `python3 -m py_compile`
  was run on every `.py` file and every `.xml` file was parsed for
  well-formedness; neither substitutes for the real test run.
- **Live-instance screenshots**: skipped per instruction for this build
  round; the supplied `ui.png` was copied to
  `static/description/assets/main_screenshot.png` and reused across the
  Screenshots and Page Experience sections of `index.html` since it is the
  only screenshot asset available (same pattern `quality_tolerance_checks`
  used).
- **`icon.png`**: not supplied in the module brief folder
  (`08-multichannel-overselling-guard/`), so `static/description/icon.png`
  was not created and the manifest has no `icon` key.
- **"Why Choose ERP23" listing icons**: the six standard `.webp` badge
  images referenced by the `erp23-module-index-generator` skill are not
  bundled with the skill in this environment. Used Font Awesome icon
  glyphs in the same card layout instead of `<img>` tags, matching the
  pattern already used in `lot_recall_report`, `mrp_variant_bom_manager`
  and `quality_tolerance_checks`.
- **Category (`Inventory/Inventory` vs `Sales/Sales`)**: the module
  mechanism lives in stock/reservation logic (`stock.soft.reservation`,
  the buffer and sellable-now report), so `Inventory/Inventory` was picked
  over `Sales/Sales`, even though the confirmation hooks it adds live on
  `sale.order`/`pos.order`.
- **Pricing**: left as TBD; run the `erp23-odoo-pricing-advisor` skill
  before listing on the Apps Store.

## 19.0.1.0.0

Ported to Odoo 19. Verified against the real `odoo/odoo` 19.0 source tree
(a sparse clone of `github.com/odoo/odoo` at the `19.0` branch), including
`odoo/addons/base` for framework-level models (a separate location from
the top-level `addons/` directory in this repo layout). No functional
code changes were needed — the following previously-unverified
assumptions are all confirmed correct:

- `pos.order.config_id` → `pos.config.picking_type_id` →
  `stock.picking.type.warehouse_id` chain (used to resolve a POS order's
  warehouse).
- `product.product.qty_available` / `free_qty`, `res.users.share` (the
  B2B-channel-detection heuristic), `product.template.categ_id`,
  `stock.warehouse.view_location_id`, and `stock.quant.quantity` — all
  used directly in the `multichannel.sellable.report` SQL view.
- `product.product_category_form_view` (with its `parent_id` field as
  the xpath anchor) and `product.product_category_action_form` — both
  confirmed against `addons/product/views/product_category_views.xml`.
- `point_of_sale`, `website_sale`, `sale`, `stock_landed_costs` all
  confirmed present in Odoo Community 19.0 (this module's own
  CE-compatibility claim was correct, unlike two sibling modules in this
  batch that incorrectly claimed CE support for Enterprise-only
  dependencies — see `quality_tolerance_checks` and
  `mrp_intercompany_wo_sync`).
- No occurrences of the `mrp.workorder`/`mrp.production` `date_planned_*`
  → `date_*` rename or the `mrp.production.lot_producing_id` →
  `lot_producing_ids` rename found in this module's code (it doesn't
  touch either field), so neither applies here.

Everything else from 17.0.1.0.0 above — the lack of live POS/website JS
hooks, the sync-cadence approximation, the aggregate (not
per-channel-attributed) "Sellable Now" figure — remains unchanged and
still applies in 19.0.
