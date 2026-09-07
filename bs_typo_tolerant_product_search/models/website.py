# Part of bs_typo_tolerant_product_search. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    # Spec section 6 - configurable sensitivity / minimum-result threshold.
    fuzzy_search_sensitivity = fields.Selection(
        [('tight', 'Tight'), ('normal', 'Normal'), ('loose', 'Loose')],
        string='Fuzzy Search Sensitivity', default='normal', required=True,
        help="How aggressively the storefront search corrects typos when "
             "results are too few. Tight = fewer, higher-confidence "
             "corrections. Loose = more corrections, higher chance of an "
             "off-target suggestion.",
    )
    fuzzy_search_min_results = fields.Integer(
        string='Minimum Results Before Fuzzy Fallback', default=1, required=True,
        help="Fuzzy fallback only kicks in when the normal exact/substring "
             "search returns fewer than this many products. Default 1 means "
             "the fallback only triggers on true zero-result searches.",
    )
