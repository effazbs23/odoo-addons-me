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
from odoo import models, fields

class FeaturedProducts(models.Model):
    _name = "featured.products"
    _description = "Featured Products"

    name = fields.Char(required=True, string="Name", help='Name of the category.')
    product_tmpl_ids = fields.Many2many(
        'product.template',
        string="Featured Products",
        domain="[('sale_ok', '=', True), ('is_published', '=', True)]",
        help="Choose featured products"
    )