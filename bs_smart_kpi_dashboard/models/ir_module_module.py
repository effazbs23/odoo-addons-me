# -*- coding: utf-8 -*-
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class IrModuleModule(models.Model):
    """Fires vocabulary auto-discovery right after an admin installs,
    upgrades, or uninstalls a module from Apps — the "when a module is
    added" trigger for ai.dashboard.allowlist._discover_new_models().

    This only covers the Apps UI's immediate-action buttons (the common
    case); modules installed via `-i`/`-u` on the command line don't go
    through here at all, which is what the daily ir.cron
    (data/ir_cron_data.xml) exists to catch instead.
    """
    _inherit = 'ir.module.module'

    def _button_immediate_function(self, function):
        result = super()._button_immediate_function(function)
        try:
            self.env['ai.dashboard.allowlist'].sudo()._discover_new_models()
            self.env.cr.commit()
        except Exception:
            # Never let vocabulary discovery break a module operation that
            # has already succeeded — log and move on.
            _logger.exception(
                "Smart KPI Dashboard: vocabulary auto-discovery failed "
                "after a module operation.")
        return result
