# Changelog

## 17.0.1.0.0

Initial release.

### Deviations from `specs.md` / `prompt.md`

- **Unverified core `quality` view/field references**: this environment has no
  vendored copy of the core `quality` addon to read directly, so the
  following are used based on standard Odoo 17 Community `quality` module
  conventions but could not be confirmed against source: the form view
  external IDs `quality.quality_point_view_form` and
  `quality.quality_check_view_form`; that `quality.point` already exposes
  a `norm_unit` Char field (reused as-is, per the design, rather than
  adding a new unit field); that `quality.check` already exposes a
  related/stored `test_type` field mirroring `point_id.test_type` (used
  in `invisible` conditions on the inherited check form); and the
  `quality.alert` field names `check_id`, `product_id`, `product_tmpl_id`,
  `title`, `description` used by `_create_tolerance_alert()`. Verify all
  of these against the target Odoo version before merging and adjust the
  view xpaths/field names if any differ.
- **"Control Chart" button implemented as `type="object"`, not
  `type="action"`**: the chart must be filtered to the check's own
  `point_id`, which is a per-record, dynamic value. A plain
  `type="action"` button cannot carry a dynamic domain based on the
  current record's field values without extra context plumbing, so
  (matching the pattern already used for per-record dynamic actions in
  `mrp_variant_bom_manager`'s "Variant Matrix" button) the button calls
  an object method, `action_view_control_chart()`, which builds and
  returns the `ir.actions.act_window` dict with `domain=[('point_id',
  '=', self.point_id.id)]` at call time.
- **Control chart has no Target/Min/Max reference lines**: `ui.png`'s
  control-chart mockup shows dashed horizontal Target/Min/Max reference
  lines overlaid on the measurement trend. Odoo's native `<graph
  type="line">` view has no concept of static reference lines independent
  of the plotted series, so this release ships a plain measured-value
  line graph without them, per `specs.md` design note 4's explicit choice
  of the native graph view over an external charting library. Rendering
  the reference lines would need a custom OWL chart component (e.g. a
  small Chart.js- or D3-based widget) — flagged here as a good v2
  enhancement rather than attempted with the native view.
- **`_onchange_measured_value`/`write()` truthiness check on
  `measured_value`**: per the design, pass/fail is (re)computed "when
  measured_value is set" — implemented as a truthy check (`if
  check.measured_value`). A legitimate target/measurement of exactly
  `0.0` will not trigger the auto pass/fail evaluation on its own (Odoo
  Float fields have no distinct "unset" state to test against
  otherwise). Not expected to matter for machining/metal-fab tolerances
  in practice, but noted here since it's a real edge case.
- **No new security file**: this module adds no new models — only fields,
  onchanges and view/method extensions on core `quality.point` and
  `quality.check` — so there is nothing new to secure and no
  `security/ir.model.access.csv` is included; the manifest's `data` list
  has no security entry.
- **Automated tests**: written
  (`tests/test_quality_tolerance_checks.py`), covering tolerance
  snapshotting at check creation, snapshot immutability after the point
  is edited, pass/no-alert and fail/one-alert behavior on `write()`, the
  symmetric-mode onchange for both absolute and percentage deviation
  types, the range-mode onchange leaving min/max untouched, and
  `sibling_check_ids` measurement history — but not executed against a
  live Odoo instance (none available in this environment). Run
  `--test-enable -i quality_tolerance_checks` before merging.
- **Live-instance screenshots**: skipped per instruction for this build
  round; the supplied `ui.png` was copied to
  `static/description/assets/main_screenshot.png` as the listing's hero
  image and is reused across the Screenshots and Page Experience
  sections of `index.html` since it is the only screenshot asset
  available.
- **`icon.png`**: not supplied in the module brief folder
  (`07-quality-tolerance-checks/`), so `static/description/icon.png` was
  not created and the manifest has no `icon` key.
- **"Why Choose ERP23" listing icons**: the six standard `.webp` badge
  images referenced by the `erp23-module-index-generator` skill are not
  bundled with the skill in this environment. Used Font Awesome icon
  glyphs in the same card layout instead of `<img>` tags, matching the
  pattern already used in `lot_recall_report` and
  `mrp_variant_bom_manager`.
- **Pricing**: left as TBD; run the `erp23-odoo-pricing-advisor` skill
  before listing on the Apps Store.

## 19.0.1.0.0

Ported to Odoo 19. While verifying core assumptions against the real
`odoo/odoo` 19.0 source tree (a sparse clone of `github.com/odoo/odoo` at
the `19.0` branch), this surfaced a pre-existing correctness issue
unrelated to the version bump:

- **Confirmed Enterprise-only dependency**: the `quality` app (Quality
  Control) does not exist anywhere in the public `odoo/odoo` (Community)
  repository — it is Odoo Enterprise-only. This module was previously
  described as working "the same in Community and Enterprise"; that was
  wrong in every version, not just 19, and has been corrected throughout
  (manifest license changed to `OPL-1`, description, and `index.html`'s
  compatibility strip and Overview/Highlights text now state the
  Enterprise requirement plainly).
- **Core `quality` field/method names remain unverified**: since `quality`
  is Enterprise-only, it is not in the public repository this pass used
  to verify the other six modules, so none of this module's assumptions
  about `quality.point`/`quality.check` field names (`test_type`, `norm`,
  `norm_unit`, `tolerance_min`/`tolerance_max` naming precedent,
  `quality_state` selection values) or view external ids could be checked
  against real source. These remain exactly as documented in the
  17.0.1.0.0 section below — verify against a real Enterprise 19.0
  instance before installing.
- **No other Odoo-19-specific code changes were identified or made** in
  this module, since its own new models/fields don't touch any of the
  core APIs (`mrp.workorder`/`mrp.production` dates, etc.) that changed
  between 17 and 19 in the modules that do depend on Community `mrp`.
