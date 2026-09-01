from odoo import api, fields, models

from .bs_notify_utils import is_valid_e164


class ResPartner(models.Model):
    _inherit = 'res.partner'

    has_valid_notify_number = fields.Boolean(
        string="Has Valid Notification Number", compute='_compute_has_valid_notify_number',
    )

    @api.depends('phone')
    def _compute_has_valid_notify_number(self):
        for partner in self:
            partner.has_valid_notify_number = is_valid_e164(partner.phone)
