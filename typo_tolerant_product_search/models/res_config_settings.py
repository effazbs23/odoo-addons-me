# Part of typo_tolerant_product_search. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fuzzy_search_sensitivity = fields.Selection(
        related='website_id.fuzzy_search_sensitivity', readonly=False,
    )
    fuzzy_search_min_results = fields.Integer(
        related='website_id.fuzzy_search_min_results', readonly=False,
    )
