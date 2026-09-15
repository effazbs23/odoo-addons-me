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
