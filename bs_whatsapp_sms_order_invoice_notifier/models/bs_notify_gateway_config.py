from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

CHANNEL_PROVIDERS = {
    'whatsapp': ('meta_cloud_api', 'twilio_whatsapp', 'generic_rest'),
    'sms': ('twilio_sms', 'generic_rest'),
}

PROVIDER_SELECTION = [
    ('meta_cloud_api', 'Meta Cloud API (WhatsApp)'),
    ('twilio_whatsapp', 'Twilio (WhatsApp)'),
    ('twilio_sms', 'Twilio (SMS)'),
    ('generic_rest', 'Generic REST Endpoint'),
]


class BsNotifyGatewayConfig(models.Model):
    _name = 'bs.notify.gateway.config'
    _description = 'Notification Gateway Configuration'

    channel = fields.Selection([('whatsapp', 'WhatsApp'), ('sms', 'SMS')], required=True)
    provider = fields.Selection(PROVIDER_SELECTION, required=True)
    api_endpoint = fields.Char(string="API Endpoint", help="Required for Generic REST; optional override for known providers.")
    api_key = fields.Char(string="API Key")
    api_secret = fields.Char(string="API Secret", help="Provider-dependent, e.g. Twilio Auth Token.")
    sender_id = fields.Char(string="Sender ID", help="Sender phone number/ID, provider-dependent.")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)

    @api.constrains('channel', 'provider')
    def _check_provider_matches_channel(self):
        for rec in self:
            if rec.provider not in CHANNEL_PROVIDERS.get(rec.channel, ()):
                raise ValidationError(_("Provider '%s' is not valid for channel '%s'.") % (rec.provider, rec.channel))

    @api.constrains('channel', 'active', 'company_id')
    def _check_single_active_gateway(self):
        # v1 has no multi-gateway failover (spec section 5): at most one
        # active gateway per channel per company.
        for rec in self.filtered('active'):
            duplicate = self.search([
                ('channel', '=', rec.channel),
                ('active', '=', True),
                ('company_id', '=', rec.company_id.id),
                ('id', '!=', rec.id),
            ], limit=1)
            if duplicate:
                raise ValidationError(_(
                    "Only one active %s gateway is allowed per company. Disable the existing one first."
                ) % rec.channel)

    def _get_active(self, channel, company):
        return self.search([
            ('channel', '=', channel),
            ('active', '=', True),
            ('company_id', '=', company.id),
        ], limit=1)
