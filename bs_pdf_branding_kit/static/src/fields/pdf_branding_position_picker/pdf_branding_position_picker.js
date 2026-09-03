/** @odoo-module **/

import { Component, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

function clampPct(value) {
    return Math.max(0, Math.min(100, value));
}

// Matches _SCALE_MIN/_SCALE_MAX in models/res_company.py.
function clampScale(value) {
    return Math.max(25, Math.min(300, value));
}

// Base (100%-scale) box sizes as a % of the canvas, matched to the SCSS
// defaults these replace (bs_pbk_handle_logo/bs_pbk_handle_watermark).
const LOGO_BASE_WIDTH_PCT = 22;
const LOGO_BASE_HEIGHT_PCT = 10;
const WATERMARK_BASE_WIDTH_PCT = 60;
const WATERMARK_BASE_FONT_PX = 13;

// Drag-to-position-and-resize picker for the logo and watermark, shown over a
// small demo invoice mockup in Settings > PDF Branding. Nominally bound to
// pdf_logo_position_x (any float field works, supportedTypes: ["float"]),
// but reads/writes all six logo/watermark fields directly off the record so
// one widget can drive both handles -- see res_company.py's
// pdf_logo_position_x/y, pdf_watermark_position_x/y and pdf_logo_scale/
// pdf_watermark_scale, used verbatim by the report overlay template that
// actually renders them.
//
// Deliberately plain pointerdown/move/up listeners instead of
// @web/core/utils/draggable's useDraggable: that hook hardcodes
// followCursor (not exposed as a param at all in this Odoo version), which
// physically moves the dragged element to position:fixed pixel coordinates
// during the drag, then -- on pointerup -- restores the element's pre-drag
// `style` attribute verbatim (dom.addStyle/saveAttribute), clobbering
// whatever this component had already re-rendered from the record update.
// The two owners of `style` (the hook's followCursor and our own
// record-driven t-att-style) fight and the handle visually snaps back after
// every drag. Tracking the pointer ourselves avoids a second owner entirely.
export class PdfBrandingPositionPicker extends Component {
    static template = "bs_pdf_branding_kit.PositionPicker";
    static props = { ...standardFieldProps };

    setup() {
        this.canvasRef = useRef("canvas");
    }

    _trackPointer(onMove) {
        const onUp = () => {
            window.removeEventListener("pointermove", onMove);
            window.removeEventListener("pointerup", onUp);
        };
        window.addEventListener("pointermove", onMove);
        window.addEventListener("pointerup", onUp);
    }

    onHandlePointerDown(ev, target) {
        if (ev.button !== 0) {
            return;
        }
        ev.preventDefault();
        const startX = ev.clientX;
        const startY = ev.clientY;
        const startFieldX = target === "logo" ? this.logoX : this.watermarkX;
        const startFieldY = target === "logo" ? this.logoY : this.watermarkY;
        this._trackPointer((moveEv) => {
            const rect = this.canvasRef.el.getBoundingClientRect();
            const newX = clampPct(startFieldX + ((moveEv.clientX - startX) / rect.width) * 100);
            const newY = clampPct(startFieldY + ((moveEv.clientY - startY) / rect.height) * 100);
            if (target === "logo") {
                this.props.record.update({ pdf_logo_position_x: newX, pdf_logo_position_y: newY });
            } else {
                this.props.record.update({ pdf_watermark_position_x: newX, pdf_watermark_position_y: newY });
            }
        });
    }

    onResizePointerDown(ev, target) {
        if (ev.button !== 0) {
            return;
        }
        ev.preventDefault();
        // Without this, the pointerdown also bubbles to the parent handle's
        // own listener and starts a position drag at the same time.
        ev.stopPropagation();
        const box = ev.currentTarget.closest(".bs_pbk_handle").getBoundingClientRect();
        const center = { x: box.left + box.width / 2, y: box.top + box.height / 2 };
        const startDist = Math.max(1, Math.hypot(ev.clientX - center.x, ev.clientY - center.y));
        const startScale = target === "logo" ? this.logoScale : this.watermarkScale;
        this._trackPointer((moveEv) => {
            const dist = Math.hypot(moveEv.clientX - center.x, moveEv.clientY - center.y);
            const newScale = clampScale(startScale * (dist / startDist));
            if (target === "logo") {
                this.props.record.update({ pdf_logo_scale: newScale });
            } else {
                this.props.record.update({ pdf_watermark_scale: newScale });
            }
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
    get logoScale() {
        return this.props.record.data.pdf_logo_scale || 100;
    }
    get watermarkScale() {
        return this.props.record.data.pdf_watermark_scale || 100;
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
        const w = (LOGO_BASE_WIDTH_PCT * this.logoScale) / 100;
        const h = (LOGO_BASE_HEIGHT_PCT * this.logoScale) / 100;
        return `left: ${this.logoX}%; top: ${this.logoY}%; width: ${w}%; height: ${h}%; transform: translate(-50%, -50%);`;
    }
    get watermarkStyle() {
        const rotate = this.diagonal ? " rotate(-30deg)" : "";
        const w = (WATERMARK_BASE_WIDTH_PCT * this.watermarkScale) / 100;
        const fontSize = (WATERMARK_BASE_FONT_PX * this.watermarkScale) / 100;
        return `left: ${this.watermarkX}%; top: ${this.watermarkY}%; width: ${w}%; font-size: ${fontSize}px; transform: translate(-50%, -50%)${rotate};`;
    }
}

export const pdfBrandingPositionPicker = {
    component: PdfBrandingPositionPicker,
    supportedTypes: ["float"],
};

registry.category("fields").add("bs_pdf_branding_position_picker", pdfBrandingPositionPicker);
