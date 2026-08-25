from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .bs_einvoice_archive import INVOICE_TYPES


class BsEinvoiceRetentionPolicy(models.Model):
    _name = 'bs.einvoice.retention.policy'
    _description = 'E-Invoice Retention Policy'
    _order = 'invoice_type'

    invoice_type = fields.Selection(INVOICE_TYPES, required=True)
    retention_years = fields.Integer(required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    _type_company_unique = models.Constraint(
        'unique(invoice_type, company_id)',
        'A retention policy for this invoice type and company already exists.',
    )

    @api.constrains('retention_years')
    def _check_retention_years(self):
        for policy in self:
            if policy.retention_years <= 0:
                raise UserError(_(
                    "Retention period must be at least 1 year -- a %s value here would make "
                    "every newly-archived invoice of this type immediately eligible for disposal."
                ) % policy.retention_years)
