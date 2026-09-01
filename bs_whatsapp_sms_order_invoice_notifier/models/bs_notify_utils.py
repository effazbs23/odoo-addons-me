import re

# E.164: a leading '+', a country-code digit 1-9, then up to 14 more digits.
E164_RE = re.compile(r'^\+[1-9]\d{6,14}$')

TOKEN_RE = re.compile(r'\{\{(\w+)\}\}')


def is_valid_e164(number):
    return bool(number and E164_RE.match(number.strip()))


def render_template(template_text, tokens):
    """Replaces {{token}} placeholders with values from `tokens`; a token
    with no value for this record type is left blank rather than raising,
    since not every template applies to every event/model.
    """
    return TOKEN_RE.sub(lambda m: str(tokens.get(m.group(1), '')), template_text or '')
