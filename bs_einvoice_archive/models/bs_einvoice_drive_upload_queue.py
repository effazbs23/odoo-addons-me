import base64
import json
import logging
import uuid
from datetime import timedelta

import requests

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5
UPLOAD_ENDPOINT = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart'
BATCH_SIZE = 20


def _redact(text, *secrets):
    """Strips any known secret value out of a string before it's ever
    logged or persisted -- the whole point being that a token must never
    show up in last_error, ir.logging, or a raised exception message.
    """
    text = str(text)
    for secret in secrets:
        if secret:
            text = text.replace(secret, '***REDACTED***')
    return text


class BsEinvoiceDriveUploadQueue(models.Model):
    _name = 'bs.einvoice.drive.upload.queue'
    _description = 'E-Invoice Google Drive Upload Queue'
    _order = 'scheduled_for'

    archive_id = fields.Many2one('bs.einvoice.archive', required=True, ondelete='cascade', index=True)
    state = fields.Selection([
        ('pending', 'Pending'), ('done', 'Done'), ('failed', 'Failed'),
    ], default='pending', required=True)
    retry_count = fields.Integer(default=0)
    last_error = fields.Text()
    scheduled_for = fields.Datetime(default=fields.Datetime.now, required=True)

    @api.model
    def _cron_process_queue(self):
        jobs = self.search([
            ('state', '=', 'pending'), ('scheduled_for', '<=', fields.Datetime.now()),
        ], limit=BATCH_SIZE)
        for job in jobs:
            job._process()

    def _process(self):
        self.ensure_one()
        self = self.sudo()  # this is internal cron/system bookkeeping, never a user-facing write
        archive = self.archive_id
        config = self.env['bs.einvoice.drive.config'].sudo().search([('company_id', '=', archive.company_id.id)], limit=1)
        if not config or config.status == 'not_connected':
            # Disconnected between queueing and processing -- not a
            # failure, this feature is fully optional. A config in
            # 'error' status is NOT treated as disconnected here: it
            # still has to go through the normal retry/backoff path
            # below, since the error may well be transient.
            archive.sudo().write({'drive_backup_status': 'not_applicable'})
            self.write({'state': 'done'})
            return

        access_token = None
        refresh_token = config._get_refresh_token()
        try:
            try:
                access_token = config._access_token()
            except Exception as auth_exc:
                config.sudo().write({'status': 'error', 'last_error': _redact(auth_exc, refresh_token)})
                raise
            if config.status == 'error':
                config.sudo().write({'status': 'connected', 'last_error': False})
            xml_file_id = self._upload_attachment(config, access_token, archive.xml_attachment_id, archive, 'xml')
            pdf_file_id = self._upload_attachment(config, access_token, archive.pdf_attachment_id, archive, 'pdf')
            archive.sudo().write({
                'drive_xml_file_id': xml_file_id or False,
                'drive_pdf_file_id': pdf_file_id or False,
                'drive_backup_status': 'backed_up',
            })
            self.write({'state': 'done', 'last_error': False})
            self.env['bs.einvoice.audit.log'].sudo().create({
                'archive_id': archive.id, 'action': 'drive_backup_succeeded',
                'note': _("Uploaded to Google Drive"),
            })
        except Exception as exc:  # noqa: BLE001 -- must never let an upload failure escape and break the cron
            error_text = _redact(exc, access_token, refresh_token)
            _logger.warning("bs_einvoice_archive: Drive upload failed for archive %s: %s", archive.name, error_text)
            self._register_failure(archive, config, error_text)

    def _register_failure(self, archive, config, error_text):
        self.retry_count += 1
        if self.retry_count >= MAX_ATTEMPTS:
            self.write({'state': 'failed', 'last_error': error_text})
            archive.sudo().write({'drive_backup_status': 'failed'})
            self.env['bs.einvoice.audit.log'].sudo().create({
                'archive_id': archive.id, 'action': 'drive_backup_failed',
                'note': _("Google Drive backup failed after %s attempts: %s") % (MAX_ATTEMPTS, error_text),
            })
            archive.move_id.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_("Google Drive backup failed"),
                note=_("Archive %s could not be backed up to Google Drive after %s attempts. "
                       "See the archive's audit log for details.") % (archive.name, MAX_ATTEMPTS),
            )
        else:
            backoff_minutes = 2 ** self.retry_count
            self.write({
                'last_error': error_text,
                'scheduled_for': fields.Datetime.now() + timedelta(minutes=backoff_minutes),
            })

    def _upload_attachment(self, config, access_token, attachment, archive, kind):
        if not attachment:
            return False
        year_folder_id = config._ensure_folder(access_token, str(archive.archived_on.year), config.folder_id)
        filename = f"{archive.move_name.replace('/', '-')}.{kind}"
        metadata = {'name': filename, 'parents': [year_folder_id]}
        return self._multipart_upload(access_token, metadata, attachment.mimetype, attachment.datas)

    @api.model
    def _multipart_upload(self, access_token, metadata, mimetype, datas_b64):
        """Builds a Drive v3 multipart/related upload body by hand -- the
        alternative (a heavier Google API client library) would be
        overkill for two small POSTs. Returns the new file's ID.
        """
        boundary = uuid.uuid4().hex
        content = base64.b64decode(datas_b64 or b'')
        body = b''.join([
            f'--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n'.encode()
            + json.dumps(metadata).encode(),
            f'\r\n--{boundary}\r\nContent-Type: {mimetype or "application/octet-stream"}\r\n\r\n'.encode()
            + content,
            f'\r\n--{boundary}--'.encode(),
        ])
        resp = requests.post(
            UPLOAD_ENDPOINT, data=body, params={'fields': 'id'},
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': f'multipart/related; boundary={boundary}',
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()['id']
