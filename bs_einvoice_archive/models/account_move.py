import base64
import hashlib
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)

# Odoo core has no field distinguishing simplified/self-billed/capital-asset/
# real-estate invoices from a plain standard one -- only credit-note
# direction is derivable from move_type. Everything else defaults to
# 'standard' and must be reclassified by whoever knows the invoice's real
# category; there's nowhere else in core to read it from.
# ponytail: heuristic mapping, revisit if an e-invoicing connector module
# later exposes a proper classification field to read instead.
_EINVOICE_TYPE_BY_MOVE_TYPE = {
    'out_refund': 'credit_note',
    'in_refund': 'credit_note',
}

_ARCHIVABLE_MOVE_TYPES = ('out_invoice', 'out_refund', 'in_invoice', 'in_refund')


class AccountMove(models.Model):
    _inherit = 'account.move'

    einvoice_archive_ids = fields.One2many('bs.einvoice.archive', 'move_id', string='E-Invoice Archives')

    def action_post(self):
        result = super().action_post()
        self._create_einvoice_archive()
        return result

    def _create_einvoice_archive(self):
        Archive = self.env['bs.einvoice.archive'].sudo()
        Policy = self.env['bs.einvoice.retention.policy'].sudo()
        for move in self:
            if move.move_type not in _ARCHIVABLE_MOVE_TYPES:
                continue
            if not move.company_id.einvoice_archive_enabled:
                continue
            if Archive.search_count([('move_id', '=', move.id)]):
                continue  # already archived (e.g. re-entering action_post is a no-op here)

            invoice_type = _EINVOICE_TYPE_BY_MOVE_TYPE.get(move.move_type, 'standard')
            policy = Policy.search([
                ('invoice_type', '=', invoice_type), ('company_id', '=', move.company_id.id),
            ], limit=1) or Policy.search([
                ('invoice_type', '=', invoice_type), ('company_id', '=', False),
            ], limit=1)

            original_archive = self.env['bs.einvoice.archive']
            if invoice_type == 'credit_note' and move.reversed_entry_id:
                original_archive = Archive.search([('move_id', '=', move.reversed_entry_id.id)], limit=1)

            xml_attachment, pdf_attachment = move._einvoice_snapshot_attachments()

            Archive.create({
                'move_id': move.id,
                'move_name': move.name,
                'partner_id': move.partner_id.id,
                'partner_trn': getattr(move.partner_id, 'vat', False) or '',
                'company_id': move.company_id.id,
                'invoice_type': invoice_type,
                'original_archive_id': original_archive.id or False,
                'xml_attachment_id': xml_attachment.id if xml_attachment else False,
                'pdf_attachment_id': pdf_attachment.id if pdf_attachment else False,
                # No ASP connector is assumed to be installed (see non-goals);
                # a connector module can populate this field itself once one is.
                'asp_status': 'not_applicable',
                'retention_years': policy.retention_years if policy else 0,
                'checksum': move._einvoice_checksum(xml_attachment, pdf_attachment),
            })
        return True

    def _einvoice_snapshot_attachments(self):
        """Locate (or generate) the XML/PDF for this invoice, as attachments
        owned by account.move -- never by bs.einvoice.archive itself. See
        architecture doc 2.5: this is what keeps the files alive if this
        module is later uninstalled.
        """
        self.ensure_one()
        existing = self.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'account.move'), ('res_id', '=', self.id),
        ])
        xml_attachment = existing.filtered(
            lambda a: a.mimetype == 'application/xml' or a.name.lower().endswith('.xml'))[:1]
        pdf_attachment = existing.filtered(
            lambda a: a.mimetype == 'application/pdf' or a.name.lower().endswith('.pdf'))[:1]
        if not pdf_attachment:
            pdf_attachment = self._einvoice_generate_pdf_attachment()
        return xml_attachment, pdf_attachment

    def _einvoice_generate_pdf_attachment(self):
        self.ensure_one()
        report = self.env.ref('account.account_invoices', raise_if_not_found=False)
        if not report:
            return self.env['ir.attachment']
        try:
            pdf_content, _ftype = self.env['ir.actions.report'].sudo()._render_qweb_pdf(report, self.ids)
        except Exception:
            _logger.exception("bs_einvoice_archive: failed to render invoice PDF for %s", self.name)
            return self.env['ir.attachment']
        return self.env['ir.attachment'].sudo().create({
            'name': f'{self.name}.pdf',
            'res_model': 'account.move',
            'res_id': self.id,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'mimetype': 'application/pdf',
        })

    def _einvoice_checksum(self, xml_attachment, pdf_attachment):
        hasher = hashlib.sha256()
        for attachment in (xml_attachment, pdf_attachment):
            if attachment:
                hasher.update(base64.b64decode(attachment.datas or b''))
        return hasher.hexdigest()
