from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

from ..models.bs_easy_smtp_preset import PROVIDER_SELECTION


@tagged('post_install', '-at_install')
class TestBsEasySmtp(TransactionCase):

    def setUp(self):
        super().setUp()
        # start each test from a clean slate so default_get's "pick the existing
        # active server" logic is deterministic regardless of other demo data
        self.env['ir.mail_server'].search([]).unlink()

    def test_onchange_provider_autofills_from_preset(self):
        """Unit: selecting each non-custom provider preset auto-fills host/port/encryption."""
        preset_model = self.env['bs.easy.smtp.preset']
        for provider, _label in PROVIDER_SELECTION:
            if provider == 'custom':
                continue
            preset = preset_model.search([('provider', '=', provider)], limit=1)
            self.assertTrue(preset, f"missing preset data for provider {provider}")
            wizard = self.env['bs.easy.smtp.wizard'].new({'provider': provider})
            wizard._onchange_provider()
            self.assertEqual(wizard.smtp_host, preset.default_host)
            self.assertEqual(wizard.smtp_port, preset.default_port)
            self.assertEqual(wizard.smtp_encryption, preset.default_encryption)
            self.assertEqual(wizard.credential_note, preset.credential_note)

    def test_onchange_custom_provider_leaves_fields_untouched(self):
        """Unit: Custom must never force preset values onto host/port/encryption (spec section 9)."""
        wizard = self.env['bs.easy.smtp.wizard'].new({
            'provider': 'custom', 'smtp_host': 'relay.internal', 'smtp_port': 2525,
        })
        wizard._onchange_provider()
        self.assertEqual(wizard.smtp_host, 'relay.internal')
        self.assertEqual(wizard.smtp_port, 2525)

    def test_error_decoder_categories(self):
        """Unit: pattern matching classifies one sample per category, falls back gracefully."""
        decode = self.env['ir.mail_server']._bs_easy_smtp_decode_error

        self.assertIn("app password", decode("Username and Password not accepted").lower())
        self.assertIn("firewall", decode("[Errno 110] Connection timed out").lower())
        self.assertIn("ssl", decode("SSL: WRONG_VERSION_NUMBER").lower())
        self.assertIn("rejected sending", decode("Relay access denied").lower())

        unrecognized = "Some completely novel error the mapping table has never seen"
        fallback = decode(unrecognized)
        self.assertIn(unrecognized, fallback)

    def test_test_send_never_persists_before_save(self):
        """Integration: test-send never creates/updates ir.mail_server before explicit save."""
        mail_server = self.env['ir.mail_server']
        wizard = self.env['bs.easy.smtp.wizard'].create({
            'provider': 'gmail',
            'smtp_user': 'me@example.com',
            'smtp_pass': 'secret',
            'test_email_to': 'test@example.com',
            'state': 'credentials',
        })
        wizard.action_test_send()
        self.assertEqual(mail_server.search_count([]), 0)
        # Odoo disables real SMTP I/O while running tests, so send_email() is a no-op success
        self.assertEqual(wizard.test_result_status, 'success')

    def test_save_requires_a_successful_test(self):
        wizard = self.env['bs.easy.smtp.wizard'].create({
            'provider': 'gmail',
            'test_email_to': 'test@example.com',
        })
        self.assertEqual(wizard.test_result_status, 'untested')
        with self.assertRaises(UserError):
            wizard.action_save()
        self.assertEqual(self.env['ir.mail_server'].search_count([]), 0)

    def test_save_creates_server_when_none_exists(self):
        wizard = self.env['bs.easy.smtp.wizard'].create({
            'provider': 'gmail',
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'smtp_encryption': 'starttls',
            'smtp_user': 'me@example.com',
            'smtp_pass': 'secret',
            'test_email_to': 'test@example.com',
            'test_result_status': 'success',
        })
        wizard.action_save()
        servers = self.env['ir.mail_server'].search([])
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers.smtp_host, 'smtp.gmail.com')

    def test_default_get_prefill_survives_client_onchange(self):
        """Regression: re-running the wizard must show the existing server's real config, not a
        preset's -- the web client always fires the on-load onchange for a field with a default
        (here 'provider'), which used to clobber the restored host/port/encryption."""
        self.env['ir.mail_server'].create({
            'name': 'Existing', 'smtp_host': 'relay.example.com',
            'smtp_port': 2525, 'smtp_encryption': 'ssl', 'smtp_user': 'ops@example.com',
        })
        defaults = self.env['bs.easy.smtp.wizard'].default_get(
            ['provider', 'smtp_host', 'smtp_port', 'smtp_encryption', 'smtp_user', 'existing_mail_server_id'])
        self.assertEqual(defaults['provider'], 'custom')
        wizard = self.env['bs.easy.smtp.wizard'].new(defaults)
        wizard._onchange_provider()  # what the web client fires automatically on load
        self.assertEqual(wizard.smtp_host, 'relay.example.com')
        self.assertEqual(wizard.smtp_port, 2525)
        self.assertEqual(wizard.smtp_encryption, 'ssl')

    def test_rerunning_wizard_updates_existing_server_not_duplicate(self):
        """Integration: re-running the wizard with an active server updates, never duplicates.
        Also serves as the regression check that an unrelated server is left untouched."""
        mail_server = self.env['ir.mail_server']
        primary = mail_server.create({
            'name': 'Primary', 'smtp_host': 'old.example.com',
            'smtp_port': 587, 'smtp_encryption': 'starttls', 'sequence': 5,
        })
        secondary = mail_server.create({
            'name': 'Secondary', 'smtp_host': 'keep.example.com',
            'smtp_port': 25, 'smtp_encryption': 'none', 'sequence': 10,
        })

        wizard = self.env['bs.easy.smtp.wizard'].create({
            'provider': 'gmail',
            'smtp_user': 'me@example.com',
            'test_email_to': 'test@example.com',
        })
        self.assertEqual(wizard.existing_mail_server_id, primary)

        wizard.write({'test_result_status': 'success'})
        wizard.action_save()

        self.assertEqual(mail_server.search_count([]), 2, "must update, not duplicate")
        self.assertEqual(primary.smtp_user, 'me@example.com')
        self.assertEqual(secondary.smtp_host, 'keep.example.com', "unrelated server must be untouched")
