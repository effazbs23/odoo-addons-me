# -*- coding: utf-8 -*-

from odoo import api, models

from odoo.addons.theme_kingdom.hooks import (
    _cleanup_stale_oe_view_refs,
    _migrate_kingdom_snippet_oe_structure,
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
            # Keep the default template last.
            templates.insert(-1, kingdom_footer)
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

    def _post_copy(self, mod):
        res = super()._post_copy(mod)
        _cleanup_stale_oe_view_refs(self.env)
        return res

    def _theme_kingdom_post_copy(self, mod):
        # Kingdom header/footer are opt-in via Website Builder — do not auto-enable.
        self._ensure_kingdom_templates_inactive()
        self.enable_view('website.template_header_default')
        self.enable_view('website.footer_custom')
        _migrate_kingdom_snippet_oe_structure(self.env)
        _strip_saved_snippet_editor_hints(self.env)
        _cleanup_stale_oe_view_refs(self.env)
        return True
