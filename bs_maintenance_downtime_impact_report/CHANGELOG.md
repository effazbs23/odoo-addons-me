# Changelog

## 19.0.1.0.0

- Initial release.
- **Deviation from specs.md design note 1**: the spec assumed core Maintenance
  already exposes an `equipment_ids` link on `mrp.workcenter`. It does not —
  in Community Edition there is no maintenance↔manufacturing bridge at all
  (that link only ships as the Enterprise `mrp_maintenance` module). This
  module adds its own `workcenter_id` field on `maintenance.equipment` (and
  the inverse `equipment_ids` on `mrp.workcenter`) instead of depending on
  Enterprise, keeping the whole module Community-compatible.
- Added `icon.png`, `main_screenshot.png`, and an animated `banner.gif`
  (used as the top listing-page banner) once supplied in the source assets
  folder.
- The dashboard passes `className="'o_downtime_content'"` to `<Layout>` and
  scopes `overflow-y: auto; min-height: 0;` to it in the SCSS, so the page
  scrolls correctly instead of being clipped by Odoo's `.o_action_manager`
  (which is `overflow: hidden` by design) when the dashboard content is
  taller than the viewport.
