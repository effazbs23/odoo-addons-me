# -*- coding: utf-8 -*-

from odoo import api, models

from odoo.addons.theme_kingdom.hooks import (
    _cleanup_stale_oe_view_refs,
    _migrate_kingdom_snippet_oe_structure,
    _remove_dynamic_product_tabs_feature as remove_dynamic_product_tabs_feature,
    _strip_baked_editor_branding,
    _strip_saved_snippet_editor_hints,
)

_OPT_IN_MIGRATION_KEY = 'theme_kingdom.header_footer_opt_in_migrated'


class ThemeUtils(models.AbstractModel):
    _inherit = 'theme.utils'

    @property
    def _header_templates(self):
        """Register Kingdom header so enable_view() mutually excludes it with core templates."""
        templates = list(super()._header_templates)
        kingdom_header = 'theme_kingdom.template_header_kingdom'
        if kingdom_header not in templates:
            # Keep the default template last.
            templates.insert(-1, kingdom_header)
        return templates

    @property
    def _footer_templates(self):
        """Register Kingdom footer so enable_view() mutually excludes it with core templates."""
        templates = list(super()._footer_templates)
        kingdom_footer = 'theme_kingdom.template_footer_kingdom'
        if kingdom_footer not in templates:
            # Last in the builder Template gallery / enable mutual exclusion list.
            templates.append(kingdom_footer)
        return templates

    def _disable_legacy_kingdom_header(self):
        """Deactivate the pre-builder always-on header view key if it still exists."""
        View = self.env['ir.ui.view'].sudo().with_context(active_test=False)
        legacy = View.search([('key', '=', 'theme_kingdom.kingdom_header')])
        if legacy:
            legacy.write({'active': False})

    def _set_kingdom_theme_views_inactive(self):
        """Force theme.ir.ui.view records inactive (XML active= is not always rewritten)."""
        ThemeView = self.env['theme.ir.ui.view'].sudo().with_context(active_test=False)
        for key in (
            'theme_kingdom.template_header_kingdom',
            'theme_kingdom.template_footer_kingdom',
        ):
            theme_views = ThemeView.search([('key', '=', key)])
            if theme_views:
                theme_views.write({'active': False})

    def _ensure_kingdom_templates_inactive(self):
        """Deactivate Kingdom header/footer on the current website."""
        self._disable_legacy_kingdom_header()
        self._set_kingdom_theme_views_inactive()
        self.disable_view('theme_kingdom.template_header_kingdom')
        self.disable_view('theme_kingdom.template_footer_kingdom')

    @api.model
    def _migrate_header_footer_opt_in(self):
        """One-time conversion from always-on Kingdom templates to builder opt-in.

        Safe to call repeatedly; gated by an ir.config_parameter flag.
        """
        ICP = self.env['ir.config_parameter'].sudo()
        if ICP.get_param(_OPT_IN_MIGRATION_KEY):
            return True
        self._set_kingdom_theme_views_inactive()
        self._disable_legacy_kingdom_header()
        for website in self.env['website'].search([]):
            utils = self.with_context(website_id=website.id)
            utils.disable_view('theme_kingdom.template_header_kingdom')
            utils.disable_view('theme_kingdom.template_footer_kingdom')
            utils.enable_view('website.template_header_default')
            utils.enable_view('website.footer_custom')
        ICP.set_param(_OPT_IN_MIGRATION_KEY, '1')
        return True

    @api.model
    def _strip_baked_editor_branding(self):
        """Expose hooks._strip_baked_editor_branding for XML <function> upgrades."""
        _strip_baked_editor_branding(self.env)
        return True

    def _post_copy(self, mod):
        res = super()._post_copy(mod)
        _cleanup_stale_oe_view_refs(self.env)
        return res

    def _enable_kingdom_chrome(self):
        """Activate Kingdom header + footer on the website in context."""
        self._disable_legacy_kingdom_header()
        self.enable_view('theme_kingdom.template_header_kingdom')
        self.enable_view('theme_kingdom.template_footer_kingdom')

    def _theme_kingdom_post_copy(self, mod):
        # When Theme Kingdom is applied to a website, enable Kingdom chrome
        # (Style → Header/Footer gallery still allows switching templates).
        self._enable_kingdom_chrome()
        self._ensure_kingdom_shop_layout()
        _migrate_kingdom_snippet_oe_structure(self.env)
        _strip_saved_snippet_editor_hints(self.env)
        _strip_baked_editor_branding(self.env)
        remove_dynamic_product_tabs_feature(self.env)
        _cleanup_stale_oe_view_refs(self.env)
        return True

    @api.model
    def _sync_kingdom_chrome_on_themed_websites(self):
        """One-time: enable Kingdom header/footer on every website using this theme."""
        ICP = self.env['ir.config_parameter'].sudo()
        flag = 'theme_kingdom.sync_chrome_on_themed_websites_v1'
        if ICP.get_param(flag):
            return True
        theme = self.env['ir.module.module'].search([
            ('name', '=', 'theme_kingdom'),
            ('state', '=', 'installed'),
        ], limit=1)
        if theme:
            for website in self.env['website'].search([('theme_id', '=', theme.id)]):
                self.with_context(website_id=website.id)._enable_kingdom_chrome()
        ICP.set_param(flag, '1')
        return True

    @api.model
    def _remove_dynamic_product_tabs_feature(self):
        """Expose hooks cleanup for XML &lt;function&gt; upgrades."""
        remove_dynamic_product_tabs_feature(self.env)
        return True

    @api.model
    def _ensure_kingdom_shop_layout(self):
        """Enable top category chips + left category sidebar on every website."""
        for website in self.env['website'].search([]):
            utils = self.with_context(website_id=website.id)
            utils.enable_view('website_sale.products_categories_top')
            utils.enable_view('website_sale.products_categories')
            # Prefer Kingdom chip styling over stock filmstrip variants.
            utils.disable_view('website_sale.filmstrip_categories_pills')
            utils.disable_view('website_sale.filmstrip_categories_images')
            utils.disable_view('website_sale.filmstrip_categories_tabs')
            utils.disable_view('website_sale.filmstrip_categories_bordered')
            utils.disable_view('website_sale.filmstrip_categories_grid')
            utils.disable_view('website_sale.filmstrip_categories_large_images')
        return True

    @api.model
    def _ensure_header_respects_no_header(self):
        """Website theme copies often skip XML updates — keep no_header support."""
        View = self.env['ir.ui.view'].sudo().with_context(active_test=False)
        views = View.search([('key', '=', 'theme_kingdom.template_header_kingdom')])
        for view in views:
            arch = view.arch_db or ''
            if 'not no_header' in arch:
                continue
            needle = '<xpath expr="//header" position="replace">'
            if needle not in arch:
                continue
            patched = arch.replace(
                needle,
                needle + '\n            <t t-if="not no_header">',
                1,
            )
            # Close the wrapper before </xpath>
            close = '</header>\n        </xpath>'
            if close in patched:
                patched = patched.replace(
                    close,
                    '</header>\n            </t>\n        </xpath>',
                    1,
                )
            elif '</header>\n        </xpath>' not in patched:
                patched = patched.replace(
                    '</header>',
                    '</header>\n            </t>',
                    1,
                )
            if 'not no_header' in patched and patched != arch:
                view.with_context(no_save_prev=True).write({'arch_db': patched})
        return True

    @api.model
    def _fix_header_category_roots_arch(self):
        """Replace stale kingdom_get_header_roots() in website theme copies.

        Theme XML updates do not always rewrite per-website ir.ui.view arch, which
        leaves AttributeError on product.public.category when the method is missing
        from an old registry / copy.
        """
        import re

        new = (
            "request.env['product.public.category'].sudo()"
            ".search([('parent_id', '=', False)], order='sequence, name, id')"
        )
        # Match any kwargs / sudo() variants of the old helper call.
        pattern = re.compile(
            r"request\.env\['product\.public\.category'\]"
            r"(?:\.sudo\(\))?"
            r"\.kingdom_get_header_roots\([^)]*\)"
        )

        def _patch_arch(arch):
            if not isinstance(arch, str) or 'kingdom_get_header_roots' not in arch:
                return arch
            return pattern.sub(new, arch)

        View = self.env['ir.ui.view'].sudo().with_context(active_test=False)
        for view in View.search([('arch_db', 'like', 'kingdom_get_header_roots')]):
            patched = _patch_arch(view.arch_db or '')
            if patched != (view.arch_db or ''):
                view.with_context(no_save_prev=True).write({'arch_db': patched})

        if 'theme.ir.ui.view' in self.env:
            ThemeView = self.env['theme.ir.ui.view'].sudo().with_context(active_test=False)
            for view in ThemeView.search([('arch', 'like', 'kingdom_get_header_roots')]):
                patched = _patch_arch(view.arch or '')
                if patched != (view.arch or ''):
                    view.write({'arch': patched})

        # Prefer fresh XML from disk for website copies after patching theme templates.
        Mod = self.env['ir.module.module'].sudo().search([('name', '=', 'theme_kingdom')], limit=1)
        if Mod and Mod.state == 'installed':
            for website in self.env['website'].search([]):
                Mod._theme_load(website)
            # Patch again in case any leftover website copy still has the call.
            for view in View.search([('arch_db', 'like', 'kingdom_get_header_roots')]):
                patched = _patch_arch(view.arch_db or '')
                if patched != (view.arch_db or ''):
                    view.with_context(no_save_prev=True).write({'arch_db': patched})
        self.env.registry.clear_cache('templates')
        return True

    @api.model
    def _fix_legacy_brands_snippet_key(self):
        """Ensure theme_kingdom.s_manufacturers exists and update saved page arches.

        After renaming the Brands snippet to s_brands, website pages that still
        reference theme_kingdom.s_manufacturers (data-snippet / t-call / live
        render) raised Missing Record. Keep a legacy template and rewrite arches.

        Also fix arch_fs that still points at the deleted s_manufacturers.xml
        path (breaks ``--dev=xml`` live reload → 404 on snippet/render).
        """
        View = self.env['ir.ui.view'].sudo().with_context(active_test=False)
        old_fs = 'theme_kingdom/views/snippets/s_manufacturers.xml'
        new_fs = 'theme_kingdom/views/snippets/s_brands.xml'

        # Fix stale arch_fs after file rename (critical with --dev=xml).
        for view in View.search([('arch_fs', '=', old_fs)]):
            view.write({'arch_fs': new_fs})
        if 'theme.ir.ui.view' in self.env:
            ThemeView = self.env['theme.ir.ui.view'].sudo()
            for view in ThemeView.search([('arch_fs', '=', old_fs)]):
                view.write({'arch_fs': new_fs})

        # Ensure the legacy key resolves (XML may not have been reloaded yet).
        legacy = self.env.ref('theme_kingdom.s_manufacturers', raise_if_not_found=False)
        modern = self.env.ref('theme_kingdom.s_brands', raise_if_not_found=False)
        if modern and not legacy:
            View.create({
                'name': 'Kingdom Brands (legacy)',
                'type': 'qweb',
                'key': 'theme_kingdom.s_manufacturers',
                'arch': '<t t-name="theme_kingdom.s_manufacturers"><t t-call="theme_kingdom.s_brands"/></t>',
            })

        replacements = (
            ('theme_kingdom.s_manufacturers', 'theme_kingdom.s_brands'),
            ('data-kingdom-live-snippet="s_manufacturers"', 'data-kingdom-live-snippet="s_brands"'),
            ('home-manufacturers-section', 'home-brands-section'),
            ('s_manufacturers ', 's_brands '),
            ('class="s_manufacturers"', 'class="s_brands"'),
        )
        views = View.search([
            '|', '|',
            ('arch_db', 'ilike', 's_manufacturers'),
            ('arch_db', 'ilike', 'home-manufacturers-section'),
            ('key', '=', 'theme_kingdom.s_manufacturers'),
        ])
        for view in views:
            arch = view.arch_db or ''
            if not isinstance(arch, str):
                continue
            # Do not rewrite the legacy alias template itself into a self-call.
            if view.key == 'theme_kingdom.s_manufacturers' and 't-call="theme_kingdom.s_brands"' in arch:
                continue
            patched = arch
            for old, new in replacements:
                patched = patched.replace(old, new)
            if patched != arch:
                view.with_context(no_save_prev=True).write({'arch_db': patched})

        self._refresh_baked_brands_snippets()
        self.env.registry.clear_cache('templates')
        return True

    @api.model
    def _refresh_baked_brands_snippets(self):
        """Replace stale Brands sections in saved pages with current brand markup.

        Website Builder bakes brand IDs into homepage arch. After manufacturer→brand
        migration (or deleted brands), those IDs serve transparent placeholders and
        the carousel looks empty. Rewrite arches from live brand records (no HTTP
        request needed).
        """
        import re
        from markupsafe import escape

        View = self.env['ir.ui.view'].sudo().with_context(active_test=False)
        Brand = self.env['kingdom.brand'].sudo()
        slides = Brand.get_website_brand_slides(per_slide=2)
        slide_html = []
        if slides:
            for slide_brands in slides:
                items = []
                for brand in slide_brands:
                    href = escape(brand.get_shop_url())
                    name = escape(brand.name or '')
                    if brand.image:
                        picture = (
                            f'<img loading="lazy" '
                            f'src="/web/image/kingdom.brand/{brand.id}/image" '
                            f'alt="{name}"/>'
                        )
                    else:
                        picture = f'<span class="brand-picture-fallback">{name}</span>'
                    items.append(
                        '<div class="brand-item">'
                        f'<a class="brand-picture" href="{href}" title="{name}">'
                        f'{picture}</a>'
                        f'<div class="brand-name"><a href="{href}">{name}</a></div>'
                        '</div>'
                    )
                slide_html.append(
                    '<div class="swiper-slide col-4 col-sm-3 col-lg-2 col-xl-1_5">'
                    + ''.join(items)
                    + '</div>'
                )
            slides_body = ''.join(slide_html)
        else:
            # Keep an empty wrapper; live-snippet / demo fallback fills on next render
            # if the snippet template is used. For baked pages, leave a clear shell.
            slides_body = ''

        fresh_section = (
            '<section class="s_brands home-brands-section carousel-grid" '
            'data-snippet="theme_kingdom.s_brands" '
            'data-kingdom-live-snippet="s_brands" '
            'data-name="Brands" aria-labelledby="BrandsHeading">'
            '<div class="k-container container">'
            '<div class="home-brands-head title">'
            '<h2 id="BrandsHeading" class="o_translate_inline"><strong>Brands</strong></h2>'
            '</div>'
            '<div class="carousel-container swiperCarousel carousel-brand">'
            '<div class="swiper-button-prev brand-carousel-arrow" aria-label="Previous brands"/>'
            '<div class="swiper-button-next brand-carousel-arrow" aria-label="Next brands"/>'
            '<div class="swiper brand brand-swiper">'
            f'<div class="swiper-wrapper">{slides_body}</div>'
            '</div></div></div></section>'
        )

        pattern = re.compile(
            r'<section\b[^>]*\b(?:s_brands|s_manufacturers|home-brands-section|home-manufacturers-section)\b[^>]*>.*?</section>',
            re.IGNORECASE | re.DOTALL,
        )
        views = View.search([
            '|', '|', '|',
            ('arch_db', 'ilike', 'home-brands-section'),
            ('arch_db', 'ilike', 'home-manufacturers-section'),
            ('arch_db', 'ilike', 'data-snippet="theme_kingdom.s_brands"'),
            ('arch_db', 'ilike', 'data-snippet="theme_kingdom.s_manufacturers"'),
        ])
        for view in views:
            if view.key in (
                'theme_kingdom.s_brands',
                'theme_kingdom.s_manufacturers',
            ):
                continue
            arch = view.arch_db or ''
            if not isinstance(arch, str) or not pattern.search(arch):
                continue
            patched = pattern.sub(fresh_section, arch)
            if patched != arch:
                view.with_context(no_save_prev=True).write({'arch_db': patched})
        return True
