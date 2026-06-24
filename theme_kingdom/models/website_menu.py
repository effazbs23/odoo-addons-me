# -*- coding: utf-8 -*-

from odoo import fields, models


class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    kingdom_product_tab_id = fields.Many2one(
        'kingdom.product.tab',
        string='Kingdom Product Tab',
        ondelete='cascade',
        copy=False,
        index=True,
    )
