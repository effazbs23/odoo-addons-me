# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    petty_cash_holder = fields.Many2one(
        'res.partner',
        string='Petty Cash Holder',
        help='Person responsible for managing this petty cash journal'
    )
    petty_cash_limit = fields.Monetary(
        string='Petty Cash Limit',
        currency_field='currency_id',
        help='Maximum amount allowed in this petty cash journal'
    )
