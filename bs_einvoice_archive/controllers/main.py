import json
import logging

import requests
from werkzeug.exceptions import BadRequest

from odoo import http
from odoo.http import request

from ..models.bs_einvoice_drive_config import GOOGLE_USERINFO_ENDPOINT

_logger = logging.getLogger(__name__)


class BsEinvoiceDriveOAuthController(http.Controller):

    @http.route('/bs_einvoice_archive/google_oauth/callback', type='http', auth='user')
    def google_oauth_callback(self, **kw):
        """Google redirects here after the user accepts/refuses the
        drive.file consent screen started from
        bs.einvoice.drive.config.action_connect().
        """
        try:
            state = json.loads(kw.get('state') or '{}')
        except ValueError:
            raise BadRequest()
        company_id = state.get('company_id')
        if not company_id:
            raise BadRequest()

        action = request.env.ref('bs_einvoice_archive.action_einvoice_drive_config')
        redirect_url = f'/odoo/action-{action.id}'

        if kw.get('error'):
            return request.redirect(f'{redirect_url}?drive_error={kw["error"]}')

        # Authorization must be fully checked -- group membership, that this
        # company is one the current user actually belongs to, and that the
        # 'state' round-trip matches the nonce action_connect() stashed in
        # this session -- before anything is written for an arbitrary
        # company_id supplied by (Google-relayed, but attacker-authored)
        # request data.
        if not request.env.user.has_group('bs_einvoice_archive.group_einvoice_archive_admin'):
            raise BadRequest()
        if company_id not in request.env.user.company_ids.ids:
            raise BadRequest()
        session_csrf = request.session.pop('bs_einvoice_drive_oauth_csrf', None)
        if not session_csrf or session_csrf != state.get('csrf'):
            raise BadRequest()
        if not kw.get('code'):
            raise BadRequest()

        Config = request.env['bs.einvoice.drive.config'].sudo()
        config = Config.search([('company_id', '=', company_id)], limit=1) or Config.create({'company_id': company_id})

        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        redirect_uri = f'{base_url}/bs_einvoice_archive/google_oauth/callback'
        try:
            access_token, refresh_token, _ttl = request.env['google.service']._get_google_tokens(
                kw['code'], 'bs_einvoice_drive', redirect_uri=redirect_uri,
            )
            email = requests.get(
                GOOGLE_USERINFO_ENDPOINT, headers={'Authorization': f'Bearer {access_token}'}, timeout=20,
            ).json().get('email', '')
            config._complete_connection(access_token, refresh_token, email)
        except Exception:
            _logger.exception("bs_einvoice_archive: Google Drive connection failed for company %s.", company_id)
            config.write({'status': 'error', 'last_error': 'Connection failed -- see server logs.'})

        return request.redirect(redirect_url)
