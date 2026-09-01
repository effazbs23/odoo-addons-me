import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from . import gateway_adapters
from .bs_notify_event_template import EVENT_TYPE_SELECTION
from .bs_notify_utils import is_valid_e164, render_template

_logger = logging.getLogger(__name__)

CHANNEL_SELECTION = [('whatsapp', 'WhatsApp'), ('sms', 'SMS')]
STATUS_SELECTION = [('sent', 'Sent'), ('failed', 'Failed'), ('skipped_no_phone', 'Skipped - No Phone')]
SOURCE_MODELS = [('sale.order', 'Sales Order'), ('account.move', 'Invoice'), ('stock.picking', 'Delivery')]


class BsNotifyLog(models.Model):
    _name = 'bs.notify.log'
    _description = 'Notification Delivery Log'
    _order = 'create_date desc'

    event_type = fields.Selection(EVENT_TYPE_SELECTION, required=True)
    channel = fields.Selection(CHANNEL_SELECTION, required=True)
    partner_id = fields.Many2one('res.partner')
    phone_number = fields.Char()
    # Indexed: looked up on every trigger (duplicate guard) and every
    # smart-button render on sale.order/stock.picking/account.move -- an
    # unindexed scan here gets slow as the log table grows in production.
    source_record_ref = fields.Reference(SOURCE_MODELS, string="Source Record", required=True, index=True)
    status = fields.Selection(STATUS_SELECTION, required=True)
    provider_response = fields.Text(string="Gateway Response")
    message_body = fields.Text()
    company_id = fields.Many2one('res.company')

    # ------------------------------------------------------------------
    # Central dispatch (spec section 7). Every trigger hook calls this and
    # only this. It must never raise -- a notification failure is always
    # a logged, retryable best-effort side effect, never a hard dependency
    # of the sale/account/stock transaction that triggered it.
    # ------------------------------------------------------------------

    @api.model
    def _send_notification(self, event_type, record, force=False):
        try:
            self._send_notification_unsafe(event_type, record, force=force)
        except Exception:  # noqa: BLE001 -- last-resort net, must never escape to the caller
            _logger.exception(
                "bs_whatsapp_sms_order_invoice_notifier: unexpected error dispatching '%s' for %s,%s",
                event_type, record._name, record.id,
            )

    def _send_notification_unsafe(self, event_type, record, force=False):
        company = record.company_id if 'company_id' in record._fields and record.company_id else self.env.company

        if not force and self._is_duplicate(event_type, record):
            return

        # sudo(): dispatch is internal system bookkeeping, not a user-facing
        # action -- it must not depend on whether the confirming/posting
        # user happens to have read access to notification config models
        # (gateway_config is deliberately admin-only since it holds API
        # secrets; a plain sales/accounting user triggering action_confirm
        # must still be able to look it up here).
        template = self.env['bs.notify.event.template'].sudo()._get_active(event_type, company)
        if not template:
            return  # event disabled / not configured -- a deliberate no-op, not a failure

        partner = self._get_partner(record)
        # Odoo 19 merged res.partner.mobile into a single 'phone' field --
        # there is no separate mobile field to read (spec section 6 assumed
        # the old two-field model; deviation logged in context.md).
        phone = (partner.phone or '').strip() if partner else ''
        if not is_valid_e164(phone):
            self.sudo().create({
                'event_type': event_type,
                'channel': 'sms' if template.channel == 'sms' else 'whatsapp',
                'partner_id': partner.id if partner else False,
                'phone_number': phone or False,
                'source_record_ref': '%s,%s' % (record._name, record.id),
                'status': 'skipped_no_phone',
                'provider_response': _("No valid E.164 mobile number on file."),
                'company_id': company.id,
            })
            return

        message = render_template(template.message_template, self._build_tokens(record))
        channels = ['whatsapp', 'sms'] if template.channel == 'both' else [template.channel]
        for channel in channels:
            self._send_via_channel(event_type, channel, record, partner, phone, message, company)

    def _send_via_channel(self, event_type, channel, record, partner, phone, message, company):
        # sudo(): same reasoning as the template lookup above -- gateway
        # credentials are admin-only by design, but any user's action can
        # trigger a send.
        gateway = self.env['bs.notify.gateway.config'].sudo()._get_active(channel, company)
        vals = {
            'event_type': event_type,
            'channel': channel,
            'partner_id': partner.id if partner else False,
            'phone_number': phone,
            'source_record_ref': '%s,%s' % (record._name, record.id),
            'message_body': message,
            'company_id': company.id,
        }
        if not gateway:
            vals.update(status='failed', provider_response=_("No active %s gateway configured.") % channel)
        else:
            try:
                response = gateway_adapters.send_message(gateway, phone, message)
                vals.update(status='sent', provider_response=response)
            except Exception as exc:  # noqa: BLE001 -- gateway/network errors must never escape
                _logger.warning(
                    "bs_whatsapp_sms_order_invoice_notifier: send failed for %s,%s: %s",
                    record._name, record.id, exc,
                )
                vals.update(status='failed', provider_response=str(exc))

        self.sudo().create(vals)
        if vals['status'] == 'sent':
            record.message_post(body=_("WhatsApp/SMS notification sent (%s): %s") % (channel, message))
        else:
            record.message_post(body=_("WhatsApp/SMS notification failed (%s): %s") % (channel, vals['provider_response']))

    def _is_duplicate(self, event_type, record):
        record_ref = '%s,%s' % (record._name, record.id)
        domain = [('event_type', '=', event_type), ('source_record_ref', '=', record_ref)]
        if event_type != 'invoice_overdue':
            # duplicate-trigger guard: only a previous *successful* send
            # blocks a re-fire, so a genuinely failed attempt can still be
            # retried automatically if the same lifecycle method runs twice.
            domain.append(('status', '=', 'sent'))
        # invoice_overdue: fire-once guard -- ANY prior attempt (sent,
        # failed or skipped) blocks the daily cron from retrying on its
        # own; a failed/skipped overdue notice still needs a manual resend.
        return bool(self.sudo().search_count(domain, limit=1))

    def _get_partner(self, record):
        return record.partner_id if 'partner_id' in record._fields else self.env['res.partner']

    def _build_tokens(self, record):
        tokens = {'partner_name': self._get_partner(record).name or ''}
        if record._name == 'sale.order':
            tokens.update(order_reference=record.name, amount_total=record.amount_total)
        elif record._name == 'account.move':
            tokens.update(
                invoice_number=record.name,
                amount_total=record.amount_total,
                due_date=record.invoice_date_due or '',
                payment_link=record.get_portal_url() if hasattr(record, 'get_portal_url') else '',
            )
        elif record._name == 'stock.picking':
            tokens.update(order_reference=record.origin or record.name)
        return tokens

    # ------------------------------------------------------------------
    # Manual resend (spec section 7.5 / 10)
    # ------------------------------------------------------------------

    def action_resend(self):
        self.ensure_one()
        record = self.source_record_ref
        if not record or not record.exists():
            raise UserError(_("The source record for this notification no longer exists."))
        if self.status == 'skipped_no_phone':
            # Nothing was ever sent -- retry the whole event from scratch
            # (force=True bypasses the duplicate guard), across every
            # channel the template specifies, since the phone may have
            # been fixed since.
            self._send_notification(self.event_type, record, force=True)
            return
        # status == 'failed': retry only the channel this log entry
        # represents. Re-running the full event would re-fire the sibling
        # channel too (e.g. re-send SMS when only WhatsApp had failed),
        # which is its own kind of duplicate the spec says to avoid.
        company = self.company_id or self.env.company
        partner = self.partner_id
        phone = (partner.phone or '').strip() if partner else self.phone_number
        self._send_via_channel(self.event_type, self.channel, record, partner, phone, self.message_body, company)
