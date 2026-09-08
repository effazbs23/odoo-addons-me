from odoo.tests import tagged

from .common import TraceabilityCommon


@tagged('post_install', '-at_install')
class TestTraceExport(TraceabilityCommon):

    def _searched_wizard(self):
        raw = self._make_product('Raw Export')
        finished = self._make_product('Finished Export')
        raw_lot = self._receive_from_vendor(raw, 'RAWE', 5)
        bom = self._make_bom(finished, [(raw, 1)])
        fin_lot, _ = self._produce(bom, finished, {raw: raw_lot}, 'FINE', qty=1)
        self._deliver_to_customer(finished, fin_lot, 1)

        wizard = self.env['bs.trace.lookup.wizard'].create({'lot_id': fin_lot.id, 'direction': 'both'})
        wizard.action_search()
        return wizard

    def test_search_populates_summary_and_chain(self):
        wizard = self._searched_wizard()
        self.assertTrue(wizard.has_result)
        self.assertIn('FINE', wizard.summary_text)
        self.assertIn('FINE', wizard.chain_html)

    def test_export_logs_event(self):
        wizard = self._searched_wizard()
        log_count_before = self.env['bs.traceability.export.log'].search_count([])
        wizard.action_export_pdf()
        logs = self.env['bs.traceability.export.log'].search([('lot_id', '=', wizard.lot_id.id)])
        self.assertEqual(self.env['bs.traceability.export.log'].search_count([]), log_count_before + 1)
        self.assertEqual(logs.exported_by, self.env.user)
        self.assertEqual(logs.direction, 'both')

    def test_export_renders_pdf(self):
        wizard = self._searched_wizard()
        # PDF generation is short-circuited to HTML in test mode unless
        # explicitly forced - force it here since we're specifically testing
        # that the wkhtmltopdf pipeline renders without error.
        pdf_content, report_type = self.env['ir.actions.report'].with_context(
            force_report_rendering=True)._render_qweb_pdf(
            'plain_language_batch_traceability.bs_trace_export_report_document', [wizard.id])
        self.assertEqual(report_type, 'pdf')
        self.assertTrue(pdf_content)
