from unittest.mock import patch

from odoo.tests import tagged

from .common import EinvoiceArchiveCommon

FAKE_REFRESH_TOKEN = 'fake-refresh-token-xyz'
FAKE_ACCESS_TOKEN = 'fake-access-token-abc'


class DriveBackupCommon(EinvoiceArchiveCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env['bs.einvoice.drive.config'].create({'company_id': cls.env.company.id})
        cls.config._set_refresh_token(FAKE_REFRESH_TOKEN)
        cls.config.write({'folder_id': 'root-folder-id', 'status': 'connected', 'google_account_email': 'x@example.com'})


@tagged('post_install', '-at_install')
class TestDriveBackupQueueRetry(DriveBackupCommon):

    def test_retries_then_fails_after_cap(self):
        move = self.init_invoice('out_invoice', partner=self.partner_a, products=self.product_a, post=True)
        archive = self.env['bs.einvoice.archive'].search([('move_id', '=', move.id)])
        job = self.env['bs.einvoice.drive.upload.queue'].search([('archive_id', '=', archive.id)])
        self.assertTrue(job)
        self.assertEqual(archive.drive_backup_status, 'pending')

        with patch.object(type(self.config), '_access_token', side_effect=RuntimeError("upload boom")):
            for _i in range(5):
                job._process()

        self.assertEqual(job.state, 'failed')
        self.assertEqual(job.retry_count, 5)
        archive.invalidate_recordset()
        self.assertEqual(archive.drive_backup_status, 'failed')
        self.assertTrue(move.activity_ids.filtered(lambda a: 'Drive backup failed' in (a.summary or '')))
        failed_logs = archive.audit_log_ids.filtered(lambda log: log.action == 'drive_backup_failed')
        self.assertTrue(failed_logs)


@tagged('post_install', '-at_install')
class TestDriveBackupOptional(EinvoiceArchiveCommon):

    def test_no_config_gives_not_applicable_and_no_queue_entry(self):
        move = self.init_invoice('out_invoice', partner=self.partner_a, products=self.product_a, post=True)
        archive = self.env['bs.einvoice.archive'].search([('move_id', '=', move.id)])
        self.assertEqual(archive.drive_backup_status, 'not_applicable')
        self.assertFalse(self.env['bs.einvoice.drive.upload.queue'].search([('archive_id', '=', archive.id)]))

    def test_disconnected_config_gives_not_applicable(self):
        config = self.env['bs.einvoice.drive.config'].create({'company_id': self.env.company.id})
        config._set_refresh_token(FAKE_REFRESH_TOKEN)
        config.write({'status': 'connected'})
        with patch('odoo.addons.bs_einvoice_archive.models.bs_einvoice_drive_config.requests.post'):
            config._do_disconnect()

        move = self.init_invoice('out_invoice', partner=self.partner_a, products=self.product_a, post=True)
        archive = self.env['bs.einvoice.archive'].search([('move_id', '=', move.id)])
        self.assertEqual(archive.drive_backup_status, 'not_applicable')


@tagged('post_install', '-at_install')
class TestDriveTokenRefresh(DriveBackupCommon):

    def test_access_token_uses_stored_refresh_token_without_reauth(self):
        with patch.object(
            type(self.env['google.service']), '_refresh_google_token',
            return_value=(FAKE_ACCESS_TOKEN, 3600),
        ) as mocked:
            access_token = self.config._access_token()
        self.assertEqual(access_token, FAKE_ACCESS_TOKEN)
        mocked.assert_called_once_with('bs_einvoice_drive', FAKE_REFRESH_TOKEN)


@tagged('post_install', '-at_install')
class TestDriveTokenUndecryptable(DriveBackupCommon):

    def test_undecryptable_token_flips_config_to_error(self):
        # Simulate ir.config_parameter 'database.secret' having rotated
        # since the token was encrypted: the stored ciphertext no longer
        # decrypts with the current key.
        self.config.write({'refresh_token_encrypted': 'not-a-valid-fernet-token'})
        token = self.config._get_refresh_token()
        self.assertFalse(token)
        self.assertEqual(self.config.status, 'error')
        self.assertTrue(self.config.last_error)


@tagged('post_install', '-at_install')
class TestDriveTokenRedaction(DriveBackupCommon):

    def test_token_never_appears_in_stored_error_or_audit_log(self):
        move = self.init_invoice('out_invoice', partner=self.partner_a, products=self.product_a, post=True)
        archive = self.env['bs.einvoice.archive'].search([('move_id', '=', move.id)])
        job = self.env['bs.einvoice.drive.upload.queue'].search([('archive_id', '=', archive.id)])

        leaking_error = RuntimeError(f"401 Unauthorized, token={FAKE_ACCESS_TOKEN} rejected")
        with patch.object(type(self.config), '_access_token', return_value=FAKE_ACCESS_TOKEN), \
             patch.object(type(job), '_upload_attachment', side_effect=leaking_error):
            job._process()

        self.assertNotIn(FAKE_ACCESS_TOKEN, job.last_error or '')
        self.assertNotIn(FAKE_REFRESH_TOKEN, job.last_error or '')
        self.assertIn('REDACTED', job.last_error or '')
