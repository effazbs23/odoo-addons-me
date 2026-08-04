# Skill: Frontend UI Expert (Odoo Website)

---

## CSS Architecture (`static/content/css/`)

### File Organization

```text
static/content/css/
├── variables.css          # :root tokens only
├── styles.css             # base / desktop (NO @media here)
├── components.css         # cards, buttons, sections (optional)
└── responsive-*.css     # breakpoint overrides ONLY
```

* **Design tokens** — Only in `variables.css`; consume via `var(--*)` everywhere else.
* **STRICT**: No `@media` queries in `styles.css` or `variables.css`.
* **No core edits** — Never modify `odoo/addons/web` or `website` assets.
* **Specificity** — Prefer theme-prefixed classes (`.theme-*`, `.o_theme_*`); avoid `!important`.
* **Bootstrap** — Use Odoo/Bootstrap utilities when they fit; add custom rules in `content/css/`.

### Manifest load order

1. `variables.css`
2. `styles.css`
3. `components.css` (if present)
4. `responsive-*.css` (smallest breakpoint file last or order max→min — stay consistent per project)
5. `content/js/*.js` after CSS

---

## Fonts & Icons (`static/content/font/`)

* **Web fonts** — Files in `content/font/`; declare `@font-face` once in `variables.css` or top of `styles.css`.
* **Icon font** — `content/font/icon-font/`; use project icon classes in HTML/QWeb.
* **Paths** — Always absolute from site root: `/module/static/content/font/...`
* **No duplicate loads** — One `@font-face` per family/weight.

---

## Images (`static/content/img/`)

* Logos, heroes, icons (bitmap), snippet thumbnails under `img/` or `img/snippets/`.
* Reference in QWeb: `t-att-src="'/%s/static/content/img/file.png' % request.env['ir.module.module'].sudo().search([('name','=','{theme_module_name}')], limit=1).name"` — or hardcode module name in path: `/{theme_module_name}/static/content/img/file.png`.
* Optimize size; WebP where supported; `loading="lazy"` below the fold.

---

## Responsive Workflow

1. **Project breakpoints** (align with `01_REFERENCE.md`):

   | File | Width |
   |------|-------|
   | `responsive-max-480.css` | ≤480px |
   | `responsive-max-768.css` | ≤768px |
   | `responsive-max-1001.css` | ≤1001px |
   | `responsive-min-1201.css` | ≥1201px |

2. **Mobile-first vs max-width** — This project uses **max-width** override files; keep all `@media` inside `responsive-*.css` only.

3. **JS breakpoints** — Swiper/carousel `breakpoints` must match CSS files.

---

## JavaScript (`static/content/js/`)

* Register in `web.assets_frontend` via manifest.
* Prefer Odoo **public widgets** for DOM-bound behavior; plain `theme.js` for small vanilla helpers.
* Scope selectors to theme classes; avoid global `$()` unless legacy snippet requires it.
* Editor-only JS → `website.assets_editor`.

```javascript
/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ThemeCarousel = publicWidget.Widget.extend({
    selector: ".o_theme_carousel",
    start() {
        return this._super(...arguments);
    },
});
```

---

## Performance

* Compress images in `content/img/`.
* Minimize HTTP via manifest bundling (Odoo concatenates listed assets).
* After changes: upgrade module + hard refresh (`?debug=assets`).

---

## Restrictions

* Do **not** change Python unless explicitly requested.
* Do **not** add npm packages without approval.
* Do **not** create assets outside `static/content/` without user approval.
