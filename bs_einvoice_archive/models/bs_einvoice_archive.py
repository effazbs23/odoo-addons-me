import logging

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

INVOICE_TYPES = [
    ('standard', 'Standard'),
    ('simplified', 'Simplified'),
    ('self_billed', 'Self-Billed'),
    ('credit_note', 'Credit Note'),
    ('debit_note', 'Debit Note'),
    ('capital_asset', 'Capital Asset'),
    ('real_estate', 'Real Estate'),
]

# The only fields a caller may still touch after creation. Everything else on
# this append-only snapshot is frozen the moment it's written (see write()
# below) -- that's the whole point of an audit archive. The drive_* fields
# are bookkeeping for the optional offsite-backup add-on (see
# bs_einvoice_drive_upload_queue.py), not part of the snapshot itself, so
# they're exempted the same way state/asp_status are.
MUTABLE_AFTER_CREATE = {
    'state', 'asp_status', 'asp_status_payload',
    'drive_xml_file_id', 'drive_pdf_file_id', 'drive_backup_status',
}


class BsEinvoiceArchive(models.Model):
    _name = 'bs.einvoice.archive'
    _description = 'E-Invoice Archive'
    _order = 'archived_on desc'

    name = fields.Char(required=True, copy=False, readonly=True, default=lambda self: _('New'))
    move_id = fields.Many2one('account.move', string='Invoice', required=True, ondelete='restrict', index=True)
    move_name = fields.Char(string='Invoice Number', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    partner_trn = fields.Char(string='Partner TRN')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    invoice_type = fields.Selection(INVOICE_TYPES, required=True)
    original_archive_id = fields.Many2one('bs.einvoice.archive', string='Original Invoice Archive')
    correction_ids = fields.One2many('bs.einvoice.archive', 'original_archive_id', string='Related Corrections')
    xml_attachment_id = fields.Many2one('ir.attachment', string='XML Attachment')
    pdf_attachment_id = fields.Many2one('ir.attachment', string='PDF Attachment')
    asp_status = fields.Selection([
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('not_applicable', 'Not Applicable'),
    ], default='not_applicable', required=True)
    asp_status_payload = fields.Text(string='ASP Status Payload')
    archived_on = fields.Datetime(required=True, default=fields.Datetime.now, readonly=True)
    retention_years = fields.Integer(required=True, readonly=True)
    retention_expiry_date = fields.Date(required=True, readonly=True, index=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('eligible_for_disposal', 'Eligible for Disposal'),
        ('disposed', 'Disposed'),
    ], default='active', required=True)
    checksum = fields.Char(string='SHA-256 Checksum', readonly=True)
    audit_log_ids = fields.One2many('bs.einvoice.audit.log', 'archive_id', string='Audit Log')
    audit_log_count = fields.Integer(compute='_compute_audit_log_count')

    # -- Optional Google Drive offsite-backup add-on (see
    # bs_einvoice_drive_config.py / bs_einvoice_drive_upload_queue.py) --
    drive_xml_file_id = fields.Char(string='Drive XML File ID', readonly=True)
    drive_pdf_file_id = fields.Char(string='Drive PDF File ID', readonly=True)
    drive_backup_status = fields.Selection([
        ('not_applicable', 'Not Applicable'),
        ('pending', 'Pending'),
        ('backed_up', 'Backed Up'),
        ('failed', 'Failed'),
    ], default='not_applicable', required=True)

    _move_id_unique = models.Constraint('unique(move_id)', 'An archive already exists for this invoice.')

    @api.depends('audit_log_ids')
    def _compute_audit_log_count(self):
        for archive in self:
            archive.audit_log_count = len(archive.audit_log_ids)

    @api.constrains('invoice_type', 'original_archive_id')
    def _check_original_archive_required(self):
        for archive in self:
            if archive.invoice_type in ('credit_note', 'debit_note') and not archive.original_archive_id:
                raise UserError(_(
                    "A %s archive must reference the original invoice's archive record."
                ) % archive.invoice_type)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('bs.einvoice.archive') or _('New')
            if 'retention_expiry_date' not in vals:
                archived_on = vals.get('archived_on') or fields.Datetime.now()
                if isinstance(archived_on, str):
                    archived_on = fields.Datetime.from_string(archived_on)
                vals['retention_expiry_date'] = archived_on.date() + relativedelta(years=vals.get('retention_years', 0))
        archives = super().create(vals_list)
        self.env['bs.einvoice.audit.log'].sudo().create([{
            'archive_id': archive.id,
            'action': 'created',
            'note': _("Archive created for invoice %s") % archive.move_name,
        } for archive in archives])
        archives._queue_drive_backup()
        return archives

    def _queue_drive_backup(self):
        """Queue an offsite-backup upload job per archive, one DB insert
        each -- never call the Google API here. This runs inside the same
        transaction as invoice posting, so it must stay cheap; the actual
        upload happens later via the drive upload queue's cron.
        """
        Config = self.env['bs.einvoice.drive.config'].sudo()
        Queue = self.env['bs.einvoice.drive.upload.queue'].sudo()
        connected_company_ids = set(Config.search([
            ('company_id', 'in', self.mapped('company_id').ids), ('status', '=', 'connected'),
        ]).mapped('company_id.id'))
        to_queue = self.filtered(lambda a: a.company_id.id in connected_company_ids)
        if to_queue:
            Queue.create([{'archive_id': archive.id} for archive in to_queue])
            to_queue.write({'drive_backup_status': 'pending'})

    def write(self, vals):
        disallowed = set(vals) - MUTABLE_AFTER_CREATE
        if disallowed:
            raise UserError(_(
                "This archive is append-only: %s cannot be changed after creation."
            ) % ', '.join(sorted(disallowed)))
        return super().write(vals)

    def unlink(self):
        raise UserError(_("Archive records cannot be deleted. Retention expiry only makes a record eligible for disposal; disposal itself never deletes the row."))

    def action_view_audit_log(self):
        self.ensure_one()
        self.env['bs.einvoice.audit.log'].sudo().create({
            'archive_id': self.id,
            'action': 'viewed',
        })
        action = self.env['ir.actions.act_window']._for_xml_id('bs_einvoice_archive.action_einvoice_audit_log')
        action['domain'] = [('archive_id', '=', self.id)]
        return action

    def action_view_original(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Original Invoice Archive'),
            'res_model': 'bs.einvoice.archive',
            'view_mode': 'form',
            'res_id': self.original_archive_id.id,
        }

    def action_view_corrections(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Related Corrections'),
            'res_model': 'bs.einvoice.archive',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.correction_ids.ids)],
        }

    def action_mark_disposed(self):
        if not self.env.user.has_group('bs_einvoice_archive.group_einvoice_archive_admin'):
            raise UserError(_("Only an E-Invoice Archive Administrator can approve disposal."))
        for archive in self:
            if archive.state != 'eligible_for_disposal':
                raise UserError(_("Only records eligible for disposal can be marked disposed."))
        self.env['bs.einvoice.audit.log'].sudo().create([{
            'archive_id': archive.id,
            'action': 'disposal_approved',
            'note': _("Marked disposed by %s") % self.env.user.name,
        } for archive in self])
        self.write({'state': 'disposed'})

    def action_retry_drive_backup(self):
        if not self.env.user.has_group('bs_einvoice_archive.group_einvoice_archive_admin'):
            raise UserError(_("Only an E-Invoice Archive Administrator can retry a Drive backup."))
        for archive in self:
            if archive.drive_backup_status != 'failed':
                raise UserError(_("Only a failed backup can be retried."))
        self.sudo().write({'drive_backup_status': 'pending'})
        self.env['bs.einvoice.drive.upload.queue'].sudo().create([
            {'archive_id': archive.id} for archive in self
        ])

    # -- Daily health-check cron (see architecture doc section 3.2/3.3) -----

    @api.model
    def _cron_health_check(self):
        self._cron_flag_missing_archives()
        self._cron_flag_broken_attachments()
        self._cron_update_disposal_eligibility()
        self._cron_flag_broken_corrections()
        self._cron_flag_drive_backup_issues()

    @api.model
    def _cron_flag_drive_backup_issues(self):
        """Folds Google Drive backup health into the same summary email as
        the rest of the health check, per spec: no second reporting path.
        """
        failed = self.search_count([('drive_backup_status', '=', 'failed')])
        error_configs = self.env['bs.einvoice.drive.config'].sudo().search([('status', '=', 'error')])
        messages = []
        if failed:
            messages.append(_("%s archive(s) have a failed Google Drive backup.") % failed)
        if error_configs:
            messages.append(_("Google Drive connection is in an error state for: %s.")
                             % ', '.join(error_configs.mapped('company_id.name')))
        if messages:
            self._cron_notify_admins(' '.join(str(m) for m in messages))
        return failed, error_configs

    @api.model
    def _cron_flag_missing_archives(self):
        moves = self.env['account.move'].sudo().search([
            ('state', '=', 'posted'),
            ('move_type', 'in', ('out_invoice', 'out_refund', 'in_invoice', 'in_refund')),
            ('einvoice_archive_ids', '=', False),
        ])
        for move in moves:
            _logger.warning("bs_einvoice_archive: posted invoice %s has no archive record.", move.name)
            move.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_("E-Invoice archive missing"),
                note=_("This posted invoice has no bs.einvoice.archive record."),
            )
        if moves:
            self._cron_notify_admins(_("%s posted invoice(s) missing an e-invoice archive.") % len(moves))
        return moves

    @api.model
    def _cron_flag_broken_attachments(self):
        archives = self.search([('state', '!=', 'disposed')])
        broken = archives.filtered(lambda a: not a.pdf_attachment_id or not a.pdf_attachment_id.exists()
                                    or (a.xml_attachment_id and not a.xml_attachment_id.exists()))
        for archive in broken:
            _logger.warning("bs_einvoice_archive: archive %s has a missing/broken attachment.", archive.name)
            archive.move_id.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_("E-Invoice archive attachment missing"),
                note=_("Archive %s is missing its PDF/XML attachment.") % archive.name,
            )
        if broken:
            self._cron_notify_admins(_("%s archive(s) have a missing/broken attachment.") % len(broken))
        return broken

    @api.model
    def _cron_update_disposal_eligibility(self):
        today = fields.Date.context_today(self)
        expired = self.search([('state', '=', 'active'), ('retention_expiry_date', '<', today)])
        expired.write({'state': 'eligible_for_disposal'})
        return expired

    @api.model
    def _cron_flag_broken_corrections(self):
        archives = self.search([('invoice_type', 'in', ('credit_note', 'debit_note'))])
        broken = archives.filtered(lambda a: not a.original_archive_id or a.original_archive_id.state == 'disposed')
        for archive in broken:
            _logger.warning(
                "bs_einvoice_archive: %s archive %s has a broken original_archive_id link.",
                archive.invoice_type, archive.name,
            )
            archive.move_id.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_("E-Invoice correction link broken"),
                note=_("%s archive %s does not resolve to a valid, non-disposed original archive.")
                % (archive.invoice_type, archive.name),
            )
        if broken:
            self._cron_notify_admins(_("%s credit/debit note archive(s) have a broken original invoice link.") % len(broken))
        return broken

    @api.model
    def _cron_notify_admins(self, message):
        admins = self.env.ref('bs_einvoice_archive.group_einvoice_archive_admin').sudo().all_user_ids
        recipients = [email for email in admins.mapped('email') if email]
        if not recipients:
            return
        self.env['mail.mail'].sudo().create({
            'subject': _("E-Invoice Archive health check"),
            'body_html': f"<p>{message}</p>",
            'email_to': ','.join(recipients),
        })
