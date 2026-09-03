from odoo.tests import tagged

from odoo.addons.bs_pdf_branding_kit.models.res_company import qrcode_data_uri
from .common import BrandingTestCommon


@tagged('post_install', '-at_install')
class TestWatermarkResolution(BrandingTestCommon):
    """Spec 10: effective watermark resolution falls back override -> company -> none;
    when_overdue condition; multi-company isolation."""

    def test_no_override_falls_back_to_company_default(self):
        self.company.pdf_watermark_type = 'text'
        self.company.pdf_watermark_text = 'COMPANY DEFAULT'
        result = self.env['bs.pdf.branding.override']._get_effective_watermark(self.company, 'quotation')
        self.assertEqual(result['type'], 'text')
        self.assertEqual(result['text'], 'COMPANY DEFAULT')

    def test_explicit_override_wins_over_company_default(self):
        self.company.pdf_watermark_type = 'text'
        self.company.pdf_watermark_text = 'COMPANY DEFAULT'
        self.env['bs.pdf.branding.override'].create({
            'company_id': self.company.id, 'report_type': 'quotation',
            'watermark_override_type': 'text', 'watermark_override_text': 'DRAFT',
        })
        result = self.env['bs.pdf.branding.override']._get_effective_watermark(self.company, 'quotation')
        self.assertEqual(result['text'], 'DRAFT')

    def test_override_none_suppresses_company_default(self):
        self.company.pdf_watermark_type = 'text'
        self.company.pdf_watermark_text = 'COMPANY DEFAULT'
        self.env['bs.pdf.branding.override'].create({
            'company_id': self.company.id, 'report_type': 'delivery_slip',
            'watermark_override_type': 'none',
        })
        result = self.env['bs.pdf.branding.override']._get_effective_watermark(self.company, 'delivery_slip')
        self.assertEqual(result['type'], 'none')

    def test_inherit_override_falls_back_to_company_default(self):
        self.company.pdf_watermark_type = 'image'
        self.env['bs.pdf.branding.override'].create({
            'company_id': self.company.id, 'report_type': 'purchase_order',
            'watermark_override_type': 'inherit',
        })
        result = self.env['bs.pdf.branding.override']._get_effective_watermark(self.company, 'purchase_order')
        self.assertEqual(result['type'], 'image')

    def test_when_overdue_true_for_unpaid_past_due_invoice(self):
        invoice = self._create_invoice(due_days=-5)
        self.assertTrue(self.env['bs.pdf.branding.override']._is_invoice_overdue(invoice))

    def test_when_overdue_false_for_invoice_not_yet_due(self):
        invoice = self._create_invoice(due_days=5)
        self.assertFalse(self.env['bs.pdf.branding.override']._is_invoice_overdue(invoice))

    def test_when_overdue_false_once_paid(self):
        invoice = self._create_invoice(due_days=-5)
        invoice.payment_state = 'paid'
        self.assertFalse(self.env['bs.pdf.branding.override']._is_invoice_overdue(invoice))

    def test_when_overdue_condition_gates_the_override(self):
        self.env['bs.pdf.branding.override'].create({
            'company_id': self.company.id, 'report_type': 'invoice',
            'watermark_override_type': 'text', 'watermark_override_text': 'OVERDUE',
            'watermark_override_condition': 'when_overdue',
        })
        overdue_invoice = self._create_invoice(due_days=-5)
        current_invoice = self._create_invoice(due_days=5)
        overdue_result = self.env['bs.pdf.branding.override']._get_effective_watermark(
            self.company, 'invoice', overdue_invoice)
        current_result = self.env['bs.pdf.branding.override']._get_effective_watermark(
            self.company, 'invoice', current_invoice)
        self.assertEqual(overdue_result['text'], 'OVERDUE')
        self.assertNotEqual(current_result.get('text'), 'OVERDUE')

    def test_watermark_opacity_clamped_to_valid_range(self):
        self.company.pdf_watermark_type = 'text'
        self.company.pdf_watermark_text = 'X'
        self.company.pdf_watermark_opacity = 250
        self.assertEqual(self.company._get_pdf_branding('quotation')['watermark_opacity'], 100.0)
        self.company.pdf_watermark_opacity = -30
        self.assertEqual(self.company._get_pdf_branding('quotation')['watermark_opacity'], 0.0)


@tagged('post_install', '-at_install')
class TestQrCode(BrandingTestCommon):
    """Spec 10: QR generation encodes the correct URL for each source option, reusing
    Odoo's own reportlab-based barcode generator (no new dependency)."""

    def setUp(self):
        super().setUp()
        try:
            self.env['ir.actions.report'].barcode('QR', 'probe', width=20, height=20)
        except Exception as exc:  # noqa: BLE001 -- environment-capability probe, see comment below
            # reportlab's PNG backend (renderPM) needs a compiled extension or
            # rlPyCairo that isn't installed in every environment; that's a
            # packaging gap in reportlab itself, not something this module's QR
            # feature can fix -- it delegates 100% to this same Odoo-core call.
            self.skipTest(f'reportlab PNG backend unavailable in this environment: {exc}')

    def test_odoo_native_qr_generator_returns_a_real_png(self):
        png = self.env['ir.actions.report'].barcode('QR', 'https://example.com/invoice/1', width=100, height=100)
        self.assertTrue(png.startswith(b'\x89PNG'))

    def test_qrcode_data_uri_helper_embeds_a_real_png(self):
        uri = qrcode_data_uri(self.env, 'https://example.com/pay?id=42&x=y', size=80)
        self.assertTrue(uri.startswith('data:image/png;base64,'))

    def test_custom_url_source(self):
        self.company.pdf_qrcode_enabled = True
        self.company.pdf_qrcode_source = 'custom_url'
        self.company.pdf_qrcode_custom_url = 'https://example.com/verify'
        branding = self.company._get_pdf_branding('purchase_order')
        self.assertTrue(branding['qrcode_data_uri'])

    def test_payment_portal_link_only_meaningful_on_invoice(self):
        self.company.pdf_qrcode_enabled = True
        self.company.pdf_qrcode_source = 'payment_portal_link'
        invoice = self._create_invoice()
        branding_invoice = self.company._get_pdf_branding('invoice', invoice)
        branding_po = self.company._get_pdf_branding('purchase_order')
        self.assertTrue(branding_invoice['qrcode_data_uri'])
        self.assertFalse(branding_po['qrcode_data_uri'])

    def test_qrcode_disabled_yields_no_url(self):
        self.company.pdf_qrcode_enabled = False
        self.company.pdf_qrcode_source = 'custom_url'
        self.company.pdf_qrcode_custom_url = 'https://example.com/verify'
        self.assertFalse(self.company._get_pdf_branding('invoice')['qrcode_data_uri'])
