from odoo import fields, models

PROVIDER_SELECTION = [
    ('gmail', "Gmail"),
    ('google_workspace', "Google Workspace"),
    ('office365', "Office 365 / Outlook"),
    ('zoho', "Zoho Mail"),
    ('ses', "Amazon SES"),
    ('sendgrid', "SendGrid"),
    ('mailgun', "Mailgun"),
    ('custom', "Custom SMTP"),
]

ENCRYPTION_SELECTION = [
    ('none', "None"),
    ('starttls', "TLS (STARTTLS)"),
    ('ssl', "SSL/TLS"),
]


class BsEasySmtpPreset(models.Model):
    _name = 'bs.easy.smtp.preset'
    _description = "Easy SMTP Setup: Provider Preset"

    provider = fields.Selection(PROVIDER_SELECTION, required=True)
    default_host = fields.Char()
    default_port = fields.Integer()
    default_encryption = fields.Selection(ENCRYPTION_SELECTION)
    credential_note = fields.Text(
        help="Short guidance shown in the wizard when this provider needs an "
             "app password or API key instead of a normal account password.")
    credential_help_url = fields.Char(help="Link to the provider's own credential setup docs.")
