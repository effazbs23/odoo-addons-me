# -*- coding: utf-8 -*-
from odoo import models


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _get_field_value_safe(self, field_name):
        """Safely get a field value that may not exist if an optional module is not installed."""
        try:
            return self[field_name]
        except (KeyError, AttributeError):
            return False

