from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Regression coverage for res.config.settings integration.

    A ``config_parameter`` field only supports a narrow set of types
    (boolean/integer/float/char/selection/many2one/datetime -- see
    ``odoo/addons/base/models/res_config.py::_get_classified_fields``); a
    ``Text`` field (originally used for ``quick_paste_llm_prompt`` before it
    was moved to its own wizard) blew up with a server error the moment the
    Settings form was opened, but that error only surfaces via
    ``default_get``/``onchange`` on ``res.config.settings`` itself --
    calling ``ir.config_parameter.sudo().set_param`` directly (as
    ``tests/test_wizard.py`` does) never exercises that code path. These
    tests call the Settings model the way the actual Settings form does.
    """

    def test_default_get_does_not_raise(self):
        Settings = self.env['res.config.settings']
        res = Settings.default_get([
            'quick_paste_llm_base_url', 'quick_paste_llm_api_key', 'quick_paste_llm_model',
        ])
        self.assertIn('quick_paste_llm_base_url', res)

    def test_onchange_does_not_raise(self):
        Settings = self.env['res.config.settings']
        values = Settings.new(Settings.default_get(
            ['quick_paste_llm_base_url', 'quick_paste_llm_api_key', 'quick_paste_llm_model'],
        ))
        result = values.onchange({}, [], {
            'quick_paste_llm_base_url': '1',
            'quick_paste_llm_api_key': '1',
            'quick_paste_llm_model': '1',
        })
        self.assertIn('value', result)

    def test_saved_values_round_trip(self):
        self.env['res.config.settings'].create({
            'quick_paste_llm_base_url': 'https://llm.example.com/v1',
            'quick_paste_llm_api_key': 'secret-key',
            'quick_paste_llm_model': 'test-model',
        }).execute()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        self.assertEqual(get_param('bs_smart_invoice_import.llm_base_url'), 'https://llm.example.com/v1')
        self.assertEqual(get_param('bs_smart_invoice_import.llm_model'), 'test-model')

    def test_model_is_not_required_to_save(self):
        # Groq (and other providers) may not need a model name pinned on
        # our side -- base_url + api_key alone must be a valid, saveable
        # configuration.
        self.env['res.config.settings'].create({
            'quick_paste_llm_base_url': 'https://api.groq.com/openai/v1',
            'quick_paste_llm_api_key': 'secret-key',
        }).execute()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        self.assertEqual(get_param('bs_smart_invoice_import.llm_base_url'), 'https://api.groq.com/openai/v1')
        self.assertFalse(get_param('bs_smart_invoice_import.llm_model'))


@tagged('post_install', '-at_install')
class TestLLMPromptWizard(TransactionCase):

    def test_default_get_prefills_default_prompt(self):
        from odoo.addons.bs_smart_invoice_import.wizard import llm_client
        res = self.env['quick.paste.llm.prompt.wizard'].default_get(['prompt'])
        self.assertEqual(res.get('prompt'), llm_client.DEFAULT_PROMPT)

    def test_default_get_prefills_saved_prompt(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'bs_smart_invoice_import.llm_prompt', 'Custom saved prompt',
        )
        res = self.env['quick.paste.llm.prompt.wizard'].default_get(['prompt'])
        self.assertEqual(res.get('prompt'), 'Custom saved prompt')

    def test_action_save_persists_to_config_parameter(self):
        wizard = self.env['quick.paste.llm.prompt.wizard'].create({'prompt': 'A new custom prompt'})
        wizard.action_save()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        self.assertEqual(get_param('bs_smart_invoice_import.llm_prompt'), 'A new custom prompt')
