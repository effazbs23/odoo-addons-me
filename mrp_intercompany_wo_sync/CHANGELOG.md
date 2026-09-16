# Changelog

## 17.0.1.0.0

Initial release.

### Deviations / assumptions from `specs.md` / `prompt.md`

This is the most architecturally uncertain module of the seven built in this
batch, since it sits on top of another module's (`sale_purchase_inter_company_rules`)
undocumented internals. Every assumption is called out here, and every place
the code depends on one is wrapped defensively (try/except + logged warning,
or a graceful no-op) so a wrong guess degrades instead of crashing core MO/
SO/PO flows for anyone else on the database.

- **No vendored core `sale_purchase_inter_company_rules` source found**: this
  environment has no full Odoo checkout, pip-installed `odoo` package, or
  vendored copy of core addons anywhere on the filesystem (checked
  `site-packages`, `/usr/lib/python3/dist-packages`, and a general
  filesystem search). Design note 1's expected fields/behavior (a company
  flag such as `intercompany_purchase_user`/`intercompany_sale_user`, an
  `auto_validation` setting, and however it links a generated PO back to its
  mirrored SO) could not be confirmed against real source. The module
  proceeds on the documented, reasonable assumption that confirming an
  intercompany purchase order (`button_confirm()`) is enough to make core
  auto-generate the mirrored sales order in the partner company, and that
  the discovery of that SO is inherently best-effort.
- **PO&rarr;SO discovery is a heuristic, not a guaranteed lookup**:
  `MrpProductionIntercompanyLink._find_matching_sale_order()` searches the
  child company for a `sale.order` whose `origin`/`client_order_ref`
  contains the purchase order's name, scoped to the requesting company's
  commercial partner. If core `sale_purchase_inter_company_rules` links the
  two records some other way (a dedicated reference field, for instance),
  this search simply won't find it, and the link stays in `po_created`
  state with `sale_order_id` empty -- the cron and the "Retry" button both
  re-attempt this lookup on every run, so the link self-heals once a
  correct match is possible, but this was never verified against a real
  intercompany PO/SO pair in a running instance.
- **Automatic hook + manual retry design, not an override of core confirm
  flows**: per the brief, the entire orchestration lives behind one method,
  `mrp.production.action_create_intercompany_supply()`. It is called
  automatically from `action_confirm()` (after `super()`, wrapped in a bare
  `try/except Exception` that only logs a warning) and manually via a
  "Check Intercompany Supply" button, mirroring how
  `multichannel_overselling_guard`'s `sale.order.action_confirm()` runs its
  safety-net check after `super()` and never lets it block the sale. An
  intercompany orchestration failure here can never block or roll back an
  MO's own confirmation.
- **Shortage detection is a simplification**: a raw-material move counts as
  "short" when its demand (`product_uom_qty`) exceeds the product's
  company-wide `free_qty` (via `with_company()`), not a
  warehouse/location-scoped reservation check. This avoids reimplementing
  Odoo's own multi-warehouse availability logic, at the cost of being less
  precise for multi-warehouse companies. See
  `MrpProduction._get_intercompany_shortage_moves()`.
- **Deduplication is per parent-MO/product, not per shortage event**: a
  second `action_create_intercompany_supply()` call (whether from a repeat
  `action_confirm()` or the manual button) skips a product that already has
  a non-`failed` link on the same parent production, per the spec. A
  previously `failed` link does not block a fresh attempt.
- **Pricing on the auto-created PO line**: uses a matching
  `product.supplierinfo` for the manufacturer's partner/product if one
  exists, else `product.standard_price`, else `list_price` -- deliberately
  no custom margin/costing logic, per design note 4 ("intercompany costing
  carried through automatically using existing intercompany pricing/margin
  rules"). This module does not attempt to replicate core's own
  intercompany pricelist behavior beyond giving the PO line *a* valid,
  sensible price; once core's automation mirrors the PO into an SO, any
  pricelist-driven repricing on that side is entirely core's own doing, not
  this module's.
- **`progress_percentage` formula** (documented since Community
  `mrp.production` has no native single "percent complete" field):
  1. If the link's `product_qty` (or the child production's own
     `product_qty` as a fallback) is known: `qty_produced / product_qty *
     100`, capped at 100.
  2. Else, if the child production has work orders: total logged
     `duration` over total `duration_expected` across its work orders, as a
     rough physical-progress proxy, capped at 100.
  3. Else: `0`.
- **Due-date exception reference date**: the parent MO's `date_deadline`
  (the commitment/customer date) is used as the "needed by" reference when
  set, since that is the more semantically correct "must have this
  component by" date; when no deadline is set, it falls back to the
  parent's own `date_planned_start` (the date the parent MO itself is
  planned to consume the component). The exception fires when the child
  production's `date_planned_finished` falls after that reference date.
  `date_planned_finished` is the same field name this repo's own
  `mrp_finite_capacity_scheduler` module already assumed for this Odoo 17
  target -- kept consistent with that assumption rather than introducing a
  different guess (e.g. `date_finished`).
- **BOM lookup for the child manufacturing order is wrapped defensively**:
  `mrp.bom._bom_find()`'s exact signature has changed across Odoo versions
  and no vendored core `mrp` source was available to confirm the Odoo 17
  one precisely. `_get_bom_for_product()` calls it inside a try/except and
  simply returns `False` (no BOM assigned, which core `mrp.production`
  tolerates) on any failure rather than guessing at parameters that might
  not match.
- **Unverified core view/menu/model external IDs**: no vendored copy of
  core `mrp`/`product` in this environment to confirm against. Based on
  standard Odoo 17 Community convention and flagged inline as XML comments
  in each file:
  - `mrp.mrp_production_form_view` (MO form inherit target, plus the
    `//header` and `//notebook` xpaths used to add the button and page).
  - `product.product_template_form_view` and the `purchase` group name
    (product template form inherit target for `intercompany_manufacturer_id`).
  - `mrp.menu_mrp_reporting` (parent menu for the new "Intercompany Supply
    Links" menu item, per the brief's "Manufacturing > Reporting or a new
    top-level item" choice -- Reporting was picked since the link list is
    an operational status view, not a configuration screen).
  Verify and adjust all of the above against the target instance before
  deploying.
- **Same-database, not cross-instance, scope restated**: per design note 5,
  this module only works when both companies live in the same Odoo
  database (a standard multi-company setup). It directly reads and creates
  `mrp.production`/`sale.order`/`purchase.order` records across companies
  via `sudo()`/`with_company()` -- there is no API, webhook, or messaging
  bridge to a separate Odoo instance. This is stated explicitly in the
  manifest `description` and prominently in the App Store `index.html`
  Overview section so buyers don't mistakenly expect cross-instance sync.
- **`intercompany_link_ids`/`as_child_intercompany_link_id` cross the
  multi-company record-rule boundary via `sudo()`**: standard Odoo
  multi-company record rules would otherwise hide another company's
  `mrp.production` from a user only assigned to the first company. Since
  this feature's entire premise is "read the other company's MO status",
  the relevant read/compute paths use `sudo()` deliberately -- this is by
  design, not an oversight, but is worth calling out for anyone auditing
  data access across companies.
- **Automated tests**: written
  (`tests/test_mrp_intercompany_wo_sync.py`), covering the
  `intercompany_manufacturer_id` field, `action_create_intercompany_supply`
  creating a PO and a correctly-populated link for a shortage scenario, no
  duplicate link on a repeated call, the `progress_percentage` formula, the
  `has_due_date_exception` flip when a child production's schedule slips
  past the parent's need date, and the cron method running without error on
  both an empty and a populated link set -- but not executed against a live
  Odoo instance (none available in this environment). Run `--test-enable -i
  mrp_intercompany_wo_sync` before merging. `python3 -m py_compile` was run
  on every `.py` file and every `.xml` file was parsed for well-formedness;
  neither substitutes for the real test run, especially given how much of
  this module's correctness depends on unverified core behavior.
- **Live-instance screenshots**: skipped per instruction for this build
  round; the supplied `ui.png` was copied to
  `static/description/assets/main_screenshot.png` and reused across the
  Screenshots and Page Experience sections of `index.html` since it is the
  only screenshot asset available (same pattern `multichannel_overselling_guard`
  and `quality_tolerance_checks` used).
- **`icon.png`**: not supplied in the module brief folder
  (`14-mrp-intercompany-wo-sync/`), so `static/description/icon.png` was
  not created and the manifest has no `icon` key.
- **"Why Choose ERP23" listing icons**: the six standard `.webp` badge
  images referenced by the `erp23-module-index-generator` skill are not
  bundled with the skill in this environment. Used Font Awesome icon
  glyphs in the same card layout instead of `<img>` tags, matching the
  pattern already used in `lot_recall_report`, `mrp_variant_bom_manager`,
  `quality_tolerance_checks` and `multichannel_overselling_guard`.
- **Pricing (App Store listing price)**: left as TBD; run the
  `erp23-odoo-pricing-advisor` skill before listing on the Apps Store.
