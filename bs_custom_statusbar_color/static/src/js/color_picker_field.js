/** @odoo-module **/

import {registry} from "@web/core/registry";
import {Component, useState} from "@odoo/owl";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {usePopover} from "@web/core/popover/popover_hook";

export const PRESET_COLORS = [
    "#08AF64",
    "#ED8B00",
    "#CF1F3C",
    "#1F77B4",
    "#9467BD",
    "#8C564B",
    "#E377C2",
    "#7F7F7F",
    "#BCBD22",
    "#17BECF",
];

const HEX_COLOR_PATTERN = /^#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})$/;

export class StatusbarColorPopover extends Component {
    static template = "custom_statusbar.StatusbarColorPopover";
    static props = {
        presets: {type: Array},
        currentColor: {type: String},
        selectColor: {type: Function},
    };

    setup() {
        this.state = useState({hexInput: this.props.currentColor || ""});
    }

    /**
     * The native <input type="color"> requires a valid hex value at all
     * times, but we don't want to persist a fake default just to satisfy
     * that. This is display-only and never written to the record.
     */
    get nativeInputValue() {
        return this.props.currentColor || "#CCCCCC";
    }

    get isValidHex() {
        return HEX_COLOR_PATTERN.test(this.state.hexInput.trim());
    }

    onHexInput(ev) {
        this.state.hexInput = ev.target.value;
    }

    onHexKeydown(ev) {
        if (ev.key === "Enter") {
            this.applyHex();
        }
    }

    applyHex() {
        const value = this.state.hexInput.trim();
        if (!HEX_COLOR_PATTERN.test(value)) {
            return;
        }
        this.props.selectColor(value.startsWith("#") ? value : `#${value}`);
    }
}

export class StatusbarColorPickerField extends Component {
    static template = "custom_statusbar.StatusbarColorPickerField";
    static props = {...standardFieldProps};

    setup() {
        this.presets = PRESET_COLORS;
        // usePopover renders in a portal attached to <body> and repositions
        // itself to stay inside the viewport, so it is never clipped or
        // misaligned by a table row/cell (unlike a manually absolutely
        // positioned <div>).
        this.popover = usePopover(StatusbarColorPopover, {
            position: "bottom-start",
        });
    }

    get value() {
        return this.props.record.data[this.props.name] || "";
    }

    get hasColor() {
        return Boolean(this.value);
    }

    /**
     * Computed directly in JS (rather than string-interpolated in the
     * template) and bound via t-att-style, so the swatch reliably shows
     * the record's actual stored color on every render - not just while
     * that row happens to be focused/being edited.
     */
    get swatchStyle() {
        return this.hasColor ? `background-color: ${this.value} !important` : "";
    }

    async setColor(color) {
        await this.props.record.update({[this.props.name]: color});
    }

    togglePicker(ev) {
        if (this.popover.isOpen) {
            this.popover.close();
            return;
        }
        this.popover.open(ev.currentTarget, {
            presets: this.presets,
            currentColor: this.value,
            selectColor: (color) => {
                this.setColor(color);
                this.popover.close();
            },
        });
    }
}

export const statusbarColorPickerField = {
    component: StatusbarColorPickerField,
    supportedTypes: ["char"],
};

registry.category("fields").add("statusbar_color_picker", statusbarColorPickerField);
