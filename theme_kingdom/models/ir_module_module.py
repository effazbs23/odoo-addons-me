# -*- coding: utf-8 -*-
from odoo import api, models

from odoo.addons.theme_kingdom.hooks import _cleanup_stale_oe_view_refs


class IrModuleModule(models.Model):
    _inherit = 'ir.module.module'

    @api.model
    def _theme_remove(self, website):
        """Drop stale editor view ids from pages when a theme unloads its views."""
        super()._theme_remove(website)
        _cleanup_stale_oe_view_refs(self.env)

    def button_choose_theme(self):
        result = super().button_choose_theme()
        _cleanup_stale_oe_view_refs(self.env)
        return result
