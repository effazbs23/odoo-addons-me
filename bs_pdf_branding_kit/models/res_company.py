import base64
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)

# Report types where a "payment portal link" QR source is meaningful.
_QR_PORTAL_LINK_REPORT_TYPES = ('invoice',)


def qrcode_data_uri(env, value, size=120):
    """Inline data: URI for Odoo's own QR generator (reportlab, via
    ir.actions.report.barcode -- reused as-is elsewhere in Odoo core, e.g.
    l10n_es_edi_tbai's invoice QR; no new QR library needed for this module).

    Generated server-side and embedded inline rather than left as a
    /report/barcode/... URL for wkhtmltopdf to fetch: on a single-worker
    instance, wkhtmltopdf's own callback request for that URL can never be
    served because the one worker is already blocked waiting on wkhtmltopdf,
    deadlocking the render. Inline avoids that request entirely.

    Returns False (never raises) if the underlying generator itself fails --
    e.g. a broken reportlab/renderPM install -- so one broken QR code degrades
    to "no QR on this document" rather than taking down the whole report,
    consistent with how a missing logo/watermark image is handled.
    """
    try:
        png = env['ir.actions.report'].barcode('QR', value, width=size, height=size)
    except Exception:
        _logger.warning('bs_pdf_branding_kit: QR code generation failed for value %r', value, exc_info=True)
        return False
    return 'data:image/png;base64,%s' % base64.b64encode(png).decode()


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Edge case (spec 9): multi-company isolation. Plain per-record fields with no
    # `default=` pointing at another company/record, so a new company created after
    # install starts with none of these set -- never inherits another company's
    # uploaded logo/watermark image.
    pdf_print_logo = fields.Binary(
        string='Print Logo',
        help='Print-specific logo used on PDF report headers. Falls back to the company logo when unset.',
    )
    pdf_watermark_type = fields.Selection(
        [('none', 'None'), ('text', 'Text'), ('image', 'Image')],
        string='Watermark Type', default='none', required=True,
    )
    pdf_watermark_text = fields.Char(string='Watermark Text')
    pdf_watermark_image = fields.Binary(string='Watermark Image')
    pdf_watermark_opacity = fields.Float(string='Watermark Opacity (%)', default=15.0)
    pdf_watermark_position = fields.Selection(
        [('center', 'Center'), ('diagonal', 'Diagonal'), ('top_right', 'Top Right')],
        string='Watermark Position', default='diagonal', required=True,
    )
    pdf_qrcode_enabled = fields.Boolean(string='Enable QR Code')
    pdf_qrcode_source = fields.Selection(
        [('payment_portal_link', 'Payment Portal Link'), ('custom_url', 'Custom URL')],
        string='QR Code Source', default='custom_url',
    )
    pdf_qrcode_custom_url = fields.Char(string='QR Code Custom URL')

    def _get_pdf_branding(self, report_type, record=None):
        """Effective branding settings for one report render.

        `record` is the document being rendered (e.g. an account.move for the
        invoice report), used for the when_overdue watermark condition and to
        resolve the payment portal link QR source. May be a falsy/empty
        recordset for the live preview (no real document to link to).
        """
        self.ensure_one()
        watermark = self.env['bs.pdf.branding.override']._get_effective_watermark(self, report_type, record)
        opacity = max(0.0, min(100.0, self.pdf_watermark_opacity))

        qrcode_value = False
        if self.pdf_qrcode_enabled:
            if self.pdf_qrcode_source == 'payment_portal_link':
                if report_type in _QR_PORTAL_LINK_REPORT_TYPES and record and record._name == 'account.move':
                    qrcode_value = record.get_portal_url()
            else:
                qrcode_value = self.pdf_qrcode_custom_url

        return {
            'logo': self.pdf_print_logo or self.logo,
            'print_logo': self.pdf_print_logo,
            'watermark_type': watermark['type'],
            'watermark_text': watermark['text'],
            'watermark_image': watermark['image'],
            'watermark_opacity': opacity,
            'watermark_position': self.pdf_watermark_position,
            'qrcode_data_uri': qrcode_data_uri(self.env, qrcode_value) if qrcode_value else False,
        }
