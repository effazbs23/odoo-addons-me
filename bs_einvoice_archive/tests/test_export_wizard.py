import base64
import json
import zipfile
from io import BytesIO

from odoo.tests import tagged

from .common import EinvoiceArchiveCommon


@tagged('post_install', '-at_install')
class TestExportWizard(EinvoiceArchiveCommon):

    def test_export_zip_has_expected_manifest_for_date_range(self):
        move = self.init_invoice('out_invoice', partner=self.partner_a, products=self.product_a, post=True)
        archive = self.env['bs.einvoice.archive'].search([('move_id', '=', move.id)])
        archived_date = archive.archived_on.date()

        wizard = self.env['bs.einvoice.archive.export.wizard'].create({
            'date_from': archived_date,
            'date_to': archived_date,
        })
        result = wizard.action_export()

        attachment_id = int(result['url'].split('/web/content/')[1].split('?')[0])
        attachment = self.env['ir.attachment'].browse(attachment_id)
        with zipfile.ZipFile(BytesIO(base64.b64decode(attachment.datas))) as zf:
            self.assertIn('manifest.json', zf.namelist())
            self.assertIn('audit_log.csv', zf.namelist())
            manifest = json.loads(zf.read('manifest.json'))

        self.assertEqual(len(manifest), 1)
        self.assertEqual(manifest[0]['Invoice Number'], move.name)
        self.assertEqual(manifest[0]['Checksum'], archive.checksum)

        exported_logs = archive.audit_log_ids.filtered(lambda log: log.action == 'exported')
        self.assertTrue(exported_logs)

    def test_export_excludes_records_outside_date_range(self):
        move = self.init_invoice('out_invoice', partner=self.partner_a, products=self.product_a, post=True)
        self.env['bs.einvoice.archive'].search([('move_id', '=', move.id)])

        wizard = self.env['bs.einvoice.archive.export.wizard'].create({
            'date_from': '2000-01-01',
            'date_to': '2000-01-02',
        })
        with self.assertRaises(Exception):
            wizard.action_export()
