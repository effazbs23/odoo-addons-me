/** @odoo-module **/

import { Component, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useDraggable } from "@web/core/utils/draggable";

function clamp(value) {
    return Math.max(0, Math.min(100, value));
}

// Drag-to-position picker for the logo and watermark, shown over a small demo
// invoice mockup in Settings > PDF Branding. Nominally bound to
// pdf_logo_position_x (any float field works, supportedTypes: ["float"]),
// but reads/writes all four position fields directly off the record so one
// widget can drive both handles -- see res_company.py's pdf_logo_position_x/y
// and pdf_watermark_position_x/y, used verbatim (as a % of the printable
// page area) by the report overlay template that actually renders them.
export class PdfBrandingPositionPicker extends Component {
    static template = "bs_pdf_branding_kit.PositionPicker";
    static props = { ...standardFieldProps };

    setup() {
        this.canvasRef = useRef("canvas");
        let target = null;
        let startX = 0;
        let startY = 0;
        let startFieldX = 0;
        let startFieldY = 0;

        useDraggable({
            ref: this.canvasRef,
            elements: ".bs_pbk_handle",
            onDragStart: ({ element, x, y }) => {
                target = element.dataset.target;
                startX = x;
                startY = y;
                startFieldX = target === "logo" ? this.logoX : this.watermarkX;
                startFieldY = target === "logo" ? this.logoY : this.watermarkY;
            },
            onDrag: ({ x, y }) => {
                const rect = this.canvasRef.el.getBoundingClientRect();
                const newX = clamp(startFieldX + ((x - startX) / rect.width) * 100);
                const newY = clamp(startFieldY + ((y - startY) / rect.height) * 100);
                if (target === "logo") {
                    this.props.record.update({ pdf_logo_position_x: newX, pdf_logo_position_y: newY });
                } else {
                    this.props.record.update({ pdf_watermark_position_x: newX, pdf_watermark_position_y: newY });
                }
            },
        });
    }

    get logoX() {
        return this.props.record.data.pdf_logo_position_x;
    }
    get logoY() {
        return this.props.record.data.pdf_logo_position_y;
    }
    get watermarkX() {
        return this.props.record.data.pdf_watermark_position_x;
    }
    get watermarkY() {
        return this.props.record.data.pdf_watermark_position_y;
    }
    get diagonal() {
        return this.props.record.data.pdf_watermark_diagonal;
    }
    get watermarkType() {
        return this.props.record.data.pdf_watermark_type;
    }
    get watermarkText() {
        return this.props.record.data.pdf_watermark_text;
    }
    get hasWatermark() {
        return Boolean(this.watermarkType) && this.watermarkType !== "none";
    }
    get logoDataUrl() {
        const b64 = this.props.record.data.pdf_print_logo;
        return b64 ? `data:image/png;base64,${b64}` : false;
    }
    get watermarkImageUrl() {
        const b64 = this.props.record.data.pdf_watermark_image;
        return b64 ? `data:image/png;base64,${b64}` : false;
    }
    get logoStyle() {
        return `left: ${this.logoX}%; top: ${this.logoY}%; transform: translate(-50%, -50%);`;
    }
    get watermarkStyle() {
        const rotate = this.diagonal ? " rotate(-30deg)" : "";
        return `left: ${this.watermarkX}%; top: ${this.watermarkY}%; transform: translate(-50%, -50%)${rotate};`;
    }
}

export const pdfBrandingPositionPicker = {
    component: PdfBrandingPositionPicker,
    supportedTypes: ["float"],
};

registry.category("fields").add("bs_pdf_branding_position_picker", pdfBrandingPositionPicker);
