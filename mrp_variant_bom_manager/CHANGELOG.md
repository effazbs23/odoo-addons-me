# Changelog

## 17.0.1.0.0

Initial release.

### Deviations from `specs.md` / `prompt.md`

- **Per-cell independence vs. the underlying data model**: `ui.png` shows
  every (BOM line, variant) cell toggled fully independently. The actual
  core field this module works on
  (`mrp.bom.line.bom_product_template_attribute_value_ids`) only supports
  an AND-of-attribute-values filter — a line applies to every variant
  whose combination is a *superset* of the chosen values. That means not
  every possible on/off pattern across variants can be represented
  exactly by a single filter. Each toggle (single cell, bulk apply/remove,
  and copy-to-variant) is resolved by recomputing the smallest common set
  of attribute values shared by every variant that should end up "on" for
  that line (see `_apply_line_variant_set` in `models/mrp_bom.py`). When no
  exact set exists for the requested pattern, the previous filter is left
  untouched and the UI shows a warning recommending the BOM line be split
  instead of silently applying something incorrect. This keeps the module
  a UI/UX layer with no new data model, per design note 1, at the cost of
  not every literal on/off pattern in the mockup being achievable in one
  step.
- **Frontend widget authored without a live Odoo instance**: the OWL
  matrix widget (`static/src/js/mrp_bom_variant_matrix.js` and its
  template) follows Odoo 17's documented field-widget registration and
  relational-field-value conventions, but was written and syntax-checked
  (`node --check`) without a running Odoo frontend to render/debug it
  against. Before shipping, load the module in a real Odoo 17 instance,
  open a BOM's "Variant Matrix" button, and check the browser console
  for any field-value-shape or template mismatches.
- **BOM form button placement**: inserted via
  `<xpath expr="//sheet" position="before">` wrapped in a new `<header>`,
  rather than anchoring next to a specific existing button, since the
  exact button layout of `mrp.mrp_bom_form_view` could not be verified
  without a running instance. Adjust the xpath/placement once verified
  against the target Odoo version.
- **Automated tests**: written (`tests/test_mrp_bom_variant_matrix.py`),
  covering the matrix computation, exact/inexact toggle resolution,
  zero-applicable-line warnings, core-`explode()`-based preview, and
  copy-to-variant — but not executed against a live Odoo instance (none
  available here). Run `--test-enable -i mrp_variant_bom_manager` before
  merging.
- **Live-instance screenshots**: skipped per instruction for this build
  round; the supplied `ui.png` was copied to
  `static/description/assets/main_screenshot.png` as the listing's hero
  image.
- **`icon.png`**: not supplied in the module brief folder, so
  `static/description/icon.png` was not created and the manifest `icon`
  key was left unset.
- **Pricing**: left as TBD; run the `erp23-odoo-pricing-advisor` skill
  before listing on the Apps Store.
