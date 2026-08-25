from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import EinvoiceArchiveCommon


@tagged('post_install', '-at_install')
class TestArchiveImmutability(EinvoiceArchiveCommon):

    def test_archive_created_on_post(self):
        move = self.init_invoice('out_invoice', partner=self.partner_a, products=self.product_a, post=True)
        archive = self.env['bs.einvoice.archive'].search([('move_id', '=', move.id)])
        self.assertTrue(archive)
        self.assertEqual(archive.move_name, move.name)
        self.assertEqual(archive.state, 'active')
        self.assertEqual(archive.invoice_type, 'standard')

    def test_write_blocks_immutable_fields(self):
        move = self.init_invoice('out_invoice', partner=self.partner_a, products=self.product_a, post=True)
        archive = self.env['bs.einvoice.archive'].search([('move_id', '=', move.id)])
        with self.assertRaises(UserError):
            archive.write({'checksum': 'tampered'})

    def test_write_allows_mutable_fields(self):
        move = self.init_invoice('out_invoice', partner=self.partner_a, products=self.product_a, post=True)
        archive = self.env['bs.einvoice.archive'].search([('move_id', '=', move.id)])
        archive.write({'asp_status': 'accepted'})
        self.assertEqual(archive.asp_status, 'accepted')

    def test_unlink_always_blocked(self):
        move = self.init_invoice('out_invoice', partner=self.partner_a, products=self.product_a, post=True)
        archive = self.env['bs.einvoice.archive'].search([('move_id', '=', move.id)])
        with self.assertRaises(UserError):
            archive.unlink()

    def test_archiving_disabled_skips_archive_creation(self):
        self.env.company.einvoice_archive_enabled = False
        move = self.init_invoice('out_invoice', partner=self.partner_a, products=self.product_a, post=True)
        archive = self.env['bs.einvoice.archive'].search([('move_id', '=', move.id)])
        self.assertFalse(archive)

    def test_standalone_credit_note_posts_without_original_archive(self):
        # A credit note with no reversed_entry_id (e.g. a standalone refund,
        # or one reversing an invoice posted before this module existed) has
        # no original archive to link to. Posting it must still succeed --
        # _cron_flag_broken_corrections is what surfaces the missing link,
        # not a hard constraint on create().
        move = self.init_invoice('out_refund', partner=self.partner_a, products=self.product_a, post=True)
        archive = self.env['bs.einvoice.archive'].search([('move_id', '=', move.id)])
        self.assertTrue(archive)
        self.assertEqual(archive.invoice_type, 'credit_note')
        self.assertFalse(archive.original_archive_id)
