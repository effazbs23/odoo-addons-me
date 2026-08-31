from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    simple_invoicing_mode = fields.Boolean(
        related='company_id.simple_invoicing_mode',
        readonly=False,
        string="Enable Simple Invoice",
    )
