/** @odoo-module **/

import {registry} from "@web/core/registry";
import {Component, useState} from "@odoo/owl";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {usePopover} from "@web/core/popover/popover_hook";
import {StatusbarColorPopover, PRESET_COLORS} from "./color_picker_field";
import {getContrastingTextColor} from "./statusbar_color_utils";

/**
 * Renders the discovered states as one mini statusbar preview per
 * (model, field) instead of a plain table: click a state's button to
 * select it, then pick its Default/In State colors and toggle it on
 * from the side panel. Every change is written straight to the
 * underlying record, so the preview button updates instantly.
 */
export class StatusbarStateEditor extends Component {
    static template = "custom_statusbar.StatusbarStateEditor";
    static props = {...standardFieldProps};

    setup() {
        this.state = useState({selectedId: null});
        this.popover = usePopover(StatusbarColorPopover, {position: "bottom-start"});
    }

    get list() {
        return this.props.record.data[this.props.name];
    }

    get groups() {
        const groupsByKey = new Map();
        for (const record of this.list.records) {
            const key = `${record.data.model_name}:${record.data.field_name}`;
            if (!groupsByKey.has(key)) {
                groupsByKey.set(key, {
                    key,
                    label:
                        record.data.field_name === "state"
                            ? record.data.model_name
                            : `${record.data.model_name} (${record.data.field_name})`,
                    records: [],
                });
            }
            groupsByKey.get(key).records.push(record);
        }
        const groups = [...groupsByKey.values()];
        for (const group of groups) {
            group.records.sort((a, b) => (a.data.sequence || 0) - (b.data.sequence || 0));
        }
        groups.sort((a, b) => (a.label > b.label ? 1 : a.label < b.label ? -1 : 0));
        return groups;
    }

    isSelected(record) {
        return this.state.selectedId === record.id;
    }

    selectRecord(record) {
        this.state.selectedId = this.isSelected(record) ? null : record.id;
    }

    getSelectedInGroup(group) {
        return group.records.find((record) => this.isSelected(record)) || null;
    }

    /**
     * Live preview of how this button would actually render: "in state"
     * color while selected (pretending this is the record's current
     * state), "default" color otherwise - same rule the real patched
     * StatusBarField uses.
     */
    getButtonStyle(record) {
        const color = this.isSelected(record)
            ? record.data.in_state_color
            : record.data.default_color;
        if (!color) {
            return "";
        }
        const textColor = getContrastingTextColor(color);
        return `background-color: ${color} !important; border-color: ${color} !important; color: ${textColor} !important;`;
    }

    getSwatchStyle(record, fieldName) {
        const color = record.data[fieldName];
        return color ? `background-color: ${color} !important` : "";
    }

    openColorPicker(ev, record, fieldName) {
        this.popover.open(ev.currentTarget, {
            presets: PRESET_COLORS,
            currentColor: record.data[fieldName] || "",
            selectColor: (color) => {
                record.update({[fieldName]: color});
                this.popover.close();
            },
        });
    }

    toggleEnabled(record) {
        record.update({enabled: !record.data.enabled});
    }
}

export const statusbarStateEditorField = {
    component: StatusbarStateEditor,
    supportedTypes: ["one2many"],
};

registry.category("fields").add("statusbar_state_editor", statusbarStateEditorField);
