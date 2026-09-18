import json
from urllib.parse import quote

from odoo import http
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestXlsxRoute(HttpCase):
    """The XLSX plumbing is a controller plus a client-side action handler.

    Rendering is covered by the flow tests; what is exercised here is the round trip
    the web client actually performs: POST /report/download with the URL the handler
    builds, which has to come back as a spreadsheet attachment.
    """

    XLSX_MIMETYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    def setUp(self):
        super().setUp()
        self.authenticate('admin', 'admin')

    def _download(self, url):
        return self.url_open('/report/download', data={
            'data': json.dumps([url, 'xlsx']),
            'context': json.dumps({}),
            'csrf_token': http.Request.csrf_token(self),
        })

    def test_wizard_style_download_returns_a_workbook(self):
        """No record ids: the filters ride in the query string, as the JS handler builds it."""
        options = quote(json.dumps({'year': 2025, 'site_ids': []}))
        context = quote(json.dumps({}))
        response = self._download(
            '/report/xlsx/bs_amc_management.report_amc_schedule?options=%s&context=%s'
            % (options, context))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], self.XLSX_MIMETYPE)
        self.assertIn('attachment', response.headers['Content-Disposition'])
        self.assertIn('.xlsx', response.headers['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'PK'), "an xlsx file is a zip archive")

    def test_unknown_report_name_is_not_served(self):
        response = self.url_open('/report/xlsx/bs_amc_management.does_not_exist')
        self.assertNotEqual(response.status_code, 200)

    def test_pdf_downloads_still_reach_core(self):
        """The override must delegate every report type it does not handle.

        A bogus PDF report is enough: core catches the lookup failure and answers with
        its own error payload. What matters is that the request is handled at all -- a
        broken delegation would blow up in this module instead.
        """
        response = self.url_open('/report/download', data={
            'data': json.dumps(['/report/pdf/account.report_invoice/999999', 'qweb-pdf']),
            'context': json.dumps({}),
            'csrf_token': http.Request.csrf_token(self),
        })
        self.assertNotEqual(response.status_code, 500)
        self.assertNotIn(self.XLSX_MIMETYPE, response.headers.get('Content-Type', ''))
