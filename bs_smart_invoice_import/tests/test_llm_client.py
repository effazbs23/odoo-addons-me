"""Plain unittest for the pure LLM response parsing (no database, no
network needed).

``llm_client.py`` is loaded directly by file path, same pattern as
``tests/test_parser.py`` uses for ``parser.py`` -- it only depends on
``requests`` (a real Odoo dependency already), not on any Odoo Model, so it
can run standalone. See tests/test_parser.py's module docstring for why this
loading style is needed instead of the normal ``odoo.addons...`` import.
"""
import importlib.util
import pathlib
import unittest

_llm_client_path = pathlib.Path(__file__).resolve().parent.parent / 'wizard' / 'llm_client.py'
_spec = importlib.util.spec_from_file_location('_bs_smart_invoice_import_llm_client', _llm_client_path)
llm_client = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(llm_client)


class TestBuildPayload(unittest.TestCase):

    def test_model_included_when_provided(self):
        payload = llm_client._build_payload('gpt-4o-mini', 'prompt text', [])
        self.assertEqual(payload['model'], 'gpt-4o-mini')

    def test_model_omitted_when_empty(self):
        # Not every OpenAI-compatible provider needs/accepts a "model" key
        # (e.g. some gateways route by API key alone) -- must never be
        # hardcoded to a default when the admin left it blank.
        payload = llm_client._build_payload('', 'prompt text', [])
        self.assertNotIn('model', payload)

    def test_model_omitted_when_none(self):
        payload = llm_client._build_payload(None, 'prompt text', [])
        self.assertNotIn('model', payload)

    def test_images_and_prompt_included_regardless_of_model(self):
        payload = llm_client._build_payload('', 'prompt text', [('image/png', 'abc123')])
        content = payload['messages'][0]['content']
        self.assertEqual(content[0], {'type': 'text', 'text': 'prompt text'})
        self.assertEqual(content[1]['type'], 'image_url')
        self.assertEqual(content[1]['image_url']['url'], 'data:image/png;base64,abc123')


class TestParseJsonRows(unittest.TestCase):

    def test_plain_json_array(self):
        text = '[{"name": "Blue Widget", "sku": "ABC-123", "qty": 12}]'
        rows = llm_client._parse_json_rows(text)
        self.assertEqual(rows, [
            {'raw_line': 'Blue Widget', 'sku': 'ABC-123', 'name': 'Blue Widget', 'qty': 12.0},
        ])

    def test_markdown_fenced_json(self):
        text = '```json\n[{"name": "Red Widget", "sku": null, "qty": 3}]\n```'
        rows = llm_client._parse_json_rows(text)
        self.assertEqual(rows, [
            {'raw_line': 'Red Widget', 'sku': '', 'name': 'Red Widget', 'qty': 3.0},
        ])

    def test_plain_fence_no_language_tag(self):
        text = '```\n[{"name": "Green Gadget", "sku": "GG-1", "qty": 9}]\n```'
        rows = llm_client._parse_json_rows(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['sku'], 'GG-1')

    def test_garbage_input_raises(self):
        with self.assertRaises(llm_client.LLMError):
            llm_client._parse_json_rows("Sorry, I can't read this invoice.")

    def test_non_array_json_raises(self):
        with self.assertRaises(llm_client.LLMError):
            llm_client._parse_json_rows('{"name": "Blue Widget"}')

    def test_missing_qty_defaults_to_one(self):
        text = '[{"name": "Mystery Item"}]'
        rows = llm_client._parse_json_rows(text)
        self.assertEqual(rows[0]['qty'], 1.0)

    def test_non_numeric_qty_defaults_to_one(self):
        text = '[{"name": "Mystery Item", "qty": "a few"}]'
        rows = llm_client._parse_json_rows(text)
        self.assertEqual(rows[0]['qty'], 1.0)

    def test_row_with_no_name_or_sku_is_skipped(self):
        text = '[{"qty": 5}, {"name": "Keeper", "qty": 1}]'
        rows = llm_client._parse_json_rows(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['name'], 'Keeper')

    def test_non_dict_items_are_skipped(self):
        text = '["not a dict", {"name": "Keeper", "qty": 1}]'
        rows = llm_client._parse_json_rows(text)
        self.assertEqual(len(rows), 1)

    def test_sku_only_row_uses_sku_as_raw_line(self):
        text = '[{"name": null, "sku": "XYZ-999", "qty": 2}]'
        rows = llm_client._parse_json_rows(text)
        self.assertEqual(rows[0]['raw_line'], 'XYZ-999')

    def test_leading_prose_before_array_no_fence(self):
        # Real-world model behavior despite "return ONLY JSON": chatty
        # preamble with no markdown fence at all.
        text = 'Here are the line items I found:\n[{"name": "Blue Widget", "sku": "ABC-123", "qty": 12}]'
        rows = llm_client._parse_json_rows(text)
        self.assertEqual(rows[0]['sku'], 'ABC-123')

    def test_trailing_prose_after_array_no_fence(self):
        text = '[{"name": "Blue Widget", "sku": "ABC-123", "qty": 12}]\nLet me know if you need anything else!'
        rows = llm_client._parse_json_rows(text)
        self.assertEqual(rows[0]['sku'], 'ABC-123')

    def test_leading_and_trailing_prose_no_fence(self):
        text = ('Sure, here you go:\n'
                '[{"name": "Blue Widget", "sku": "ABC-123", "qty": 12}]\n'
                'Hope that helps!')
        rows = llm_client._parse_json_rows(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['sku'], 'ABC-123')

    def test_array_wrapped_in_object(self):
        # Some models wrap the array in an object despite being asked for a
        # bare array, e.g. {"line_items": [...]}.
        text = '{"line_items": [{"name": "Blue Widget", "sku": "ABC-123", "qty": 12}]}'
        rows = llm_client._parse_json_rows(text)
        self.assertEqual(rows[0]['sku'], 'ABC-123')

    def test_bracket_inside_string_value_does_not_break_scan(self):
        text = 'Note: [not real data]\n[{"name": "Widget [v2]", "sku": "ABC-123", "qty": 1}]'
        rows = llm_client._parse_json_rows(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['name'], 'Widget [v2]')

    def test_error_message_includes_raw_response_preview(self):
        with self.assertRaises(llm_client.LLMError) as ctx:
            llm_client._parse_json_rows("Sorry, I can't read this invoice.")
        self.assertIn("Sorry, I can't read this invoice.", str(ctx.exception))

    def test_empty_array_returns_empty_list_not_error(self):
        rows = llm_client._parse_json_rows('[]')
        self.assertEqual(rows, [])


if __name__ == '__main__':
    unittest.main()
