import requests

TIMEOUT = 15
DEFAULT_URL_TEMPLATE = "https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"


def _send(gateway_config, phone_number, message, whatsapp):
    account_sid = gateway_config.api_key
    auth_token = gateway_config.api_secret
    url = gateway_config.api_endpoint or DEFAULT_URL_TEMPLATE.format(account_sid=account_sid)
    sender = ('whatsapp:%s' % gateway_config.sender_id) if whatsapp else gateway_config.sender_id
    to = ('whatsapp:%s' % phone_number) if whatsapp else phone_number
    resp = requests.post(
        url,
        data={'From': sender, 'To': to, 'Body': message},
        auth=(account_sid, auth_token),
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.text


def send_whatsapp(gateway_config, phone_number, message):
    return _send(gateway_config, phone_number, message, whatsapp=True)


def send_sms(gateway_config, phone_number, message):
    return _send(gateway_config, phone_number, message, whatsapp=False)
