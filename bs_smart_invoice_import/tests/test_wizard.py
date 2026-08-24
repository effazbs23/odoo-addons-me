import base64
from datetime import date
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.bs_smart_invoice_import.wizard.quick_paste_wizard import MAX_INVOICE_FILE_SIZE


@tagged('post_install', '-at_install')
class TestQuickPasteWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': "Quick Paste Test Partner"})
        cls.product_abc = cls.env['product.product'].create({
            'name': "Nimbrix Cascadel Quorten",
            'default_code': 'ABC-123',
            'standard_price': 10.0,
        })
        cls.product_def = cls.env['product.product'].create({
            'name': "Fenwick Ashgrove Trellis",
            'default_code': 'DEF-456',
            'standard_price': 20.0,
        })
        # Two similarly-worded products, used to test that a genuinely
        # ambiguous customer-style name (missing the distinguishing word)
        # comes back 'ambiguous' rather than guessing.
        cls.product_bracket_a = cls.env['product.product'].create({
            'name': "Acme Steel Bracket Type A",
            'default_code': 'BRK-A',
            'standard_price': 5.0,
        })
        cls.product_bracket_b = cls.env['product.product'].create({
            'name': "Acme Steel Bracket Type B",
            'default_code': 'BRK-B',
            'standard_price': 5.0,
        })
        # A near-duplicate family, used to test that a garbled customer
        # typo still resolves to the specific right variant rather than
        # its close sibling.
        cls.product_ngk = cls.env['product.product'].create({
            'name': "NGK Spark Plug",
            'default_code': 'NGK-STD',
            'standard_price': 3.0,
        })
        cls.product_ngk_iridium = cls.env['product.product'].create({
            'name': "NGK Iridium Spark Plug",
            'default_code': 'NGK-IRI',
            'standard_price': 8.0,
        })
        cls.product_champion = cls.env['product.product'].create({
            'name': "Champion Spark Plug",
            'default_code': 'CHM-STD',
            'standard_price': 4.0,
        })
        # A short single-word typo'd query against several multi-word
        # names, none of which share that word -- tests that a fragment
        # match ("dawer" vs "Office Drawer Unit") still resolves, without
        # being confused by unrelated multi-word products in the catalog.
        cls.product_drawer = cls.env['product.product'].create({
            'name': "Office Drawer Unit",
            'default_code': 'DWR-004',
            'standard_price': 60.0,
        })
        cls.product_storage_box = cls.env['product.product'].create({
            'name': "Storage Box",
            'default_code': 'BOX-003',
            'standard_price': 15.0,
        })
        cls.product_table = cls.env['product.product'].create({
            'name': "Big Meeting Table",
            'default_code': 'TBL-001',
            'standard_price': 500.0,
        })
        cls.product_lamp = cls.env['product.product'].create({
            'name': "LED Desk Lamp",
            'default_code': 'LMP-002',
            'standard_price': 20.0,
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })
        cls.purchase_order = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
        })

    def _make_wizard(self, order, raw_text):
        return self.env['quick.paste.wizard'].with_context(
            active_model=order._name, active_id=order.id,
        ).create({'raw_text': raw_text})

    def test_default_get_populates_order_reference(self):
        wizard = self._make_wizard(self.sale_order, '')
        self.assertEqual(wizard.order_id, self.sale_order)

    def test_match_product_exact_default_code(self):
        Wizard = self.env['quick.paste.wizard']
        product, status = Wizard._match_product('ABC-123', 'Blue Widget')
        self.assertEqual(status, 'matched')
        self.assertEqual(product, self.product_abc)

    def test_match_product_case_insensitive(self):
        Wizard = self.env['quick.paste.wizard']
        product, status = Wizard._match_product('abc-123', '')
        self.assertEqual(status, 'matched')
        self.assertEqual(product, self.product_abc)

    def test_match_product_fuzzy_name_fallback(self):
        # Names distinctive from both baseline (non-demo) products in any
        # real database AND from each other (a prior version of this test
        # used two names that were distinctive individually but too
        # structurally similar to each other -- "Zqplx Bluevex Widget
        # 77219" / "Zqplx Redvex Widget 88320" -- which difflib scored at
        # 0.72 similarity, above the 0.6 cutoff, producing a false
        # 'ambiguous' result).
        Wizard = self.env['quick.paste.wizard']
        product, status = Wizard._match_product('', 'Nimbrix Cascadel Quorte')  # typo
        self.assertEqual(status, 'matched')
        self.assertEqual(product, self.product_abc)

    def test_match_product_unmatched(self):
        Wizard = self.env['quick.paste.wizard']
        product, status = Wizard._match_product('NOPE-999', 'Completely Unrelated Thing')
        self.assertEqual(status, 'unmatched')
        self.assertFalse(product)

    def test_match_product_semantic_no_sku_customer_style(self):
        # Simulates a customer email: no SKU at all, just a misspelled/
        # reworded product name copied from memory.
        Wizard = self.env['quick.paste.wizard']
        product, status = Wizard._match_product('', 'nimbrix cascadl quorten')
        self.assertEqual(status, 'matched')
        self.assertEqual(product, self.product_abc)

    def test_match_product_semantic_ambiguous_missing_distinguisher(self):
        # "Acme Steel Bracket" (missing "Type A"/"Type B") is a genuine
        # ambiguity between two real products -- should not silently guess.
        Wizard = self.env['quick.paste.wizard']
        product, status = Wizard._match_product('', 'Acme Steel Bracket')
        self.assertEqual(status, 'ambiguous')
        self.assertIn(self.product_bracket_a, product)
        self.assertIn(self.product_bracket_b, product)

    def test_match_product_semantic_typo_resolves_specific_variant(self):
        # A typo that still includes the distinguishing word should resolve
        # to the specific variant, not fall into 'ambiguous'.
        Wizard = self.env['quick.paste.wizard']
        product, status = Wizard._match_product('', 'acme steel braket type a')
        self.assertEqual(status, 'matched')
        self.assertEqual(product, self.product_bracket_a)

    def test_match_product_hybrid_garbled_typo_ranks_correctly_but_ambiguous(self):
        # "sapark"/"plags" is a genuine spelling mangle, not just a
        # rewording -- semantic similarity alone put this too close to the
        # wrong sibling product ("NGK Iridium Spark Plug"); the rapidfuzz
        # blend is what still ranks the correct one on top (score 0.593).
        # Session 7 raised SEMANTIC_MATCH_THRESHOLD 0.55 -> 0.65 (to reject
        # an unrelated false positive seen on a different, thin catalog),
        # so this score no longer clears the auto-match bar -- it's now
        # 'ambiguous' (manual confirmation) rather than auto-'matched',
        # a deliberate, user-accepted tradeoff, not a regression.
        Wizard = self.env['quick.paste.wizard']
        product, status = Wizard._match_product('', 'ngk sapark plags')
        self.assertEqual(status, 'ambiguous')
        self.assertIn(self.product_ngk, product)

    def test_action_parse_bare_leading_qty_no_marker(self):
        # Real customer-email style: "500 ngk sapark plags" -- no SKU, no
        # "x"/"qty:" marker, just a leading number and a typo'd name. Qty
        # parsing is unaffected by the session 7 threshold change; product
        # status is now 'ambiguous' rather than 'matched' -- see
        # test_match_product_hybrid_garbled_typo_ranks_correctly_but_ambiguous.
        wizard = self._make_wizard(self.sale_order, "500 ngk sapark plags")
        wizard.action_parse()
        line = wizard.preview_line_ids
        self.assertEqual(line.qty, 500)
        self.assertEqual(line.status, 'ambiguous')

    def test_match_product_fuzzy_fragment_ranks_correctly_but_ambiguous(self):
        # A single short, typo'd word compared against a longer multi-word
        # product name it doesn't fully overlap with -- WRatio's
        # partial-match handling still ranks it correctly (score 0.596),
        # but that's below the raised 0.65 SEMANTIC_MATCH_THRESHOLD
        # (session 7), so this is now 'ambiguous' rather than auto-'matched'
        # -- same deliberate tradeoff as the ngk/sapark case above.
        Wizard = self.env['quick.paste.wizard']
        product, status = Wizard._match_product('', 'dawer')
        self.assertEqual(status, 'ambiguous')
        self.assertIn(self.product_drawer, product)

    def test_action_parse_mixed_leading_and_embedded_qty_batch(self):
        # The exact multi-line batch from the user's report: qty leads on
        # some lines, is embedded mid-sentence on another, and one line's
        # match is a short single-word fragment.
        wizard = self._make_wizard(
            self.sale_order,
            "200 big meting tabil\n30 lamp\nstorage box 77 pics\n12 dawer",
        )
        wizard.action_parse()
        lines = {line.raw_line: line for line in wizard.preview_line_ids}

        self.assertEqual(lines['200 big meting tabil'].qty, 200)
        self.assertEqual(lines['200 big meting tabil'].product_id, self.product_table)

        self.assertEqual(lines['30 lamp'].qty, 30)
        self.assertEqual(lines['30 lamp'].product_id, self.product_lamp)

        self.assertEqual(lines['storage box 77 pics'].qty, 77)
        self.assertEqual(lines['storage box 77 pics'].product_id, self.product_storage_box)

        # 'dawer' ranks the right product (0.596) but that's below the
        # raised 0.65 match threshold (session 7) -- 'ambiguous', not
        # auto-matched. See test_match_product_fuzzy_fragment_ranks_
        # correctly_but_ambiguous for the isolated case.
        self.assertEqual(lines['12 dawer'].qty, 12)
        self.assertEqual(lines['12 dawer'].status, 'ambiguous')

    def test_action_parse_populates_preview_lines(self):
        wizard = self._make_wizard(
            self.sale_order,
            "ABC-123    Blue Widget    12\nNOPE-999    Nothing Here    2",
        )
        wizard.action_parse()
        self.assertEqual(wizard.state, 'preview')
        self.assertEqual(len(wizard.preview_line_ids), 2)
        matched = wizard.preview_line_ids.filtered(lambda l: l.status == 'matched')
        unmatched = wizard.preview_line_ids.filtered(lambda l: l.status == 'unmatched')
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched.product_id, self.product_abc)
        self.assertEqual(len(unmatched), 1)

    def test_action_confirm_creates_sale_order_lines_and_skips_unmatched(self):
        wizard = self._make_wizard(
            self.sale_order,
            "ABC-123    Blue Widget    12\nDEF-456    Red Widget    3\nNOPE-999    Nothing Here    2",
        )
        wizard.action_parse()
        wizard.action_confirm()

        self.assertEqual(len(self.sale_order.order_line), 2)
        line_abc = self.sale_order.order_line.filtered(lambda l: l.product_id == self.product_abc)
        self.assertEqual(line_abc.product_uom_qty, 12)

        messages = self.sale_order.message_ids.mapped('body')
        self.assertTrue(any('NOPE-999' in body for body in messages))

    def test_action_confirm_creates_purchase_order_lines_with_standard_price(self):
        wizard = self._make_wizard(
            self.purchase_order,
            "ABC-123    Blue Widget    5",
        )
        wizard.action_parse()
        wizard.action_confirm()

        self.assertEqual(len(self.purchase_order.order_line), 1)
        line = self.purchase_order.order_line[0]
        self.assertEqual(line.product_qty, 5)
        self.assertEqual(line.price_unit, self.product_abc.standard_price)

    def test_action_confirm_without_order_raises(self):
        wizard = self.env['quick.paste.wizard'].create({'raw_text': 'ABC-123 Blue Widget 1'})
        wizard.action_parse()
        with self.assertRaises(Exception):
            wizard.action_confirm()

    # ------------------------------------------------------------------
    # Invoice upload / LLM extraction
    # ------------------------------------------------------------------
    def _set_llm_config(self, model=None):
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('bs_smart_invoice_import.llm_base_url', 'https://llm.example.com/v1')
        params.set_param('bs_smart_invoice_import.llm_api_key', 'test-key')
        if model:
            params.set_param('bs_smart_invoice_import.llm_model', model)

    def test_get_llm_config_none_when_unset(self):
        self.assertIsNone(self.env['quick.paste.wizard']._get_llm_config())

    def test_get_llm_config_none_with_base_url_but_no_api_key(self):
        # Groq (and most commercial providers) require an API key -- only
        # base_url isn't enough to consider this configured.
        self.env['ir.config_parameter'].sudo().set_param(
            'bs_smart_invoice_import.llm_base_url', 'https://api.groq.com/openai/v1',
        )
        self.assertIsNone(self.env['quick.paste.wizard']._get_llm_config())

    def test_get_llm_config_returns_dict_once_set(self):
        self._set_llm_config(model='test-model')
        config = self.env['quick.paste.wizard']._get_llm_config()
        self.assertEqual(config['base_url'], 'https://llm.example.com/v1')
        self.assertEqual(config['api_key'], 'test-key')
        self.assertEqual(config['model'], 'test-model')
        self.assertTrue(config['prompt'])  # falls back to DEFAULT_PROMPT

    def test_get_llm_config_works_without_model(self):
        # The whole point of this session's fix: base_url + api_key alone
        # (no model) must be a valid, usable configuration.
        self._set_llm_config()
        config = self.env['quick.paste.wizard']._get_llm_config()
        self.assertEqual(config['base_url'], 'https://llm.example.com/v1')
        self.assertEqual(config['model'], '')

    def test_default_get_flags_setup_required_for_invoice_mode_when_unconfigured(self):
        wizard = self.env['quick.paste.wizard'].with_context(
            active_model=self.sale_order._name, active_id=self.sale_order.id,
            default_mode='invoice',
        ).create({})
        self.assertEqual(wizard.state, 'setup_required')

    def test_default_get_stays_input_for_invoice_mode_when_configured(self):
        self._set_llm_config()
        wizard = self.env['quick.paste.wizard'].with_context(
            active_model=self.sale_order._name, active_id=self.sale_order.id,
            default_mode='invoice',
        ).create({})
        self.assertEqual(wizard.state, 'input')

    def test_action_extract_invoice_without_config_flips_to_setup_required(self):
        wizard = self._make_wizard(self.sale_order, '')
        wizard.write({
            'mode': 'invoice',
            'invoice_filename': 'invoice.png',
            'invoice_file': b'ZmFrZSBpbWFnZSBieXRlcw==',
        })
        wizard.action_extract_invoice()
        self.assertEqual(wizard.state, 'setup_required')

    def test_action_extract_invoice_without_file_raises(self):
        self._set_llm_config()
        wizard = self._make_wizard(self.sale_order, '')
        wizard.mode = 'invoice'
        with self.assertRaises(Exception):
            wizard.action_extract_invoice()

    def test_action_extract_invoice_builds_preview_like_paste(self):
        self._set_llm_config()
        wizard = self._make_wizard(self.sale_order, '')
        wizard.write({
            'mode': 'invoice',
            'invoice_filename': 'invoice.png',
            'invoice_file': b'ZmFrZSBpbWFnZSBieXRlcw==',
        })
        canned_rows = [
            {'raw_line': 'Blue Widget x12', 'sku': 'ABC-123', 'name': 'Blue Widget', 'qty': 12},
            {'raw_line': 'Unknown Thing', 'sku': '', 'name': 'Completely Unrelated Thing', 'qty': 1},
        ]
        with patch(
            'odoo.addons.bs_smart_invoice_import.wizard.llm_client.extract_invoice_lines',
            return_value=canned_rows,
        ):
            wizard.action_extract_invoice()

        self.assertEqual(wizard.state, 'preview')
        self.assertEqual(len(wizard.preview_line_ids), 2)
        matched = wizard.preview_line_ids.filtered(lambda l: l.status == 'matched')
        self.assertEqual(matched.product_id, self.product_abc)
        self.assertEqual(matched.qty, 12)

    def test_action_extract_invoice_llm_error_becomes_user_error(self):
        self._set_llm_config()
        wizard = self._make_wizard(self.sale_order, '')
        wizard.write({
            'mode': 'invoice',
            'invoice_filename': 'invoice.png',
            'invoice_file': b'ZmFrZSBpbWFnZSBieXRlcw==',
        })
        with patch(
            'odoo.addons.bs_smart_invoice_import.wizard.llm_client.extract_invoice_lines',
            side_effect=Exception("boom"),
        ):
            # A generic Exception from a mocked call still propagates as an
            # error (only LLMError is caught and converted to UserError) --
            # this confirms the call site is actually reached.
            with self.assertRaises(Exception):
                wizard.action_extract_invoice()

    # ------------------------------------------------------------------
    # Upload hardening (size limit, malformed data, rate limiting)
    # ------------------------------------------------------------------
    def test_action_extract_invoice_oversized_file_raises(self):
        self._set_llm_config()
        wizard = self._make_wizard(self.sale_order, '')
        oversized = base64.b64encode(b'\0' * (MAX_INVOICE_FILE_SIZE + 1))
        wizard.write({
            'mode': 'invoice',
            'invoice_filename': 'invoice.png',
            'invoice_file': oversized,
        })
        with self.assertRaises(UserError):
            wizard.action_extract_invoice()

    def test_action_extract_invoice_malformed_base64_raises_user_error(self):
        self._set_llm_config()
        wizard = self._make_wizard(self.sale_order, '')
        wizard.write({
            'mode': 'invoice',
            'invoice_filename': 'invoice.png',
            'invoice_file': b'not-valid-base64!!!',
        })
        with self.assertRaises(UserError):
            wizard.action_extract_invoice()

    def test_llm_rate_limit_blocks_after_daily_cap(self):
        self._set_llm_config()
        self.env['ir.config_parameter'].sudo().set_param('bs_smart_invoice_import.llm_daily_limit', '2')
        Wizard = self.env['quick.paste.wizard']
        Wizard._check_llm_rate_limit()
        Wizard._check_llm_rate_limit()
        with self.assertRaises(UserError):
            Wizard._check_llm_rate_limit()

    def test_llm_rate_limit_disabled_when_zero(self):
        self._set_llm_config()
        self.env['ir.config_parameter'].sudo().set_param('bs_smart_invoice_import.llm_daily_limit', '0')
        Wizard = self.env['quick.paste.wizard']
        for _i in range(5):
            Wizard._check_llm_rate_limit()  # never raises

    def test_action_extract_invoice_blocked_by_rate_limit_before_network_call(self):
        self._set_llm_config()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('bs_smart_invoice_import.llm_daily_limit', '1')
        today_key = f'bs_smart_invoice_import.llm_usage.{self.env.uid}.{date.today().isoformat()}'
        params.set_param(today_key, '1')  # already at the cap

        wizard = self._make_wizard(self.sale_order, '')
        wizard.write({
            'mode': 'invoice',
            'invoice_filename': 'invoice.png',
            'invoice_file': b'ZmFrZSBpbWFnZSBieXRlcw==',
        })
        with patch(
            'odoo.addons.bs_smart_invoice_import.wizard.llm_client.extract_invoice_lines',
        ) as mocked_call:
            with self.assertRaises(UserError):
                wizard.action_extract_invoice()
            mocked_call.assert_not_called()

    # ------------------------------------------------------------------
    # UoM category safety net
    # ------------------------------------------------------------------
    def test_order_uom_id_falls_back_when_category_mismatched(self):
        weight_uom = self.env.ref('uom.product_uom_kgm')
        line = self.env['quick.paste.wizard.line'].create({
            'wizard_id': self._make_wizard(self.sale_order, '').id,
            'product_id': self.product_abc.id,
            'uom_id': weight_uom.id,  # wrong category for a generic product
            'qty': 1,
            'status': 'matched',
        })
        self.assertEqual(line._order_uom_id(), self.product_abc.uom_id)

    def test_order_uom_id_keeps_matching_category(self):
        wizard = self._make_wizard(self.sale_order, '')
        line = self.env['quick.paste.wizard.line'].create({
            'wizard_id': wizard.id,
            'product_id': self.product_abc.id,
            'uom_id': self.product_abc.uom_id.id,
            'qty': 1,
            'status': 'matched',
        })
        self.assertEqual(line._order_uom_id(), self.product_abc.uom_id)

    # ------------------------------------------------------------------
    # Embedding cache company scoping
    # ------------------------------------------------------------------
    def test_catalog_embedding_cache_key_includes_company(self):
        from odoo.addons.bs_smart_invoice_import.wizard import quick_paste_wizard as qpw
        other_company = self.env['res.company'].create({'name': "Other Co"})
        key_main = (self.env.cr.dbname, tuple(sorted(self.env.companies.ids)))
        key_other = (self.env.cr.dbname, tuple(sorted((self.env.company | other_company).ids)))
        self.assertNotEqual(key_main, key_other)
        # Sanity check the cache dict itself is never pre-seeded with a
        # cross-company key by unrelated test/module setup.
        self.assertNotIn(key_other, qpw._CATALOG_EMBEDDING_CACHE)

    def test_action_create_product_from_line_links_new_product(self):
        # Built directly rather than via action_parse: this tests
        # action_create_product_from_line in isolation, not the matcher's
        # unmatched/ambiguous/matched call (already covered by the
        # _match_product tests above).
        wizard = self._make_wizard(self.sale_order, '')
        line = self.env['quick.paste.wizard.line'].create({
            'wizard_id': wizard.id,
            'raw_line': 'Totally New Widget Nobody Has, 4',
            'name': 'Totally New Widget Nobody Has',
            'qty': 4,
            'status': 'unmatched',
        })
        line.action_create_product_from_line()

        self.assertEqual(line.status, 'matched')
        self.assertTrue(line.product_id)
        self.assertEqual(line.product_id.name, 'Totally New Widget Nobody Has')
        self.assertEqual(line.uom_id, line.product_id.uom_id)
