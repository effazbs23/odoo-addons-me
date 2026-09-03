from odoo import _, api, models
from odoo.exceptions import UserError

_REPORT_ACTIONS = {
    'quotation': 'sale.action_report_saleorder',
    'invoice': 'account.account_invoices',
    'delivery_slip': 'stock.action_report_delivery',
    'purchase_order': 'purchase.action_report_purchase_order',
}

_PREVIEW_ATTACHMENT_NAME = 'bs_pdf_branding_preview.pdf'


class BsPdfBrandingPreviewWizard(models.TransientModel):
    _name = 'bs.pdf.branding.preview.wizard'
    _description = 'PDF Branding Live Preview'

    @api.model
    def _create_dummy_record(self, report_type, company):
        """Create a real, throwaway record to render the preview against.

        Odoo's report pipeline (report_action()'s active_ids, EDI-export hooks
        some installed modules add on report generation, etc.) assumes a real,
        saved record with real field values like create_date -- an in-memory
        .new() record breaks both of those (report_action() can't build a
        download URL for it: recordset.ids is always [] for an unsaved record,
        and some hooks crash on fields .new() never sets). This record is
        deleted again in action_preview() right after rendering, so nothing
        from it survives the request.
        """
        partner = self.env['res.partner'].search([('company_id', 'in', (False, company.id))], limit=1)
        if report_type == 'quotation':
            return self.env['sale.order'].create({
                'name': 'S00000 (Preview)', 'partner_id': partner.id, 'company_id': company.id,
            })
        if report_type == 'invoice':
            return self.env['account.move'].create({
                'move_type': 'out_invoice', 'partner_id': partner.id, 'company_id': company.id,
            })
        if report_type == 'delivery_slip':
            picking_type = self.env['stock.picking.type'].search(
                [('company_id', '=', company.id), ('code', '=', 'outgoing')], limit=1)
            return self.env['stock.picking'].create({
                'name': 'WH/OUT/00000 (Preview)', 'partner_id': partner.id, 'company_id': company.id,
                'picking_type_id': picking_type.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
            })
        if report_type == 'purchase_order':
            return self.env['purchase.order'].create({
                'name': 'P00000 (Preview)', 'partner_id': partner.id, 'company_id': company.id,
            })
        raise UserError(_('Unknown report type: %s', report_type))

    @api.model
    def action_preview(self, report_type, branding, company):
        """Render report_type's native report using `branding` (the settings
        panel's CURRENT, possibly-unsaved values, passed through context so
        the shared overlay template uses it instead of re-reading company_id's
        persisted fields) and return an action that opens the finished PDF.

        A throwaway record is created to render against and deleted again
        immediately after -- no business record (sale order, invoice, delivery,
        purchase order) is left behind. The rendered PDF itself is handed back
        via a short-lived ir.attachment (Odoo's report/download flow needs a
        URL to point at); any previous preview of this user's is replaced
        rather than left to accumulate.
        """
        xmlid = _REPORT_ACTIONS[report_type]
        report = self.env.ref(xmlid)
        record = self._create_dummy_record(report_type, company)
        try:
            content, _report_type = report.with_company(company).with_context(
                bs_pdf_branding_preview=branding,
            )._render_qweb_pdf(xmlid, res_ids=record.ids)
        finally:
            record.unlink()

        self.env['ir.attachment'].search([
            ('name', '=', _PREVIEW_ATTACHMENT_NAME), ('create_uid', '=', self.env.uid),
        ]).unlink()
        attachment = self.env['ir.attachment'].create({
            'name': _PREVIEW_ATTACHMENT_NAME,
            'type': 'binary',
            'raw': content,
            'mimetype': 'application/pdf',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%d?download=false' % attachment.id,
            'target': 'new',
        }
