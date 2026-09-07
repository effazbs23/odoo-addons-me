# Part of bs_typo_tolerant_product_search. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class SearchFuzzyLog(models.Model):
    """Search Term Miss Log (spec section 6).

    One row per storefront search where the fuzzy fallback actually fired, so
    the store owner can see near-miss search terms over time (spec 5, 8.5).
    """
    _name = 'bs.search.fuzzy.log'
    _description = 'Search Fuzzy Fallback Log'
    _order = 'create_date desc'
    _rec_name = 'search_term'

    search_term = fields.Char(string='Searched Term', required=True, readonly=True)
    corrected_term = fields.Char(string='Corrected Term', readonly=True)
    result_count = fields.Integer(string='Result Count', readonly=True)
    clicked = fields.Boolean(string='Clicked Through', default=False, readonly=True)
