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
from odoo import models, fields, api

class DealsOfDay(models.Model):
    _name = 'natural.deals.of.day'
    _description = 'Deals of the Day'
    _order = 'sequence asc'

    name = fields.Char(string='Deal Name', required=True)
    product_tmpl_ids = fields.Many2many(
        comodel_name='product.template',
        relation='natural_deals_product_rel',
        column1='deal_id',
        column2='product_id',
        string='Products',
        domain="[('sale_ok', '=', True), ('is_published', '=', True)]",
        readonly=False,
    )
    deal_end_time = fields.Datetime(string='Deal End Time')
    is_active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(string='Sequence', default=10)