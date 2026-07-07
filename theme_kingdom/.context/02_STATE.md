# Project State & Active Task

---

## High-Level Roadmap

* **Phase 1: Theme Module Scaffold**
  - [ ] Create `website`-dependent theme module with `__manifest__.py` assets.
  - [ ] Set up SCSS variables and bootstrap overrides.
  - [ ] Inherit `website.layout` for header/footer shell.

* **Phase 2: Core Pages & Snippets**
  - [ ] Homepage sections (hero, features, CTA).
  - [ ] Shop / product grid styling (if `website_sale` is installed).
  - [ ] Contact / footer blocks.

* **Phase 3: Website Builder & Polish**
  - [ ] Register custom snippets with preview thumbnails.
  - [ ] Responsive QA on mobile/tablet/desktop.
  - [ ] i18n pass for translatable strings.

---

## Current Active Task

> **Objective**: _(Update this section when starting a task — e.g. "Build homepage hero snippet and primary navigation inherit.")_

### Task Checklist

- [ ] Confirm theme module name and addons path.
- [ ] Register assets in `__manifest__.py`.
- [ ] Implement QWeb inherits (minimal XPath diffs).
- [ ] Add SCSS following modular partial structure.
- [ ] Test in browser (logged-in editor + public visitor).
- [ ] Update `03_LOG.md` when the task is done.

---

## Module Checklist (new theme)

- [ ] `depends`: `['website']` (+ `website_sale` if eCommerce)
- [ ] `assets` → `web.assets_frontend`
- [ ] `data` XML files listed in manifest
- [ ] Module installed/upgraded: `-u {theme_module_name}`
