# -*- coding: utf-8 -*-
#############################################################################
#
#    erp23
#
#    Copyright (C) 2026-TODAY erp23(<https://www.erp-23.com/>)
#    Author: erp23(<https://www.erp-23.com/>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    product_count = fields.Integer(
        string='Product Count',
        compute='_compute_product_count',
        store=False,
    )

    #  No @api.depends — avoids the crash entirely
    def _compute_product_count(self):
        for category in self:
            try:
                category.product_count = self.env['product.template'].sudo().search_count([
                    ('categ_id', '=', category.id),
                    ('is_published', '=', True),
                    ('sale_ok', '=', True),
                ])
            except Exception:
                category.product_count = 0