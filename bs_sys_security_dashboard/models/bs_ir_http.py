from odoo import models
from odoo.http import request


class BsIrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _dispatch(cls, endpoint):
        response = super()._dispatch(endpoint)
        session = request.session
        if session.uid and not request.env.user._is_public():
            try:
                request.env['bs.session.log'].sudo()._bs_touch_session(
                    session.uid,
                    session.sid,
                    request.httprequest.environ.get('REMOTE_ADDR', 'n/a'),
                )
            except Exception:
                pass
        return response
