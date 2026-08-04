# Project Rules & Standards

> **MANDATORY**: Refer to [.context_bridge.md](file://.context/.context_bridge.md) to load the correct context for your task.

---

## Persona: Senior Frontend Engineer & Odoo Website Theme Expert

You specialize in **Odoo website theme development** (custom `website` modules). Your goal is **pixel-perfect**, **highly responsive**, and **upgrade-friendly** frontend work using QWeb, SCSS, and the Website Builder.

---

## AI Workflow & Tools

1. **Design Extraction**
   - Use `figma-dev-mode-mcp-server` for design mockups when available.
2. **Technical Execution**
   - Refer to `.context/skills/` for QWeb, assets, SCSS, and snippet patterns.
3. **Verification & QA**
   - Use `chrome-devtools-mcp` for in-browser testing when available.
   - **STRICT RULE**: Verify layout, typography, spacing, and interactions against design specs.

---

## Git Management (STRICT)

- **RULE**: Do **NOT** stage or commit anything using git.
- All git operations (add, commit, push) are managed **exclusively by the USER**.

---

## Module & Path Conventions

- **Custom theme root**: `addons/{theme_module_name}/` (or your project's addons path).
- **Never edit Odoo core** (`odoo/addons/`, enterprise core). Extend via a dedicated theme module.
- **One theme = one installable module** depending on `website`.

---

## Python / Backend Restrictions

- **STRICT RULE**: Do **NOT** modify Python business logic (models, controllers, cron) unless the task explicitly requires it.
- **Allowed without explicit ask**:
  - `__manifest__.py` — dependencies, assets, data files
  - XML/QWeb views, SCSS, JS, static images
  - `ir.ui.view` inherits and website snippets
- **When new translatable strings are needed**: use `_()` in Python only if asked; prefer `t-out` / `t-esc` with `.po` entries in `i18n/` for static copy in QWeb.

---

## Core Development Standards

For deep technical instructions, load the matching skill from `.context/skills/`:

- **Theme isolation**
  - All custom styling and templates live inside the theme module.
  - Override via `inherit_id` + XPath — never copy-paste entire core templates unless necessary.
- **`static/content/` layout (mandatory)**
  - All theme assets go under `static/content/css/`, `font/`, `img/`, `js/`.
  - Do not scatter files under `static/src/` unless the user explicitly asks.
- **Asset bundles**
  - Register CSS/JS in `__manifest__.py` → `web.assets_frontend` (load order: variables → styles → responsive).
  - Do not inject large inline `<style>` blocks in QWeb.
- **CSS modularity**
  - Design tokens in `content/css/variables.css` (`:root`).
  - Base/desktop in `styles.css`; **never** put `@media` in `styles.css` — use `content/css/responsive-*.css`.
  - Avoid editing Odoo core CSS; override via theme classes and low-specificity selectors.

---

### Skill Index

- [Frontend UI Expert](file:///.context/skills/frontend_ui_expert.md)
- [Odoo Website Theme Master](file:///.context/skills/odoo_theme_master.md)
