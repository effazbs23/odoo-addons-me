# Theme Kingdom — Odoo Apps Store publishing checklist

Use this list before uploading to [apps.odoo.com](https://apps.odoo.com/apps/upload).

## Required files (in this module)

| File | Purpose |
|------|---------|
| `__manifest__.py` | Name, summary, category `Theme/eCommerce`, version, author, depends, `images` |
| `static/description/icon.png` | Module icon (128×128 PNG) |
| `static/description/index.html` | Apps store landing page (English) |
| `static/description/main_screenshot.png` | Large homepage screenshot (`*_screenshot` in manifest) |
| `static/description/banner.png` | Cover / gallery image |
| `doc/index.rst` | Technical documentation (optional but recommended) |

## Manifest `images` key

```python
'images': [
    'static/description/banner.png',
    'static/description/theme_desktop.png',
    'static/description/main_screenshot.png',
],
```

The file whose name ends with `_screenshot` is shown as the **large preview** on the store.

## Screenshots to prepare (recommended)

1. **Homepage full page** — desktop (1920px), saved as `main_screenshot.png`
2. **Mobile homepage** — phone mockup, save as `theme_mobile.png`
3. **Deal of the Day** — countdown + product carousel close-up
4. **Shop / category page** — product grid with filters
5. **Product detail page** — gallery, price, add to cart
6. **Promo banner** — optional marketing graphic like the nopStation samples

Replace placeholder images in `static/description/` with real Odoo screenshots from your demo site.

## `index.html` rules (Odoo sanitizer)

- English only
- No `<html>`, `<head>`, `<body>` — start with `<section>`
- Use Bootstrap grid (`row`, `col-*`) and hex colors (`#0d6e6e`)
- No JavaScript, no external links (except YouTube / mailto per vendor guidelines)
- Images: PNG, JPEG, or GIF only; reference files in `static/description/`

## Before upload

- [ ] Test install on a clean Odoo 19 database
- [ ] Theme activates from **Website → Themes**
- [ ] All snippets render on homepage
- [ ] `icon.png` is real PNG (not renamed .ico)
- [ ] Version in manifest matches Odoo series (`19.0.x.x`)
- [ ] LGPL-3 or compatible `license` key in manifest
- [ ] No broken image paths in `index.html`
- [ ] Demo data / screenshots use English product names

## Upload steps

1. Register as vendor on apps.odoo.com
2. Push module to a **public Git** repository (GitHub/GitLab)
3. Submit repo URL at **Apps → Upload**
4. Wait for automated validation and manual review

## Marketing assets (optional, outside Odoo)

For your own website or nopStation-style promo banners:

- Responsive mockup (laptop + tablet + phone)
- Feature icons grid (responsive, snippets, wishlist, promotions, etc.)
- Brand lockup: Kingdom logo + “Odoo eCommerce Theme”

These are not required inside the module but help sales pages.
