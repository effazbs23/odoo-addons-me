from odoo import _, fields, models
from odoo.exceptions import UserError


class BsEinvoiceAuditLog(models.Model):
    _name = 'bs.einvoice.audit.log'
    _description = 'E-Invoice Audit Log'
    _order = 'timestamp desc'

    # Optional: connect/disconnect events (drive_connected/drive_disconnected)
    # aren't tied to any one archive, so this is nullable.
    archive_id = fields.Many2one('bs.einvoice.archive', ondelete='cascade', index=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, required=True)
    action = fields.Selection([
        ('created', 'Created'),
        ('viewed', 'Viewed'),
        ('exported', 'Exported'),
        ('status_updated', 'Status Updated'),
        ('disposal_attempted', 'Disposal Attempted'),
        ('disposal_approved', 'Disposal Approved'),
        ('drive_connected', 'Google Drive Connected'),
        ('drive_disconnected', 'Google Drive Disconnected'),
        ('drive_backup_succeeded', 'Google Drive Backup Succeeded'),
        ('drive_backup_failed', 'Google Drive Backup Failed'),
    ], required=True)
    timestamp = fields.Datetime(default=fields.Datetime.now, required=True)
    note = fields.Char()

    def write(self, vals):
        raise UserError(_("Audit log entries cannot be modified."))

    def unlink(self):
        raise UserError(_("Audit log entries cannot be deleted."))
