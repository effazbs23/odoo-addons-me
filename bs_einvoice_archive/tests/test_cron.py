from odoo.tests import tagged

from .common import EinvoiceArchiveCommon


@tagged('post_install', '-at_install')
class TestHealthCheckCron(EinvoiceArchiveCommon):

    def test_cron_flags_posted_invoice_missing_archive(self):
        move = self.init_invoice('out_invoice', partner=self.partner_a, products=self.product_a, post=True)
        archive = self.env['bs.einvoice.archive'].search([('move_id', '=', move.id)])
        # Simulate the archive having gone missing out-of-band (raw SQL, since
        # unlink() on this model always raises by design).
        self.env.cr.execute("DELETE FROM bs_einvoice_archive WHERE id = %s", (archive.id,))
        move.invalidate_recordset()

        flagged = self.env['bs.einvoice.archive']._cron_flag_missing_archives()
        self.assertIn(move, flagged)
        self.assertTrue(move.activity_ids)

        # A second run on the same still-broken record must not pile on a
        # second identical activity.
        self.env['bs.einvoice.archive']._cron_flag_missing_archives()
        self.assertEqual(len(move.activity_ids), 1)

    def test_cron_flags_broken_correction_link(self):
        original_move = self.init_invoice('out_invoice', partner=self.partner_a, products=self.product_a, post=True)
        original_archive = self.env['bs.einvoice.archive'].search([('move_id', '=', original_move.id)])

        refund_moves = original_move._reverse_moves(cancel=False)
        refund_moves.action_post()
        refund_archive = self.env['bs.einvoice.archive'].search([('move_id', 'in', refund_moves.ids)])
        self.assertEqual(refund_archive.invoice_type, 'credit_note')
        self.assertEqual(refund_archive.original_archive_id, original_archive)

        # Simulate a broken link (e.g. the original archive got wiped
        # out-of-band) via raw SQL, bypassing the append-only write() guard.
        self.env.cr.execute(
            "UPDATE bs_einvoice_archive SET original_archive_id = NULL WHERE id = %s",
            (refund_archive.id,),
        )
        refund_archive.invalidate_recordset()

        broken = self.env['bs.einvoice.archive']._cron_flag_broken_corrections()
        self.assertIn(refund_archive, broken)

    def test_cron_promotes_expired_records_to_eligible(self):
        move = self.init_invoice('out_invoice', partner=self.partner_a, products=self.product_a, post=True)
        archive = self.env['bs.einvoice.archive'].search([('move_id', '=', move.id)])
        self.env.cr.execute(
            "UPDATE bs_einvoice_archive SET retention_expiry_date = %s WHERE id = %s",
            ('2000-01-01', archive.id),
        )
        archive.invalidate_recordset()

        expired = self.env['bs.einvoice.archive']._cron_update_disposal_eligibility()
        self.assertIn(archive, expired)
        self.assertEqual(archive.state, 'eligible_for_disposal')
