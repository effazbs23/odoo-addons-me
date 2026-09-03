from odoo import _, api, models
from odoo.exceptions import UserError

_REPORT_ACTIONS = {
    'quotation': 'sale.action_report_saleorder',
    'invoice': 'account.account_invoices',
    'delivery_slip': 'stock.action_report_delivery',
    'purchase_order': 'purchase.action_report_purchase_order',
}


class BsPdfBrandingPreviewWizard(models.TransientModel):
    _name = 'bs.pdf.branding.preview.wizard'
    _description = 'PDF Branding Live Preview'

    @api.model
    def _dummy_record(self, report_type, company):
        """Build an in-memory-only (never created/saved) dummy record to render."""
        partner = self.env['res.partner'].new({'name': 'Preview Customer', 'company_id': company.id})
        if report_type == 'quotation':
            return self.env['sale.order'].new({
                'name': 'S00000 (Preview)', 'partner_id': partner.id, 'company_id': company.id,
            })
        if report_type == 'invoice':
            return self.env['account.move'].new({
                'move_type': 'out_invoice', 'partner_id': partner.id, 'company_id': company.id,
            })
        if report_type == 'delivery_slip':
            return self.env['stock.picking'].new({
                'name': 'WH/OUT/00000 (Preview)', 'partner_id': partner.id, 'company_id': company.id,
            })
        if report_type == 'purchase_order':
            return self.env['purchase.order'].new({
                'name': 'P00000 (Preview)', 'partner_id': partner.id, 'company_id': company.id,
            })
        raise UserError(_('Unknown report type: %s', report_type))

    @api.model
    def action_preview(self, report_type, branding, company):
        """Render report_type's native report against a dummy in-memory record.

        `branding` is the already-resolved dict of the settings panel's CURRENT
        (possibly unsaved) values, passed through context so the shared overlay
        template uses it instead of re-reading company_id's persisted fields.
        Nothing is created/written: the dummy record is a .new() recordset and
        this method never calls create()/write() on any business model.
        """
        dummy = self._dummy_record(report_type, company)
        report = self.env.ref(_REPORT_ACTIONS[report_type])
        # config=False: a Preview click must always show the rendered PDF, never
        # redirect to the "configure your document layout" onboarding wizard that
        # report_action() shows admins the first time a company has no layout set.
        return report.with_context(bs_pdf_branding_preview=branding).report_action(dummy, config=False)
