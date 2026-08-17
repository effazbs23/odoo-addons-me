/** @odoo-module **/

import {registry} from "@web/core/registry";
import {Component} from "@odoo/owl";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {getContrastingTextColor} from "./statusbar_color_utils";

/**
 * Compact, read-only preview of a rule's statusbar for use as a list
 * view column - shows each state colored with its Default Color so you
 * can see the result at a glance without opening the rule. No
 * click-to-edit here; that lives in the full statusbar_state_editor on
 * the form.
 */
export class StatusbarStatePreview extends Component {
    static template = "custom_statusbar.StatusbarStatePreview";
    static props = {...standardFieldProps};

    get records() {
        const list = this.props.record.data[this.props.name];
        return [...list.records].sort(
            (a, b) => (a.data.sequence || 0) - (b.data.sequence || 0)
        );
    }

    getButtonStyle(record) {
        const color = record.data.default_color;
        if (!color) {
            return "";
        }
        const textColor = getContrastingTextColor(color);
        return `background-color: ${color} !important; border-color: ${color} !important; color: ${textColor} !important;`;
    }
}

export const statusbarStatePreviewField = {
    component: StatusbarStatePreview,
    supportedTypes: ["one2many"],
};

registry.category("fields").add("statusbar_state_preview", statusbarStatePreviewField);
