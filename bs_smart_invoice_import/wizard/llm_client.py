"""OpenAI-compatible chat-completions client used to extract invoice line
items from uploaded images. No Odoo Model dependency -- see
``tests/test_llm_client.py``, which loads this file the same standalone way
``tests/test_parser.py`` loads ``parser.py``.
"""
import json
import logging
import re

import requests

_logger = logging.getLogger(__name__)

DEFAULT_PROMPT = (
    "You are an invoice-reading assistant. Look at the attached invoice "
    "image(s) and extract every line item.\n"
    "Return ONLY a JSON array (no markdown fences, no commentary, no "
    "explanation) where each element is an object:\n"
    '{"name": "<item description as printed>", '
    '"sku": "<item/product code if printed, else null>", '
    '"qty": <ordered/invoiced quantity as a number>}\n'
    "If a line item is unreadable or you are not confident about it, skip "
    "it rather than guessing."
)


class LLMError(Exception):
    """Raised for any network, HTTP, or response-shape failure talking to
    the configured LLM API, or for a response that isn't parseable as the
    expected JSON row list."""


def _build_payload(model, prompt, images_b64):
    content = [{'type': 'text', 'text': prompt}]
    for mime_type, b64_data in images_b64:
        content.append({
            'type': 'image_url',
            'image_url': {'url': f'data:{mime_type};base64,{b64_data}'},
        })
    payload = {
        'messages': [{'role': 'user', 'content': content}],
        'temperature': 0,
    }
    # Not every OpenAI-compatible endpoint requires (or even accepts) a
    # "model" key -- some gateways route by API key/base URL alone. Only
    # include it if the admin actually configured one; never substitute a
    # hardcoded default, since that would silently pin every provider to
    # whatever model we guessed.
    if model:
        payload['model'] = model
    return payload


def extract_invoice_lines(base_url, api_key, model, prompt, images_b64, timeout=90):
    """Call an OpenAI-compatible ``/chat/completions`` endpoint with the
    given invoice page image(s) and return a list of
    {'raw_line', 'sku', 'name', 'qty'} dicts -- the same row shape
    ``wizard/parser.py:parse_raw_text`` produces, so callers can feed either
    source into the same matching/preview pipeline.

    ``images_b64`` is a list of (mime_type, base64_str) tuples, one per
    invoice page/image.
    """
    url = base_url.rstrip('/') + '/chat/completions'
    headers = {'Content-Type': 'application/json'}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    payload = _build_payload(model, prompt or DEFAULT_PROMPT, images_b64)

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise LLMError(str(exc)) from exc

    try:
        data = response.json()
        text = data['choices'][0]['message']['content']
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise LLMError("Unexpected response shape from the LLM API.") from exc

    return _parse_json_rows(text)


_FENCE_RE = re.compile(r'```(?:json)?\s*(.*?)\s*```', re.DOTALL | re.IGNORECASE)


def _iter_bracketed_arrays(text):
    """Yield every top-level [...] array substring found in text, left to
    right (respecting string literals, so a ']' inside a quoted value
    doesn't end a match early). A chatty response can contain more than one
    bracketed region (e.g. an unrelated aside before the real data), so
    callers should try each in order rather than only the first.
    """
    i = 0
    n = len(text)
    while i < n:
        start = text.find('[', i)
        if start == -1:
            return
        depth = 0
        in_string = False
        escape = False
        end = None
        for j in range(start, n):
            char = text[j]
            if in_string:
                if escape:
                    escape = False
                elif char == '\\':
                    escape = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == '[':
                depth += 1
            elif char == ']':
                depth -= 1
                if depth == 0:
                    end = j
                    break
        if end is None:
            return
        yield text[start:end + 1]
        i = end + 1


def _candidate_json_strings(text):
    """Real models don't reliably follow "return ONLY JSON": they add
    leading/trailing commentary, fence the array in markdown even when told
    not to, or wrap it in an object like {"line_items": [...]}. Yields
    progressively more forgiving extraction attempts, tried in order until
    one parses into a usable row list.
    """
    yield text

    fence_match = _FENCE_RE.search(text)
    if fence_match:
        yield fence_match.group(1).strip()

    yield from _iter_bracketed_arrays(text)


def _rows_from_parsed(items):
    """Convert already-`json.loads`-parsed data into row dicts, or return
    None if the shape isn't recognizable at all (list, or a dict wrapping a
    list under some key) -- as opposed to a recognizable-but-empty list,
    which is a legitimate "no rows" result, not a shape mismatch."""
    if isinstance(items, dict):
        items = next((v for v in items.values() if isinstance(v, list)), None)
    if not isinstance(items, list):
        return None

    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = (item.get('name') or '').strip()
        sku = (item.get('sku') or '').strip() if item.get('sku') else ''
        qty_raw = item.get('qty', 1)
        try:
            qty = float(qty_raw)
        except (TypeError, ValueError):
            qty = 1.0
        if not (name or sku):
            continue
        rows.append({
            'raw_line': name or sku,
            'sku': sku,
            'name': name,
            'qty': qty,
        })
    return rows


def _parse_json_rows(text):
    """Parse the LLM's text response into row dicts, trying progressively
    more forgiving extraction strategies (see _candidate_json_strings)
    before giving up."""
    text = text or ''
    for candidate in _candidate_json_strings(text.strip()):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        rows = _rows_from_parsed(parsed)
        if rows is not None:
            return rows

    _logger.warning("Could not parse LLM response as JSON. Raw response: %r", text)
    preview = text.strip()
    if len(preview) > 300:
        preview = preview[:300] + '...'
    raise LLMError(
        "Could not parse the LLM's response as JSON. The model's raw reply "
        "started with: " + (preview or '(empty response)')
    )
