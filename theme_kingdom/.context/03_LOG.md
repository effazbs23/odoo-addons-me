# Development Log

---

## 2026-06-01

### Asset convention: `static/content/`

* Documented `content/css`, `content/font`, `content/img`, `content/js` under `static/`.
* CSS split: `variables.css`, `styles.css`, `responsive-*.css` (no `@media` in main styles).

### Context Migration: nopCommerce → Odoo Website Theme

* **Rules & persona** — Updated `00_RULES.md` for Odoo module isolation, QWeb, and asset bundles.
* **Reference** — Replaced nopCommerce paths with standard Odoo theme layout, SCSS tokens, and QWeb patterns in `01_REFERENCE.md`.
* **Skills** — Added `odoo_theme_master.md`; retired `nop_theme_master.md`.
* **Bridge** — `context_bridge.md` now maps tasks to Odoo-specific skills.
* **State** — Reset roadmap template for Odoo theme phases.

---

## Earlier (nopCommerce era — archived)

* Context optimization with modular skills and context bridge (2026-05-13).
* Homepage BlogNews plugin work — **superseded**; do not apply nopCommerce paths to Odoo tasks.
