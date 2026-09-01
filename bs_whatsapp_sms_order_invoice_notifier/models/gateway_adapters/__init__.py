from . import meta_cloud_api
from . import twilio
from . import generic_rest

ADAPTERS = {
    'meta_cloud_api': meta_cloud_api.send,
    'twilio_whatsapp': twilio.send_whatsapp,
    'twilio_sms': twilio.send_sms,
    'generic_rest': generic_rest.send,
}


def send_message(gateway_config, phone_number, message):
    """Dispatches to the provider-specific adapter for `gateway_config.provider`.

    Adding a new provider means adding one adapter function here, not
    touching the dispatch logic in bs.notify.log.

    Raises on any failure -- the caller (bs.notify.log._send_notification)
    is the single place responsible for catching, logging, and never
    letting the error escape to the business transaction. Adapters
    themselves must not swallow errors, or the log loses the real reason.
    """
    adapter = ADAPTERS.get(gateway_config.provider)
    if not adapter:
        raise ValueError("No adapter implemented for provider '%s'" % gateway_config.provider)
    return adapter(gateway_config, phone_number, message)
