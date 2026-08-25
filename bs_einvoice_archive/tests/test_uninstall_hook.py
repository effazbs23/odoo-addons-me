from odoo.exceptions import UserError
from odoo.tests import tagged

from .. import uninstall_hook
from .common import EinvoiceArchiveCommon


@tagged('post_install', '-at_install')
class TestUninstallHook(EinvoiceArchiveCommon):

    def test_blocks_when_unexpired_records_exist(self):
        self.init_invoice('out_invoice', partner=self.partner_a, products=self.product_a, post=True)
        with self.assertRaises(UserError):
            uninstall_hook(self.env)

    def test_allows_when_no_unexpired_records_remain(self):
        move = self.init_invoice('out_invoice', partner=self.partner_a, products=self.product_a, post=True)
        archive = self.env['bs.einvoice.archive'].search([('move_id', '=', move.id)])
        archive.write({'state': 'disposed'})
        uninstall_hook(self.env)  # should not raise
