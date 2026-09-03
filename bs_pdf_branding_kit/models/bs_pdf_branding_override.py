from odoo import api, fields, models

REPORT_TYPES = [
    ('quotation', 'Quotation / Sales Order'),
    ('invoice', 'Customer Invoice'),
    ('delivery_slip', 'Delivery Slip'),
    ('purchase_order', 'Purchase Order'),
]

# payment_state values that mean an invoice is no longer "overdue" even if past due date
_NOT_OVERDUE_PAYMENT_STATES = ('paid', 'in_payment', 'reversed')


class BsPdfBrandingOverride(models.Model):
    _name = 'bs.pdf.branding.override'
    _description = 'PDF Branding Per-Document-Type Override'
    _rec_name = 'report_type'

    company_id = fields.Many2one(
        'res.company', string='Company', required=True, default=lambda self: self.env.company,
    )
    report_type = fields.Selection(REPORT_TYPES, string='Report Type', required=True)
    watermark_override_type = fields.Selection(
        [('inherit', 'Inherit Company Default'), ('none', 'None'), ('text', 'Text'), ('image', 'Image')],
        string='Watermark Override', default='inherit', required=True,
    )
    watermark_override_text = fields.Char(string='Override Text')
    # Not in the original spec table: watermark_override_type offers 'image' as a
    # choice, so a field to hold that image is required for the choice to do anything.
    watermark_override_image = fields.Binary(string='Override Image')
    watermark_override_condition = fields.Selection(
        [('always', 'Always'), ('when_overdue', 'Only When Overdue')],
        string='Apply', default='always', required=True,
        help='"Only When Overdue" is only meaningful for Customer Invoice.',
    )

    _company_report_type_uniq = models.Constraint(
        'unique(company_id, report_type)',
        'Only one branding override per report type per company is allowed.',
    )

    @api.model
    def _get_effective_watermark(self, company, report_type, record=None):
        """Resolve effective watermark settings for one report render.

        Order: explicit override for (company, report_type) if not 'inherit'
        (and, for the when_overdue condition, only if the condition currently
        holds) -> else company-level default -> else none.

        Returns a dict: {'type': 'none'|'text'|'image', 'text': str|False, 'image': bin|False}.
        """
        override = self.search([
            ('company_id', '=', company.id), ('report_type', '=', report_type),
        ], limit=1)

        if override and override.watermark_override_type != 'inherit':
            applies = True
            if override.watermark_override_condition == 'when_overdue':
                applies = self._is_invoice_overdue(record)
            if applies:
                return {
                    'type': override.watermark_override_type,
                    'text': override.watermark_override_text,
                    'image': override.watermark_override_image,
                }

        return {
            'type': company.pdf_watermark_type,
            'text': company.pdf_watermark_text,
            'image': company.pdf_watermark_image,
        }

    @api.model
    def _is_invoice_overdue(self, record):
        if not record or record._name != 'account.move':
            return False
        if not record.invoice_date_due:
            return False
        if record.payment_state in _NOT_OVERDUE_PAYMENT_STATES:
            return False
        return record.invoice_date_due < fields.Date.context_today(record)
