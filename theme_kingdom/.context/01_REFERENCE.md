# Technical Reference — Odoo Website Theme

---

## Core Setup

- **Local URL**: `http://localhost:8069/` (adjust port/host to your instance)
- **Theme module path**: `addons/{theme_module_name}/`
- **Website dependency**: `website` (and `web` implicitly)
- **Static assets root**: `static/content/` — **all** theme CSS, fonts, images, and JS live here

---

## Standard Module Layout

```text
{theme_module_name}/
├── __manifest__.py
├── __init__.py
├── static/
│   └── content/                    # PRIMARY asset folder (mandatory convention)
│       ├── css/
│       │   ├── variables.css       # design tokens (:root)
│       │   ├── styles.css          # base / desktop styles
│       │   ├── components.css      # optional partials
│       │   └── responsive-*.css    # breakpoint overrides only
│       ├── font/
│       │   ├── *.woff2 / *.woff / *.ttf
│       │   └── icon-font/           # custom icon font (optional)
│       ├── img/
│       │   ├── logo.png
│       │   └── snippets/           # snippet thumbnails
│       └── js/
│           └── theme.js
├── views/
│   ├── website_templates.xml
│   ├── snippets.xml
│   └── pages.xml
├── data/
│   └── website.xml
└── i18n/
    └── {lang}.po
```

> **Odoo rule**: Public URLs always start with `/static/`. Files are served as  
> `/ {theme_module_name} /static/content/{css|font|img|js}/...`

---

## Asset Bundle (`__manifest__.py`)

Load files in dependency order — variables first, responsive last:

```python
'assets': {
    'web.assets_frontend': [
        # CSS (order matters)
        '{theme_module_name}/static/content/css/variables.css',
        '{theme_module_name}/static/content/css/styles.css',
        '{theme_module_name}/static/content/css/components.css',
        '{theme_module_name}/static/content/css/responsive-max-768.css',
        '{theme_module_name}/static/content/css/responsive-max-480.css',
        # JS
        '{theme_module_name}/static/content/js/theme.js',
    ],
},
```

- **Do not** put `@media` blocks in `styles.css` — use `responsive-*.css` files only.
- Optional SCSS: if used, place under `static/content/css/` and list `.scss` paths the same way (Odoo compiles them in the bundle).
- Editor-only assets → `website.assets_editor` (not `web.assets_frontend`).

---

## Design Tokens (`variables.css`)

*Define under `:root` in `static/content/css/variables.css`:*

```css
:root {
  --primary-dark-blue: #041e42;
  --primary-light-blue: #62b5e5;
  --primary-orange: #f59a1f;
  --primary-grey: #9ea2a2;
  --dark-grey: #383640;
  --light-grey: #f5f5f5;
  --white: #ffffff;
  --black: #000000;
  --primary-font: 'Helvetica', Arial, sans-serif;
  --container-max-width: 1340px;
}
```

Use `var(--token-name)` in all other CSS files.

---

## Fonts & Icon Font

| Asset type | Path | Usage |
|------------|------|--------|
| Web fonts | `static/content/font/` | `@font-face` in `variables.css` or `styles.css` |
| Icon font | `static/content/font/icon-font/` | Custom classes (e.g. `icon-play`) |
| Reference | `static/content/font/icon-font/demo.html` | Icon glyph map (if present) |

**`@font-face` URL pattern** (from compiled CSS):

```css
@font-face {
  font-family: 'ThemeIcons';
  src: url('/{theme_module_name}/static/content/font/icon-font/theme-icons.woff2') format('woff2');
  font-weight: normal;
  font-style: normal;
  font-display: block;
}
```

---

## Images & QWeb Paths

| Use | QWeb / HTML path |
|-----|------------------|
| Logo | `/ {theme_module_name} /static/content/img/logo.png` |
| Snippet thumb | `static/content/img/snippets/my_snippet.png` |
| Background in CSS | `url('/{theme_module_name}/static/content/img/hero-bg.jpg')` |

- Prefer **Font Awesome** (`fa fa-*`) for standard UI icons when no custom icon font is needed.
- Use `loading="lazy"` on below-fold images.

---

## QWeb Quick Reference

| Pattern | Example |
|---------|---------|
| Inherit layout | `<template inherit_id="website.layout">` + `<xpath>` |
| Replace block | `<xpath expr="//header" position="replace">` |
| Insert snippet | Register in `snippets.xml`, drop zone via `oe_structure` |
| Translatable text | `<span t-translation="on">...</span>` |
| Conditional | `t-if`, `t-elif`, `t-else` |
| Loop | `t-foreach` / `t-as` |

---

## Useful Odoo XML IDs

- `website.layout` — main frontend shell
- `website.snippets` — snippet registry
- `website.homepage` — homepage template
- `website.placeholder_header` / footer variants

---

## Responsive CSS Files (naming)

| File | Typical breakpoint |
|------|-------------------|
| `responsive-max-480.css` | Mobile |
| `responsive-max-768.css` | Tablet |
| `responsive-max-1001.css` | Laptop |
| `responsive-min-1201.css` | Large desktop (if needed) |

Match JS carousel/config breakpoints to these values when applicable.
