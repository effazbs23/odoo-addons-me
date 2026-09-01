import requests

TIMEOUT = 15


def send(gateway_config, phone_number, message):
    if not gateway_config.api_endpoint:
        raise ValueError("Generic REST provider requires an API endpoint")
    headers = {'Content-Type': 'application/json'}
    if gateway_config.api_key:
        headers['Authorization'] = 'Bearer %s' % gateway_config.api_key
    payload = {'to': phone_number, 'message': message, 'sender_id': gateway_config.sender_id}
    resp = requests.post(gateway_config.api_endpoint, json=payload, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.text
