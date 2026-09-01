import requests

TIMEOUT = 15
DEFAULT_URL_TEMPLATE = "https://graph.facebook.com/v19.0/{sender_id}/messages"


def send(gateway_config, phone_number, message):
    url = gateway_config.api_endpoint or DEFAULT_URL_TEMPLATE.format(sender_id=gateway_config.sender_id)
    headers = {
        'Authorization': 'Bearer %s' % gateway_config.api_key,
        'Content-Type': 'application/json',
    }
    payload = {
        'messaging_product': 'whatsapp',
        'to': phone_number.lstrip('+'),
        'type': 'text',
        'text': {'body': message},
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.text
