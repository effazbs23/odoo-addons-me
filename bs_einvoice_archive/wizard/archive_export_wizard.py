import base64
import csv
import io
import json
import zipfile
from datetime import timedelta

from odoo import _, fields, models
from odoo.exceptions import UserError

from ..models.bs_einvoice_archive import EXPORT_ATTACHMENT_NAME

# Only the manifest's column labels change with language -- the archived
# documents themselves are never translated (see architecture doc 2.4).
_MANIFEST_LABELS = {
    'en': {
        'invoice_number': 'Invoice Number', 'trn': 'TRN', 'archived_on': 'Archived On',
        'retention_expiry_date': 'Retention Expiry', 'checksum': 'Checksum', 'asp_status': 'ASP Status',
    },
    'ar': {
        'invoice_number': 'رقم الفاتورة', 'trn': 'الرقم الضريبي', 'archived_on': 'تاريخ الأرشفة',
        'retention_expiry_date': 'تاريخ انتهاء الاحتفاظ', 'checksum': 'بصمة التحقق', 'asp_status': 'حالة مزود الخدمة',
    },
}

# A blank-filter export (no date/partner/TRN, not launched from a list
# selection) would otherwise match every archive in the database and hold
# every PDF/XML in memory at once while zipping. Cap it and tell the user to
# narrow the filter instead of silently ballooning memory on a large DB.
MAX_EXPORT_ARCHIVES = 2000


class BsEinvoiceArchiveExportWizard(models.TransientModel):
    _name = 'bs.einvoice.archive.export.wizard'
    _description = 'E-Invoice Archive Export Wizard'

    date_from = fields.Date()
    date_to = fields.Date()
    partner_ids = fields.Many2many('res.partner', string='Partners')
    trn = fields.Char(string='TRN')
    language = fields.Selection([('en', 'English'), ('ar', 'Arabic')], default='en', required=True)

    def _matching_archives(self):
        if self.env.context.get('active_model') == 'bs.einvoice.archive' and self.env.context.get('active_ids'):
            # Launched from a multi-select "Export for Audit" on the archive
            # list: the selection itself is the filter, date/partner/trn are
            # ignored.
            return self.env['bs.einvoice.archive'].browse(self.env.context['active_ids'])
        domain = []
        if self.date_from:
            domain.append(('archived_on', '>=', fields.Datetime.to_string(self.date_from)))
        if self.date_to:
            domain.append(('archived_on', '<', fields.Datetime.to_string(self.date_to + timedelta(days=1))))
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        if self.trn:
            domain.append(('partner_trn', '=ilike', self.trn))
        # Active archives are always active_test-scoped by default; disposed
        # records are still legitimately exportable as historical evidence.
        archives = self.env['bs.einvoice.archive'].search(domain, limit=MAX_EXPORT_ARCHIVES + 1)
        if len(archives) > MAX_EXPORT_ARCHIVES:
            raise UserError(_(
                "This filter matches more than %s archives. Narrow the date range, partner, "
                "or TRN filter before exporting."
            ) % MAX_EXPORT_ARCHIVES)
        return archives

    def action_export(self):
        self.ensure_one()
        archives = self._matching_archives()
        if not archives:
            raise UserError(_("No archive records match this filter."))

        labels = _MANIFEST_LABELS[self.language]
        manifest = []
        audit_rows = [('archive', 'user', 'action', 'timestamp', 'note')]

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for archive in archives:
                manifest.append({
                    labels['invoice_number']: archive.move_name,
                    labels['trn']: archive.partner_trn,
                    labels['archived_on']: fields.Datetime.to_string(archive.archived_on),
                    labels['retention_expiry_date']: fields.Date.to_string(archive.retention_expiry_date),
                    labels['checksum']: archive.checksum,
                    labels['asp_status']: archive.asp_status,
                })
                if archive.xml_attachment_id:
                    zf.writestr(f'{archive.name}/{archive.xml_attachment_id.name}',
                                base64.b64decode(archive.xml_attachment_id.datas or b''))
                if archive.pdf_attachment_id:
                    zf.writestr(f'{archive.name}/{archive.pdf_attachment_id.name}',
                                base64.b64decode(archive.pdf_attachment_id.datas or b''))
                for log in archive.audit_log_ids:
                    audit_rows.append((archive.name, log.user_id.name, log.action,
                                        fields.Datetime.to_string(log.timestamp), log.note or ''))

            zf.writestr('manifest.json', json.dumps(manifest, indent=2, ensure_ascii=False))
            csv_buffer = io.StringIO()
            csv.writer(csv_buffer).writerows(audit_rows)
            zf.writestr('audit_log.csv', csv_buffer.getvalue())

        self.env['bs.einvoice.audit.log'].sudo().create([{
            'archive_id': archive.id,
            'action': 'exported',
            'note': _("Exported by %s") % self.env.user.name,
        } for archive in archives])

        attachment = self.env['ir.attachment'].create({
            'name': EXPORT_ATTACHMENT_NAME,
            'type': 'binary',
            'datas': base64.b64encode(buffer.getvalue()),
            'mimetype': 'application/zip',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
