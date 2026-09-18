# Changelog

## 17.0.1.0.0

Initial release.

### Deviations from `specs.md` / `prompt.md`

- **XLSX export**: the spec calls for "base_xlsx style patterns already used
  elsewhere in the ERP23 catalog", but this repository does not yet contain
  a shared `base_xlsx` abstraction to reuse (this module is the first
  addon in the catalog). Implemented a small, self-contained XLSX builder
  (`report/lot_recall_report_xlsx.py`) using `xlsxwriter` directly. Swap
  this out for the shared base module once one exists in the catalog.
- **`lot.recall.report.line` fields**: extended beyond the seven fields
  listed in `specs.md` (`partner_id, sale_order_id, delivery_id, quantity,
  uom_id, delivery_date, lot_id`) with `direction`, `source_type`,
  `purchase_order_id`, `production_id`, and `component_lot_id`. The single
  line model needs to represent both forward (customer delivery) and
  backward (vendor receipt / manufacturing / component lot) rows, which
  isn't possible with the original field set alone.
- **Menu location**: `features.md`/`specs.md` ask for the report menu
  under Inventory > Reporting. The exact external ID of the core
  "Reporting" submenu differs across Odoo versions and could not be
  verified without a running instance, so the menu is placed at the
  Inventory app's root menu bar instead (`menu_bs_lot_recall_report`,
  parent `stock.menu_stock_root`) to guarantee a working install. Update
  the `parent` once verified against the target Odoo version.
- **Live-instance screenshots** (step 5 of `prompt.md`): skipped per
  explicit instruction for this build round — no running Odoo instance
  was available/used, and workflow screenshots were not captured. The
  supplied `ui.png` was copied to
  `static/description/assets/main_screenshot.png` as a stand-in visual
  reference for the App Store listing.
- **`icon.png`**: not supplied in the module brief folder
  (`01-lot-recall-report/`), so `static/description/icon.png` was not
  created and the manifest's `icon` key was left unset. Generate one via
  the `erp23-logo-generator` skill and wire it into the manifest.
- **Automated tests**: written (`tests/test_lot_recall_report.py`) but not
  executed against a live Odoo instance in this environment (none
  available). Run `--test-enable -i bs_lot_recall_report` before merging.
- **Pricing**: left as TBD; run the `erp23-odoo-pricing-advisor` skill
  before listing on the Apps Store.
- **"Why Choose ERP23" listing icons**: the six standard `.webp` badge
  images (silver-partner, countries-served, etc.) referenced by the
  `erp23-module-index-generator` skill are not bundled with the skill and
  not present in this module. Used Font Awesome icon glyphs in the same
  card layout instead of `<img>` tags so the section could stay in rather
  than be dropped. Swap in the real badge art if/when it's added to the
  catalog.

## 19.0.1.0.0

Ported to Odoo 19. Verified against the real `odoo/odoo` 19.0 source tree
(a sparse clone of `github.com/odoo/odoo` at the `19.0` branch) rather
than guessing:

- **`mrp.production.lot_producing_id` no longer exists**: Odoo 19's
  `mrp.production` tracks produced lots/serials via a many2many
  `lot_producing_ids` (multiple serials can be produced per order), not a
  singular `lot_producing_id` many2one. `_build_backward_lines`'s search
  domain was updated from `('lot_producing_id', '=', lot.id)` to
  `('lot_producing_ids', 'in', lot.id)`. **This was a real bug with no
  test coverage** — added `test_backward_trace_manufacturing` to close
  that gap and catch a regression if this changes again.
- **Confirmed correct, unchanged**: `stock.view_production_lot_form`
  (previously flagged as an unverified assumption — now confirmed against
  `addons/stock/views/stock_lot_views.xml`), `stock.move.sale_line_id`,
  `stock.picking.sale_id`, `stock.move_line.picking_id...purchase_line_id`
  chain (`addons/purchase_stock/models/stock_move.py`), and
  `mrp.production.date_finished`/`qty_produced`/`move_raw_ids`. The
  `stock.move.line.qty_done` vs `quantity` defensive check
  (`'qty_done' in ml._fields`) was already forward-compatible: `qty_done`
  is fully gone in 19.0, and the code already falls through to
  `.quantity` correctly.
- **`stock.menu_stock_root` confirmed to exist** as the Inventory app's
  root menu (referenced as a parent by several core menu items in
  `addons/stock/views/stock_menu_views.xml`); the menu-placement deviation
  noted in 17.0.1.0.0 above still applies (placed at the app root rather
  than nested in the exact "Reporting" submenu), but the anchor menu
  itself is verified real.
