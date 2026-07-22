# -*- coding: utf-8 -*-
from lxml import html

from odoo import models
from odoo.addons.base.models.ir_ui_view import MOVABLE_BRANDING


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    def save(self, value, xpath=None):
        """Strip baked ir.ui.view branding from saved HTML before writing arches.

        Live/editor HTML may contain ``data-oe-model="ir.ui.view"`` on snippet
        descendants. If those attrs are persisted inside ``#wrap``, Odoo moves
        branding off ``#wrap`` on the next render and Website Builder disables
        all Blocks.
        """
        if xpath is not None and value:
            try:
                arch_section = html.fromstring(
                    value, parser=html.HTMLParser(encoding='utf-8')
                )
            except Exception:
                return super().save(value, xpath=xpath)
            changed = False
            for el in arch_section.iter():
                if el.get('data-oe-model') != 'ir.ui.view':
                    continue
                # Keep root branding for save routing; replace_arch_section
                # ignores root data-oe-* anyway.
                if el is arch_section:
                    continue
                for attr in MOVABLE_BRANDING:
                    if attr in el.attrib:
                        del el.attrib[attr]
                        changed = True
            if changed:
                value = html.tostring(arch_section, encoding='unicode', method='html')
        return super().save(value, xpath=xpath)
