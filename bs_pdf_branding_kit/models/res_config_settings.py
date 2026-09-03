from odoo import fields, models

from .res_company import pdf_page_size_mm, qrcode_data_uri


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pdf_print_logo = fields.Binary(related='company_id.pdf_print_logo', readonly=False)
    pdf_watermark_type = fields.Selection(related='company_id.pdf_watermark_type', readonly=False)
    pdf_watermark_text = fields.Char(related='company_id.pdf_watermark_text', readonly=False)
    pdf_watermark_image = fields.Binary(related='company_id.pdf_watermark_image', readonly=False)
    pdf_watermark_opacity = fields.Float(related='company_id.pdf_watermark_opacity', readonly=False)
    pdf_watermark_diagonal = fields.Boolean(related='company_id.pdf_watermark_diagonal', readonly=False)
    pdf_logo_position_x = fields.Float(related='company_id.pdf_logo_position_x', readonly=False)
    pdf_logo_position_y = fields.Float(related='company_id.pdf_logo_position_y', readonly=False)
    pdf_watermark_position_x = fields.Float(related='company_id.pdf_watermark_position_x', readonly=False)
    pdf_watermark_position_y = fields.Float(related='company_id.pdf_watermark_position_y', readonly=False)
    pdf_qrcode_enabled = fields.Boolean(related='company_id.pdf_qrcode_enabled', readonly=False)
    pdf_qrcode_source = fields.Selection(related='company_id.pdf_qrcode_source', readonly=False)
    pdf_qrcode_custom_url = fields.Char(related='company_id.pdf_qrcode_custom_url', readonly=False)

    def action_preview_quotation(self):
        return self._pdf_branding_preview('quotation')

    def action_preview_invoice(self):
        return self._pdf_branding_preview('invoice')

    def action_preview_delivery_slip(self):
        return self._pdf_branding_preview('delivery_slip')

    def action_preview_purchase_order(self):
        return self._pdf_branding_preview('purchase_order')

    def _pdf_branding_preview(self, report_type):
        self.ensure_one()
        opacity = max(0.0, min(100.0, self.pdf_watermark_opacity))
        qrcode_value = False
        if self.pdf_qrcode_enabled:
            qrcode_value = (
                self.pdf_qrcode_custom_url if self.pdf_qrcode_source == 'custom_url'
                # No real record exists yet in a live preview, so a portal link can't
                # be resolved -- show a representative placeholder instead.
                else 'https://example.com/my/invoices/preview'
            )
        page_width_mm, page_height_mm = pdf_page_size_mm(self.company_id)
        branding = {
            'logo': self.pdf_print_logo or self.company_id.logo,
            'print_logo': self.pdf_print_logo,
            'logo_position_x': self.pdf_logo_position_x,
            'logo_position_y': self.pdf_logo_position_y,
            'watermark_type': self.pdf_watermark_type,
            'watermark_text': self.pdf_watermark_text,
            'watermark_image': self.pdf_watermark_image,
            'watermark_opacity': opacity,
            'watermark_diagonal': self.pdf_watermark_diagonal,
            'watermark_position_x': self.pdf_watermark_position_x,
            'watermark_position_y': self.pdf_watermark_position_y,
            'qrcode_data_uri': qrcode_data_uri(self.env, qrcode_value) if qrcode_value else False,
            'page_width_mm': page_width_mm,
            'page_height_mm': page_height_mm,
        }
        return self.env['bs.pdf.branding.preview.wizard'].action_preview(report_type, branding, self.company_id)
