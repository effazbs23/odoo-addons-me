# -*- coding: utf-8 -*-
import werkzeug

from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    # Frontend paths public visitors may still open while Coming Soon is on.
    _KINGDOM_COMING_SOON_ALLOW_PREFIXES = (
        '/coming-soon',
        '/web/',
        '/web',
        '/websocket',
        '/web/login',
        '/web/session',
        '/web/health',
        '/web/reset_password',
        '/web/signup',
        '/web/database',
        '/shop/quickview',
        '/theme_kingdom/quickview',
        '/theme_kingdom/snippet/render',
    )

    @classmethod
    def _kingdom_coming_soon_path_allowed(cls, path):
        path = (path or '/').split('?', 1)[0]
        if path != '/' and path.endswith('/'):
            path = path.rstrip('/')
        for prefix in cls._KINGDOM_COMING_SOON_ALLOW_PREFIXES:
            if path == prefix.rstrip('/') or path.startswith(prefix if prefix.endswith('/') else prefix + '/'):
                return True
            if prefix == '/coming-soon' and path.endswith('/coming-soon'):
                return True
        return False

    @classmethod
    def _frontend_pre_dispatch(cls):
        super()._frontend_pre_dispatch()
        website = getattr(request, 'website', None)
        if not website or not website.kingdom_should_redirect_coming_soon():
            return
        path = request.httprequest.path
        if cls._kingdom_coming_soon_path_allowed(path):
            return
        werkzeug.exceptions.abort(request.redirect('/coming-soon', code=303))
