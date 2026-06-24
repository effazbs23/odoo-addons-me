# -*- coding: utf-8 -*-

from odoo import models


class ThemeUtils(models.AbstractModel):
    _inherit = 'theme.utils'

    def _activate_kingdom_footer(self):
        """Enable the Kingdom footer and disable default Odoo footer templates."""
        for xml_id in self._footer_templates:
            self.disable_view(xml_id)
        self.enable_view('theme_kingdom.template_footer_kingdom')

    @property
    def _footer_templates(self):
        templates = list(super()._footer_templates)
        kingdom_footer = 'theme_kingdom.template_footer_kingdom'
        if kingdom_footer not in templates:
            templates.append(kingdom_footer)
        return templates

    def _theme_kingdom_post_copy(self, mod):
        self._activate_kingdom_footer()
        return True
