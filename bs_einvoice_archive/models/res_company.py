from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Lets a company opt out of auto-archiving every posted invoice/refund.
    # action_post() renders a PDF snapshot synchronously when none exists
    # yet (see account_move.py), which is real per-invoice cost on top of
    # normal posting -- some companies installing this module for one
    # subsidiary shouldn't have to pay it everywhere.
    einvoice_archive_enabled = fields.Boolean(default=True)
