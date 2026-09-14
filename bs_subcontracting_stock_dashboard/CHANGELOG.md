# Changelog

## 19.0.1.0.0

Initial release.

### Deviations from specs.md

- **Vendor resolution and product cost read via ORM, not raw SQL:**
  `res.partner.property_stock_subcontractor` and `product.product.standard_price`
  are both `company_dependent` fields, stored as JSONB in recent Odoo
  versions rather than plain columns — not practical (or version-stable)
  to join against directly in the `subcontracting.stock.report` SQL view.
  Both are instead exposed as non-stored compute fields resolved through
  the ORM, which handles the JSONB/company lookup transparently. The SQL
  view itself only touches plain FK/date/boolean columns.
- **Aging is deliberately non-stored:** `age_days`/`aging_bucket` must keep
  advancing purely from calendar time passing, with no write ever touching
  the underlying quant — a stored compute would go stale the moment nobody
  touches a record (same reasoning as `bs_purchase_reorder_optimizer`'s
  stale-orderpoint fields).
- **Drill-down (feature 5)** reuses the native `stock.quant` / `stock.move.line`
  list views with a pre-set domain, rather than building a custom read
  model just to re-display the same records the SQL view already reads.
- **Dashboard's date-range control from the mockup was dropped**: `stock.quant`
  is a point-in-time snapshot, not a historical series, so a "last 7 days"
  filter has no well-defined meaning for current on-hand stock. The Aging
  Report and drill-down views cover the historical/dated angle instead.
- **Overdue alert (feature 6)** is anchored to the vendor's own
  `res.partner` record (which supports `mail.activity`/chatter natively)
  rather than to a specific quant/location — it's a review nudge for that
  vendor's overall situation, not a per-line note.
- **Multi-company record rule added post-audit:** `subcontracting.stock.report`
  is a SQL view and doesn't automatically inherit `stock.quant`'s own
  multi-company rule (record rules are per-model). Added a matching
  `[('company_id', 'in', company_ids)]` rule so a user restricted to one
  company can't see another company's subcontracting stock through the
  dashboard.
- **Branding assets:** `icon.png` and `main_screenshot.png` were supplied
  in the prompt's source folder and used as-is; `banner.png` was not
  supplied.
