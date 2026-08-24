# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Off by default so installing/upgrading this module changes nothing
    # about how existing prompts parse — see kpi_prompt_parser.py's
    # `_fuzzy_match_pass` docstring for exactly what this gates.
    kpi_dashboard_fuzzy_match_enabled = fields.Boolean(
        string="Fuzzy-match unmatched phrases",
        config_parameter='bs_smart_kpi_dashboard.fuzzy_match_enabled',
        help="When a prompt's leftover text (after the normal exact-match "
             "pass) still matches no vocabulary phrase, try a conservative "
             "whole-phrase similarity comparison against known synonym "
             "phrases before falling back to the guided form. Never "
             "overrides an exact match. Off by default.")
