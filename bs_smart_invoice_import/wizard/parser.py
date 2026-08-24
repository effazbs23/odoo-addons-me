"""Pure regex/heuristic parser for the Quick Paste wizard.

No Odoo dependency on purpose: this module only turns raw pasted text into a
list of ``{'raw_line', 'sku', 'name', 'qty'}`` dicts, so it can be unit
tested without a database and swapped for (or augmented by) an AI-based
parser later without touching matching or line-creation logic. See
``quick_paste_wizard.py::_parse_order_rows`` for the extension seam.
"""
from __future__ import annotations

import re

HEADER_KEYWORDS = {
    'sku', 'code', 'ref', 'reference', 'product', 'item', 'description',
    'name', 'qty', 'quantity', 'unit', 'price', 'amount', 'total', 'uom',
}
_HEADER_RE = re.compile(
    r'\b(?:' + '|'.join(re.escape(kw) for kw in HEADER_KEYWORDS) + r')\b',
    re.IGNORECASE,
)
_DIGIT_RE = re.compile(r'\d')

# Priority 1: inline "qty x sku" / "sku x qty" / bare "x qty" markers.
# The (?<![\w-]) / (?![\w-]) guards stop a digit run inside a hyphenated SKU
# (e.g. the "321" in "JKL-321") from being mistaken for a standalone number.
# The (?=[\s\d]) lookahead after [xX] stops a SKU that itself starts with
# "X" (e.g. "XYZ-999") from having its leading letter swallowed as an "x"
# multiplier when preceded by an unrelated number.
_QTY_X_SKU_RE = re.compile(
    r'(?<![\w-])(?P<qty>\d+)\s*[xX](?=[\s\d])\s*'
    r'(?P<sku>[A-Za-z][A-Za-z0-9]*(?:[-_/][A-Za-z0-9]+)+)(?![\w-])'
)
_SKU_X_QTY_RE = re.compile(
    r'(?<![\w-])(?P<sku>[A-Za-z][A-Za-z0-9]*(?:[-_/][A-Za-z0-9]+)+)\s*[xX]\s*'
    r'(?P<qty>\d+)(?![\w-])'
)
_BARE_X_QTY_RE = re.compile(r'(?<![\w-])[xX]\s*(?P<qty>\d+)(?![\w-])')

# Priority 2: label form "qty: 12" / "quantity=12".
_LABEL_QTY_RE = re.compile(r'\b(?:qty|quantity)\b\s*[:=]\s*(?P<qty>\d+)', re.IGNORECASE)

# Priority 3: bare leading quantity, no marker/label at all, e.g.
# "500 NGK Spark Plugs" -- common in casual customer text copy-pasted from
# an email. The (?=\D) lookahead requires the next token to be non-numeric,
# so two adjacent bare numbers (e.g. a numeric barcode column followed by a
# separate qty column) are deliberately left to the last-numeric-column
# fallback below instead of being misread here.
_LEADING_QTY_RE = re.compile(r'^(?P<qty>\d+)\s+(?=\D)')

# A code-like token: alphanumeric (with -/_// separators allowed) that mixes
# at least one letter and one digit, e.g. ABC-123, GHI-789, SKU123.
_SKU_TOKEN_RE = re.compile(
    r'\b(?=[A-Za-z0-9\-_/]*[A-Za-z])(?=[A-Za-z0-9\-_/]*\d)'
    r'[A-Za-z0-9]+(?:[-_/][A-Za-z0-9]+)*\b'
)
_NUMERIC_RE = re.compile(r'^-?\d+(?:\.\d+)?$')
_STRAY_PUNCT = ' \t,;:-'


def _is_header(line: str) -> bool:
    return bool(_HEADER_RE.search(line)) and not _DIGIT_RE.search(line)


def _split_columns(line: str) -> list[str]:
    """Split a raw line into columns: tab > comma > 2+ spaces > single column."""
    if '\t' in line:
        cols = line.split('\t')
    elif ',' in line:
        cols = line.split(',')
    elif re.search(r'\s{2,}', line):
        cols = re.split(r'\s{2,}', line)
    else:
        cols = [line]
    return [c.strip(_STRAY_PUNCT).strip() for c in cols if c.strip(_STRAY_PUNCT).strip()]


def _clean(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip(_STRAY_PUNCT).strip()


def _extract_sku(text: str) -> tuple[str, str]:
    """Return (sku, remaining_text) pulling the first code-like token out of text."""
    match = _SKU_TOKEN_RE.search(text)
    if not match:
        return '', _clean(text)
    sku = match.group(0)
    remaining = text[:match.start()] + ' ' + text[match.end():]
    return sku, _clean(remaining)


def _parse_line(line: str) -> dict:
    raw_line = line

    # Priority 1: inline markers.
    match = _QTY_X_SKU_RE.search(line)
    if match:
        qty = int(match.group('qty'))
        sku = match.group('sku')
        remaining = line[:match.start()] + ' ' + line[match.end():]
        name = _clean(remaining)
        return {'raw_line': raw_line, 'sku': sku, 'name': name, 'qty': qty}

    match = _SKU_X_QTY_RE.search(line)
    if match:
        qty = int(match.group('qty'))
        sku = match.group('sku')
        remaining = line[:match.start()] + ' ' + line[match.end():]
        name = _clean(remaining)
        return {'raw_line': raw_line, 'sku': sku, 'name': name, 'qty': qty}

    match = _BARE_X_QTY_RE.search(line)
    if match:
        qty = int(match.group('qty'))
        remaining = line[:match.start()] + ' ' + line[match.end():]
        sku, name = _extract_sku(remaining)
        return {'raw_line': raw_line, 'sku': sku, 'name': name, 'qty': qty}

    # Priority 2: label form.
    match = _LABEL_QTY_RE.search(line)
    if match:
        qty = int(match.group('qty'))
        remaining = line[:match.start()] + ' ' + line[match.end():]
        sku, name = _extract_sku(remaining)
        return {'raw_line': raw_line, 'sku': sku, 'name': name, 'qty': qty}

    # Priority 3: bare leading quantity, no marker at all.
    match = _LEADING_QTY_RE.match(line)
    if match:
        qty = int(match.group('qty'))
        remaining = line[match.end():]
        sku, name = _extract_sku(remaining)
        return {'raw_line': raw_line, 'sku': sku, 'name': name, 'qty': qty}

    # Priority 4: fallback to the last purely-numeric column -- or, if the
    # line has no real column delimiter (tab/comma/2+space) at all, the
    # last purely-numeric *word*, so a quantity embedded mid-sentence in
    # plain single-spaced text (e.g. "storage box 77 pcs") is still found,
    # not just one sitting in its own column.
    columns = _split_columns(line)
    if len(columns) == 1:
        columns = line.split()
    qty = 1
    remaining_columns = columns
    for idx in range(len(columns) - 1, -1, -1):
        if _NUMERIC_RE.match(columns[idx]):
            qty = int(float(columns[idx]))
            remaining_columns = columns[:idx] + columns[idx + 1:]
            break

    sku, name = _extract_sku(' '.join(remaining_columns))
    return {'raw_line': raw_line, 'sku': sku, 'name': name, 'qty': qty}


def parse_raw_text(raw_text: str) -> list[dict]:
    """Parse a raw pasted text block into row dicts.

    Each row: {'raw_line': str, 'sku': str, 'name': str, 'qty': int}.
    Blank lines and detected header rows are skipped.
    """
    rows = []
    for line in (raw_text or '').splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if _is_header(stripped):
            continue
        rows.append(_parse_line(stripped))
    return rows
