# Changelog

## 17.0.1.0.0

Initial release.

### Deviations from `specs.md` / `prompt.md`

- **Custom dashboard side panels**: `ui.png` shows a Gantt view with docked
  "Due-Date Risk", "Unscheduled Work Orders" and "Utilization (This Week)"
  panels alongside it. Odoo's native `<gantt>` view (from `web_gantt`)
  does not support arbitrary docked side panels without a custom OWL
  controller/template override. For this release those three panels are
  implemented as separate, filterable list views/menu items
  (`Finite Capacity Scheduler` list mode with "Unscheduled"/"At Risk"
  filters, and a `Workcenter Capacity` list with a utilization progress
  bar) rather than an embedded side panel next to the Gantt chart itself.
  Recreating the exact docked-panel layout is a natural v2 enhancement
  once there's a running Odoo instance to iterate the frontend against.
- **Enterprise dependency**: per `specs.md` item 6, this module targets
  Odoo Enterprise and depends on `web_gantt` for the `<gantt>` view type.
  This is called out explicitly here and in the App Store listing.
- **Menu/view external IDs** (`mrp.menu_mrp_planning`,
  `mrp.mrp_workcenter_view`): used based on standard Odoo naming, but not
  verified against a running instance in this environment. Verify and
  adjust if the target Odoo version uses different IDs.
- **Auto-schedule algorithm**: implemented as a simple greedy first-fit
  heuristic per `specs.md` item 4 (sort by MO due date, place in the
  earliest non-overlapping slot on the work order's own workcenter). It
  does not account for a workcenter's working calendar (it will happily
  schedule into off-hours) or capacity > 1 concurrency — both are called
  out as good v2 refinements, kept out of v1 to keep the heuristic simple
  and auditable per the spec's explicit scoping note.
- **Automated tests**: written (`tests/test_mrp_finite_capacity_scheduler.py`)
  but not executed against a live Odoo instance in this environment (none
  available). Run `--test-enable -i mrp_finite_capacity_scheduler` before
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

## 19.0.1.0.0

Ported to Odoo 19. Verified against the real `odoo/odoo` 19.0 source tree
(a sparse clone of `github.com/odoo/odoo` at the `19.0` branch) rather than
guessing — the following were corrected as a result:

- **`mrp.workorder` date fields renamed**: `date_planned_start` /
  `date_planned_finished` do not exist on `mrp.workorder` in 19.0 — the
  real fields are `date_start` / `date_finished`. Every reference across
  `models/mrp_workorder.py`, `models/mrp_workcenter.py`,
  `wizard/mrp_auto_schedule_wizard.py`, `views/mrp_workorder_views.xml`
  (including the `<gantt date_start=".." date_stop="..">` attributes,
  which are unrelated fixed attribute names on the `<gantt>` tag itself —
  only the field names they point to changed), the tests, and the
  `index.html` copy have been updated. **This means the 17.0.1.0.0
  release above targets Odoo 17's actual field names for this model; if
  installing on 17.0/18.0 specifically, double-check whether those
  versions already use `date_start`/`date_finished` too — Odoo renamed
  this at some point between 17 and 19 and the exact version boundary
  was not pinned down in this pass.**
- **`resource.calendar.attendance` has no `date_from`/`date_to` fields**:
  `_compute_capacity_per_day` incorrectly filtered attendance lines on
  `date_from`/`date_to` (those fields belong to `resource.calendar.leaves`,
  a different model, not the weekly recurring attendance lines). This
  would have raised an `AttributeError` in any Odoo version, not just 19 —
  it's a genuine bug fix, not a version-porting change. Replaced with a
  filter on `display_type` (excludes the section/separator rows the
  attendance list widget can contain), which is the correct, existing
  field on this model.
- **`mrp.menu_mrp_planning` does not exist**: the real external id for
  Manufacturing's "Planning" root menu is `mrp.mrp_planning_menu_root`.
  Fixed in `views/menus.xml`. (`mrp.mrp_workcenter_view` was verified
  correct and left unchanged.)
- Not independently verified this pass (no source available — `web_gantt`
  is an Enterprise-only module not in the public `odoo/odoo` repo): the
  `<gantt>` view's own attributes (`default_group_by`, `color`,
  `precision`, `default_scale`) are assumed unchanged from 17 to 19.
  Verify against a real Enterprise 19.0 instance before install.
