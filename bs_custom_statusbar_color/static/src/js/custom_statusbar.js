/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {StatusBarField} from "@web/views/fields/statusbar/statusbar_field";
import {useService} from "@web/core/utils/hooks";
import {getContrastingTextColor} from "./statusbar_color_utils";

patch(StatusBarField.prototype, {
    setup() {
        super.setup();
        this.statusbarColor = useService("statusbar_color");
    },

    /**
     * Looks up the configured color for this button. Uses the
     * "in state" color when the record is currently in this exact
     * state (the highlighted/disabled button), and the "default" color
     * for every other step (past or upcoming). Returns null when
     * nothing has been explicitly enabled/colored for it.
     */
    getCustomColor(item) {
        const {record, name} = this.props;
        if (item.isSelected) {
            return this.statusbarColor.getInStateColor(record.resModel, name, item.value);
        }
        return this.statusbarColor.getDefaultColor(record.resModel, name, item.value);
    },

    /**
     * Extra class toggled on only when this button has a custom color,
     * so the SCSS can also color the connector "arrow" pseudo-element
     * (which inline styles can't reach) via the CSS variable set below.
     */
    getItemClassName(item) {
        return this.getCustomColor(item) ? " o_statusbar_custom_colored" : "";
    },

    /**
     * Inline style applied to a statusbar button. Only ever returns
     * something when the user has explicitly enabled a color for this
     * exact state - every other statusbar in the system keeps Odoo's
     * stock appearance untouched. Also forces a contrasting text color
     * so the label stays legible against whatever background was picked,
     * and exposes the color as a CSS variable so the connector arrow
     * (::after) can pick it up too.
     */
    getItemStyle(item) {
        const color = this.getCustomColor(item);
        if (!color) {
            return "";
        }
        const textColor = getContrastingTextColor(color);
        return (
            `--o-statusbar-custom-color: ${color}; ` +
            `background-color: ${color} !important; ` +
            `border-color: ${color} !important; ` +
            `color: ${textColor} !important; ` +
            "opacity: 1 !important;"
        );
    },
});
