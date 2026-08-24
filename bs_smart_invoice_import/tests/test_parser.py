"""Plain unittest for the pure regex parser (no database needed).

Covers the batch of test lines from the module spec plus a few extra edge
cases discovered while implementing the "x" multiplier heuristics.

``parser.py`` is loaded directly by file path (not via the normal
``odoo.addons.bs_smart_invoice_import...`` import) so this file has zero
Odoo/database dependency and can run standalone with plain
``python3 -m unittest`` or ``pytest`` — going through the package's regular
``__init__.py`` chain would drag in ``quick_paste_wizard.py``'s Model
classes, which Odoo's ORM refuses to define outside a properly bootstrapped
``odoo.addons.*`` namespace. NOTE: because this stays a plain
``unittest.TestCase`` (not ``odoo.tests.BaseCase``), it is NOT auto-tagged
'standard' and will NOT be picked up by ``odoo-bin --test-enable``'s default
tag filter — run it directly instead. See tests/test_wizard.py for the
DB-backed TransactionCase tests that do run under Odoo's test runner.
"""
import importlib.util
import pathlib
import unittest

_parser_path = pathlib.Path(__file__).resolve().parent.parent / 'wizard' / 'parser.py'
_spec = importlib.util.spec_from_file_location('_bs_smart_invoice_import_parser', _parser_path)
_parser_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_parser_module)
parse_raw_text = _parser_module.parse_raw_text

SPEC_BATCH = """\
SKU    Description    Qty
ABC-123    Blue Widget    12
DEF-456    Red Widget    3
12 x GHI-789
JKL-321 x 5
qty: 7 MNO-654
Some plain item without a real sku, 4
PQR-100,   Green Gadget,   9"""


class TestQuickPasteParser(unittest.TestCase):

    def test_spec_batch_row_count(self):
        rows = parse_raw_text(SPEC_BATCH)
        # header row must be skipped, 7 data rows remain
        self.assertEqual(len(rows), 7)

    def test_header_row_skipped(self):
        rows = parse_raw_text(SPEC_BATCH)
        raw_lines = [r['raw_line'] for r in rows]
        self.assertNotIn('SKU    Description    Qty', raw_lines)

    def test_two_space_columns(self):
        rows = parse_raw_text(SPEC_BATCH)
        self.assertEqual(rows[0], {
            'raw_line': 'ABC-123    Blue Widget    12',
            'sku': 'ABC-123', 'name': 'Blue Widget', 'qty': 12,
        })
        self.assertEqual(rows[1], {
            'raw_line': 'DEF-456    Red Widget    3',
            'sku': 'DEF-456', 'name': 'Red Widget', 'qty': 3,
        })

    def test_qty_x_sku_marker(self):
        rows = parse_raw_text(SPEC_BATCH)
        row = rows[2]
        self.assertEqual(row['sku'], 'GHI-789')
        self.assertEqual(row['qty'], 12)

    def test_sku_x_qty_marker_does_not_eat_hyphenated_digits(self):
        rows = parse_raw_text(SPEC_BATCH)
        row = rows[3]
        self.assertEqual(row['raw_line'], 'JKL-321 x 5')
        self.assertEqual(row['sku'], 'JKL-321')
        self.assertEqual(row['qty'], 5)
        self.assertNotEqual(row['qty'], 321)

    def test_label_qty_form(self):
        rows = parse_raw_text(SPEC_BATCH)
        row = rows[4]
        self.assertEqual(row['sku'], 'MNO-654')
        self.assertEqual(row['qty'], 7)

    def test_no_sku_falls_back_to_last_numeric_column(self):
        rows = parse_raw_text(SPEC_BATCH)
        row = rows[5]
        self.assertEqual(row['sku'], '')
        self.assertEqual(row['qty'], 4)
        self.assertEqual(row['name'], 'Some plain item without a real sku')

    def test_comma_columns_strip_stray_punctuation(self):
        rows = parse_raw_text(SPEC_BATCH)
        row = rows[6]
        self.assertEqual(row['sku'], 'PQR-100')
        self.assertEqual(row['name'], 'Green Gadget')
        self.assertEqual(row['qty'], 9)
        self.assertFalse(row['name'].endswith(','))
        self.assertFalse(row['sku'].endswith(','))

    def test_default_qty_is_one(self):
        rows = parse_raw_text('WXY-999    Plain Product')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['qty'], 1)

    def test_bare_x_marker(self):
        rows = parse_raw_text('Blue Widget x12')
        self.assertEqual(rows[0]['qty'], 12)

    def test_bare_leading_qty_no_marker(self):
        # Casual customer-email text: no "x", no label, no delimiter --
        # just a leading number then free text.
        rows = parse_raw_text('500 ngk sapark plags')
        self.assertEqual(rows[0]['qty'], 500)
        self.assertEqual(rows[0]['sku'], '')
        self.assertEqual(rows[0]['name'], 'ngk sapark plags')

    def test_bare_qty_embedded_mid_sentence(self):
        # The quantity isn't always first -- plain single-spaced text with
        # a number anywhere still needs the number pulled out as qty, not
        # left stuck in the name (e.g. "storage box 77 pcs").
        rows = parse_raw_text('storage box 77 pics')
        self.assertEqual(rows[0]['qty'], 77)
        self.assertEqual(rows[0]['sku'], '')
        self.assertEqual(rows[0]['name'], 'storage box pics')

    def test_two_adjacent_bare_numbers_last_one_wins(self):
        # Two bare numbers with no marker/delimiter between them is
        # inherently ambiguous, but the leading one isn't swallowed by the
        # bare-leading-qty heuristic (Priority 3 requires a non-digit right
        # after the number) -- it falls through to the last-numeric-token
        # fallback instead, which picks the trailing number, consistent
        # with every other "last number wins" case in this parser.
        rows = parse_raw_text('12345678 2')
        self.assertEqual(rows[0]['qty'], 2)
        self.assertEqual(rows[0]['name'], '12345678')

    def test_quantity_equals_label(self):
        rows = parse_raw_text('quantity=15 XYZ-999')
        self.assertEqual(rows[0]['qty'], 15)
        self.assertEqual(rows[0]['sku'], 'XYZ-999')

    def test_sku_starting_with_x_not_swallowed_by_multiplier(self):
        # regression: a leading "X" in a SKU must not be misread as "qty x sku"
        rows = parse_raw_text('quantity=15 XYZ-999')
        self.assertEqual(rows[0]['sku'], 'XYZ-999')

    def test_tab_delimited_columns(self):
        rows = parse_raw_text('STU-222\tYellow Gadget\t20')
        self.assertEqual(rows[0], {
            'raw_line': 'STU-222\tYellow Gadget\t20',
            'sku': 'STU-222', 'name': 'Yellow Gadget', 'qty': 20,
        })

    def test_blank_lines_ignored(self):
        rows = parse_raw_text('\n\nABC-123    Blue Widget    12\n\n')
        self.assertEqual(len(rows), 1)

    def test_header_with_digits_not_skipped(self):
        # "sku" keyword present but row also has a digit -> must NOT be treated as header
        rows = parse_raw_text('Some plain item without a real sku, 4')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['qty'], 4)

    def test_empty_input(self):
        self.assertEqual(parse_raw_text(''), [])
        self.assertEqual(parse_raw_text(None), [])


if __name__ == '__main__':
    unittest.main()
