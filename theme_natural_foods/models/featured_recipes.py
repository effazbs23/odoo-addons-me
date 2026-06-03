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

class FeaturedRecipes(models.Model):
    _name = "featured.recipes"
    _description = "Featured Recipes"

    name = fields.Char(string="Recipe Name", required=True)
    subtitle = fields.Text(string="Recipe Subtitle")
    image = fields.Image(string="Recipe Image")
    duration = fields.Char(string="Duration", default="15 min")
    category = fields.Selection([
        ('vegan','Vegan'),
        ('vegetarian','Vegetarian'),
        ('nonveg','Non-Veg')
    ], string="Category", default='vegan')