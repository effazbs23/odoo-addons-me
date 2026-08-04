# Skill: Odoo Website Theme Master

---

## Module Scaffold

### `__manifest__.py` essentials (`static/content/`)

```python
{
    'name': 'My Website Theme',
    'category': 'Theme/Website',
    'version': '1.0.0',
    'depends': ['website'],
    'data': [
        'views/website_templates.xml',
        'views/snippets.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '{theme_module_name}/static/content/css/variables.css',
            '{theme_module_name}/static/content/css/styles.css',
            '{theme_module_name}/static/content/css/components.css',
            '{theme_module_name}/static/content/css/responsive-max-768.css',
            '{theme_module_name}/static/content/css/responsive-max-480.css',
            '{theme_module_name}/static/content/js/theme.js',
        ],
    },
    'license': 'LGPL-3',
}
```

* Replace `{theme_module_name}` with the technical module folder name.
* Add `website_sale` to `depends` only when styling shop templates.

### Theme Kingdom — JS in `views/assets.xml`, CSS in manifest

| Asset | Location |
|-------|----------|
| CSS | `__manifest__.py` → `assets` → `web.assets_frontend` |
| JS | `views/assets.xml` → inherit `website.layout`, `<script src="...">` before `</body>` |

* Do **not** add theme JS in `__manifest__.py` `assets`.
* Do **not** use `<asset>` for plain IIFE / vendor JS (use layout `<script>` tags in `assets.xml`).
* Do **not** add theme CSS in `views/assets.xml`.
* New JS → one `<script>` in `kingdom_js_assets` template (order: libraries → `main.js`).
* `data` must include `'views/assets.xml'` in `__manifest__.py`.
* After code/XML/asset changes, upgrade with `-u theme_kingdom` — **do not** increment `__manifest__.py` `version` each time (only for a deliberate release).

---

## Folder Rules

| Folder | Purpose |
|--------|---------|
| `static/content/css/` | All stylesheets |
| `static/content/font/` | Web fonts + `icon-font/` |
| `static/content/img/` | Images, logos, snippet thumbs |
| `static/content/js/` | Public frontend scripts |
| `views/` | QWeb XML only |

**Never** place theme CSS/fonts/images in `static/src/` or module root `content/` (without `static/`) — Odoo only serves files under `static/`.

---

## QWeb Inheritance

### Rules

1. **Always inherit** — `<template inherit_id="...">` + `<xpath>`.
2. **Minimal diff** — Change only required nodes.
3. **Asset links** — Do not add `<link>` tags for theme CSS in QWeb; use manifest `assets` instead.

### Example: header class

```xml
<template id="layout_header_class" inherit_id="website.layout" name="Theme Header Class">
    <xpath expr="//header" position="attributes">
        <attribute name="class" add="o_theme_header" separator=" "/>
    </xpath>
</template>
```

### Example: image from content folder

```xml
<img src="/my_theme/static/content/img/logo.png" alt="Logo" class="o_theme_logo"/>
```

---

## Custom Snippets

1. QWeb in `views/snippets.xml`.
2. Register via inherit on `website.snippets`.
3. Thumbnail: `static/content/img/snippets/my_snippet.png`.
4. Editable zones: `<div class="oe_structure"/>`.

* Class prefix: `o_theme_` or `s_theme_` to avoid core collisions.

---

## Homepage & Pages

* Inherit `website.homepage` or add `website.page` in `data/`.
* Blog/shop styling: separate XML inherits + optional `content/css/pages/*.css` listed in manifest.

---

## Install / Upgrade

```bash
./odoo-bin -c odoo.conf -u {theme_module_name} -d {database} --stop-after-init
```

* Upgrade after manifest, XML, or any `static/content/` file change.
* Use `?debug=assets` while editing CSS.

---

## UI Verification (QA)

- [ ] Tokens applied from `variables.css`
- [ ] Responsive files only contain `@media` rules
- [ ] Fonts load (Network tab — no 404 under `/static/content/font/`)
- [ ] Images resolve under `/static/content/img/`
- [ ] No console JS errors
- [ ] Public + Website Editor both checked

---

## Do Not

* Copy full `website.layout` without `inherit_id`.
* Patch core/enterprise addons in-place.
* Put `@media` in `styles.css`.
* Hardcode database IDs in XML.
