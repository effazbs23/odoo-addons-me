from odoo import fields, models

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
