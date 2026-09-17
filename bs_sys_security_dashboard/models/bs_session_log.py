from odoo import models, fields, api
from odoo.exceptions import AccessError
import odoo.http as http


class BsSessionLog(models.Model):
    _name = 'bs.session.log'
    _description = 'BS User Session Log'
    _order = 'last_activity desc'

    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade')
    session_id = fields.Char(string='Session ID', required=True, index=True)
    ip_address = fields.Char(string='IP Address')
    last_activity = fields.Datetime(string='Last Activity', default=fields.Datetime.now)

    _session_id_unique = models.Constraint(
        'unique(session_id)', 'A session log already exists for this session.',
    )

    @api.model
    def _bs_touch_session(self, uid, sid, ip):
        # Called on every request for a logged-in user, so this stays a single indexed upsert.
        log = self.sudo().search([('session_id', '=', sid)], limit=1)
        if log:
            log.write({'last_activity': fields.Datetime.now(), 'ip_address': ip})
        else:
            self.sudo().create({
                'user_id': uid,
                'session_id': sid,
                'ip_address': ip,
                'last_activity': fields.Datetime.now(),
            })

    @api.model
    def action_kill_session(self, session_id):
        if not self.env.user.has_group('base.group_system'):
            raise AccessError("Only administrators can terminate sessions.")
        self.sudo().search([('session_id', '=', session_id)]).unlink()
        if hasattr(http, 'root') and hasattr(http.root, 'session_store'):
            try:
                http.root.session_store.delete(session_id)
                return True
            except Exception:
                return False
        return False
