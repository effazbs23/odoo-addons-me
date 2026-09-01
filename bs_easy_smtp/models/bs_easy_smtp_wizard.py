from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .bs_easy_smtp_preset import ENCRYPTION_SELECTION, PROVIDER_SELECTION

# smtp_encryption on ir.mail_server also allows 'starttls_strict'/'ssl_strict' (stricter
# certificate validation); this wizard only offers the 3 baseline modes from the spec, so
# coerce the stricter variants down to their base mode when prefilling from an existing server.
_ENCRYPTION_FALLBACK = {'starttls_strict': 'starttls', 'ssl_strict': 'ssl'}


class BsEasySmtpWizard(models.TransientModel):
    _name = 'bs.easy.smtp.wizard'
    _description = "Easy SMTP Setup Wizard"

    state = fields.Selection(
        [('provider', "Choose Provider"), ('credentials', "Credentials & Test")],
        default='provider', required=True)

    provider = fields.Selection(PROVIDER_SELECTION, required=True, default='gmail')
    smtp_host = fields.Char(string="SMTP Server")
    smtp_port = fields.Integer(string="SMTP Port", default=587)
    smtp_encryption = fields.Selection(ENCRYPTION_SELECTION, string="Encryption", default='starttls')
    credential_note = fields.Text(readonly=True)
    credential_help_url = fields.Char(readonly=True)

    smtp_user = fields.Char(string="Username")
    smtp_pass = fields.Char(string="Password")
    test_email_to = fields.Char(string="Send Test To")

    test_result_status = fields.Selection(
        [('untested', "Not Tested"), ('success', "Success"), ('failed', "Failed")],
        default='untested', required=True)
    test_result_message = fields.Text(readonly=True)

    # set from default_get when an active mail server already exists (spec section 9:
    # re-running the wizard should update that server, not create a duplicate one)
    existing_mail_server_id = fields.Many2one('ir.mail_server', readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res.setdefault('test_email_to', self.env.user.email)
        existing = self.env['ir.mail_server'].search([], order='sequence, id', limit=1)
        if existing:
            res.update({
                # 'custom' so the automatic on-load onchange for 'provider' (Odoo always
                # fires it once for a field that has a default) doesn't clobber the
                # restored host/port/encryption below with a preset's values
                'provider': 'custom',
                'existing_mail_server_id': existing.id,
                'smtp_host': existing.smtp_host,
                'smtp_port': existing.smtp_port,
                'smtp_encryption': _ENCRYPTION_FALLBACK.get(existing.smtp_encryption, existing.smtp_encryption),
                'smtp_user': existing.smtp_user,
            })
        return res

    @api.onchange('provider')
    def _onchange_provider(self):
        # Custom must leave every field fully editable with no forced preset assumptions
        # (spec section 9) -- also what keeps default_get's existing-server restore intact.
        if not self.provider or self.provider == 'custom':
            return
        preset = self.env['bs.easy.smtp.preset'].search([('provider', '=', self.provider)], limit=1)
        self.smtp_host = preset.default_host
        self.smtp_port = preset.default_port
        self.smtp_encryption = preset.default_encryption
        self.credential_note = preset.credential_note
        self.credential_help_url = preset.credential_help_url

    def _reopen_action(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Easy SMTP Setup"),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def action_next(self):
        self.ensure_one()
        if not self.provider:
            raise UserError(_("Choose a provider first."))
        self.state = 'credentials'
        return self._reopen_action()

    def action_back(self):
        self.ensure_one()
        self.state = 'provider'
        return self._reopen_action()

    def action_test_send(self):
        self.ensure_one()
        if not self.test_email_to:
            raise UserError(_("Enter an email address to send the test to."))
        email_from = self.smtp_user or self.env.user.email
        if not email_from:
            raise UserError(_("Enter a username, or set an email address on your user, before sending a test."))

        mail_server = self.env['ir.mail_server']
        try:
            message = mail_server._build_email__(
                email_from=email_from,
                email_to=[self.test_email_to],
                subject=_("Easy SMTP Setup: test email"),
                body=_("This is a test email sent from the Easy SMTP Setup wizard. "
                       "If you received this, your outgoing mail settings are working."),
            )
            mail_server.send_email(
                message,
                smtp_server=self.smtp_host,
                smtp_port=self.smtp_port,
                smtp_user=self.smtp_user,
                smtp_password=self.smtp_pass,
                smtp_encryption=self.smtp_encryption,
            )
        except Exception as exc:  # noqa: BLE001 - broad on purpose, decoded below, never swallowed
            self.write({
                'test_result_status': 'failed',
                'test_result_message': mail_server._bs_easy_smtp_decode_error(str(exc)),
            })
            return self._reopen_action()

        self.write({
            'test_result_status': 'success',
            'test_result_message': _(
                "Test email sent successfully to %(to)s. This confirms the credentials and "
                "reachability from this server right now -- re-test after any network or "
                "credential change, especially when moving to production.",
                to=self.test_email_to,
            ),
        })
        return self._reopen_action()

    def action_save(self):
        self.ensure_one()
        if self.test_result_status != 'success':
            raise UserError(_("Send a successful test email before saving this as the active mail server."))

        vals = {
            'name': dict(PROVIDER_SELECTION).get(self.provider, "Easy SMTP Setup"),
            'smtp_host': self.smtp_host,
            'smtp_port': self.smtp_port,
            'smtp_encryption': self.smtp_encryption,
            'smtp_user': self.smtp_user,
            'smtp_pass': self.smtp_pass,
            'active': True,
        }
        if self.existing_mail_server_id:
            self.existing_mail_server_id.write(vals)
            server = self.existing_mail_server_id
        else:
            server = self.env['ir.mail_server'].create(vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _("Saved as the active outgoing mail server (%s).", server.name),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
