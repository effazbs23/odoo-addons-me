import base64
import hashlib
import json
import logging
import uuid

import requests
from cryptography.fernet import Fernet, InvalidToken

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

DRIVE_SERVICE = 'bs_einvoice_drive'
DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive.file'
GOOGLE_REVOKE_ENDPOINT = 'https://oauth2.googleapis.com/revoke'
GOOGLE_USERINFO_ENDPOINT = 'https://www.googleapis.com/oauth2/v2/userinfo'
GOOGLE_FILES_ENDPOINT = 'https://www.googleapis.com/drive/v3/files'
ROOT_FOLDER_NAME = 'E-Invoice Archive'


def _fernet_key(env):
    """Derive a Fernet key from Odoo's own per-database secret
    (ir.config_parameter 'database.secret', the same value core uses for
    HMAC signing -- see odoo.tools.misc.hmac) rather than inventing a new
    secret to manage.
    """
    secret = env['ir.config_parameter'].sudo().get_param('database.secret')
    return base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())


class BsEinvoiceDriveConfig(models.Model):
    _name = 'bs.einvoice.drive.config'
    _description = 'E-Invoice Google Drive Backup Config'

    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    google_account_email = fields.Char(readonly=True)
    refresh_token_encrypted = fields.Char(readonly=True, groups='bs_einvoice_archive.group_einvoice_archive_admin')
    folder_id = fields.Char(readonly=True, string='Drive Root Folder ID')
    status = fields.Selection([
        ('not_connected', 'Not Connected'),
        ('connected', 'Connected'),
        ('error', 'Error'),
    ], default='not_connected', required=True)
    last_error = fields.Text(readonly=True)
    pending_backup_count = fields.Integer(compute='_compute_backup_counts')
    failed_backup_count = fields.Integer(compute='_compute_backup_counts')

    _company_unique = models.Constraint('unique(company_id)', 'Only one Drive config per company.')

    def _compute_backup_counts(self):
        Archive = self.env['bs.einvoice.archive'].sudo()
        for config in self:
            domain = [('company_id', '=', config.company_id.id)]
            config.pending_backup_count = Archive.search_count(domain + [('drive_backup_status', '=', 'pending')])
            config.failed_backup_count = Archive.search_count(domain + [('drive_backup_status', '=', 'failed')])

    def action_view_pending_backups(self):
        self.ensure_one()
        return self._archives_action(_('Pending Drive Backups'), 'pending')

    def action_view_failed_backups(self):
        self.ensure_one()
        return self._archives_action(_('Failed Drive Backups'), 'failed')

    def _archives_action(self, name, drive_backup_status):
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': 'bs.einvoice.archive',
            'view_mode': 'list,form',
            'domain': [('company_id', '=', self.company_id.id), ('drive_backup_status', '=', drive_backup_status)],
        }

    # -- Token storage (encrypted at rest, never exposed in plain text) ----

    def _get_refresh_token(self):
        self.ensure_one()
        if not self.refresh_token_encrypted:
            return False
        try:
            return Fernet(_fernet_key(self.env)).decrypt(self.refresh_token_encrypted.encode()).decode()
        except InvalidToken:
            _logger.error("bs_einvoice_archive: could not decrypt stored Drive refresh token for company %s.",
                          self.company_id.id)
            return False

    def _set_refresh_token(self, token):
        self.ensure_one()
        encrypted = Fernet(_fernet_key(self.env)).encrypt(token.encode()).decode() if token else False
        self.sudo().write({'refresh_token_encrypted': encrypted})

    # -- OAuth connect / disconnect -----------------------------------------

    def _check_admin(self):
        if not self.env.user.has_group('bs_einvoice_archive.group_einvoice_archive_admin'):
            raise UserError(_("Only an E-Invoice Archive Administrator can manage the Google Drive connection."))

    def _redirect_uri(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return base_url + '/bs_einvoice_archive/google_oauth/callback'

    def action_connect(self):
        """Redirects to Google's consent screen for the drive.file scope
        only -- never a broader Drive scope (see architecture doc security
        notes).
        """
        self.ensure_one()
        self._check_admin()
        state = json.dumps({'company_id': self.company_id.id, 'csrf': uuid.uuid4().hex})
        url = self.env['google.service']._get_authorize_uri(
            DRIVE_SERVICE, DRIVE_SCOPE, self._redirect_uri(),
            state=state, approval_prompt='force', access_type='offline',
        )
        return {'type': 'ir.actions.act_url', 'url': url, 'target': 'self'}

    def action_disconnect(self):
        self.ensure_one()
        self._check_admin()
        self._do_disconnect()

    def _do_disconnect(self):
        """The actual disconnect logic, without the admin-group gate --
        used by action_disconnect() (user-triggered) and by the module's
        uninstall_hook (system-triggered courtesy revoke).
        """
        self.ensure_one()
        token = self._get_refresh_token()
        if token:
            try:
                requests.post(GOOGLE_REVOKE_ENDPOINT, params={'token': token}, timeout=20)
            except requests.RequestException:
                # Best-effort courtesy call -- disconnecting locally must
                # succeed even if Google's endpoint is unreachable.
                _logger.warning("bs_einvoice_archive: failed to revoke Drive token with Google (non-fatal).")
        company_name = self.company_id.name
        self.sudo().write({
            'google_account_email': False, 'refresh_token_encrypted': False,
            'folder_id': False, 'status': 'not_connected', 'last_error': False,
        })
        self.env['bs.einvoice.audit.log'].sudo().create({
            'action': 'drive_disconnected',
            'note': _("Google Drive backup disconnected for company %s") % company_name,
        })

    # -- Called by the OAuth callback controller ----------------------------

    def _complete_connection(self, access_token, refresh_token, email):
        self.ensure_one()
        self._set_refresh_token(refresh_token)
        folder_id = self._ensure_folder(access_token, ROOT_FOLDER_NAME, parent_id=None)
        self.sudo().write({
            'google_account_email': email, 'folder_id': folder_id,
            'status': 'connected', 'last_error': False,
        })
        self.env['bs.einvoice.audit.log'].sudo().create({
            'action': 'drive_connected',
            'note': _("Google Drive backup connected (%s) for company %s") % (email, self.company_id.name),
        })

    # -- Drive API helpers (shared with the upload queue) -------------------

    def _access_token(self):
        """Exchanges the stored refresh token for a fresh access token.
        Raises UserError (never with the token in the message) if there is
        no connected account.
        """
        self.ensure_one()
        refresh_token = self._get_refresh_token()
        if not refresh_token:
            raise UserError(_("No Google Drive account is connected for company %s.") % self.company_id.name)
        access_token, _ttl = self.env['google.service']._refresh_google_token(DRIVE_SERVICE, refresh_token)
        return access_token

    @api.model
    def _ensure_folder(self, access_token, name, parent_id):
        """Finds (or creates) a Drive folder by name under parent_id (None
        means the Drive root) and returns its file ID.
        """
        query = f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        query += f" and '{parent_id}' in parents" if parent_id else " and 'root' in parents"
        resp = requests.get(
            GOOGLE_FILES_ENDPOINT, params={'q': query, 'fields': 'files(id)'},
            headers={'Authorization': f'Bearer {access_token}'}, timeout=20,
        )
        resp.raise_for_status()
        files = resp.json().get('files') or []
        if files:
            return files[0]['id']

        metadata = {'name': name, 'mimeType': 'application/vnd.google-apps.folder'}
        if parent_id:
            metadata['parents'] = [parent_id]
        resp = requests.post(
            GOOGLE_FILES_ENDPOINT, json=metadata, params={'fields': 'id'},
            headers={'Authorization': f'Bearer {access_token}'}, timeout=20,
        )
        resp.raise_for_status()
        return resp.json()['id']
