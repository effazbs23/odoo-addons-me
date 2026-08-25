from . import models
from . import wizard
from . import controllers

from odoo import _
from odoo.exceptions import UserError
from odoo.fields import Date


def uninstall_hook(env):
    """Block uninstall while any archive is still within its legal retention
    window. The underlying ir.attachment/account.move records are untouched
    either way (see 2.5 of the architecture doc) -- this only protects the
    browse/audit/export interface from disappearing while records are still
    legally required to stay reachable.
    """
    Archive = env['bs.einvoice.archive'].sudo()
    unexpired = Archive.search_count([
        ('state', '!=', 'disposed'),
        ('retention_expiry_date', '>', Date.context_today(Archive)),
    ])
    if unexpired:
        raise UserError(_(
            "%(count)s e-invoice archive record(s) are still within their legal "
            "retention period and cannot be uninstalled away. The underlying "
            "PDF/XML files (stored as ir.attachment on the source invoices) "
            "will NOT be deleted, but you will lose the ability to browse, "
            "audit-log, and export them through this module. If you must "
            "proceed, dispose of or wait out the retention period for these "
            "records first.",
            count=unexpired,
        ))
    _revoke_drive_tokens(env)


def _revoke_drive_tokens(env):
    """Courtesy step only: revokes this app's OAuth grant with Google so it
    stops showing up under the client's connected apps. Never touches a
    single file in the client's actual Drive (same principle as the local
    ir.attachment strategy -- the backups are meant to outlive this
    module) and never blocks uninstall if Google can't be reached.
    """
    for config in env['bs.einvoice.drive.config'].sudo().search([('status', '=', 'connected')]):
        try:
            config._do_disconnect()
        except Exception:  # noqa: BLE001 -- uninstall must proceed regardless
            pass
