# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    settlement_id = fields.Many2one(
        'petty.cash.settlement',
        string='Settlement',
        help='Related Petty Cash Settlement',
        readonly=True,
        copy=False
    )

