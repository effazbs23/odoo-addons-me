/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";

/**
 * Shown whenever the parser's confidence is below threshold. Pre-filled
 * with whatever the parser DID resolve (this.props.partialSpec) so the
 * user only has to fix the ambiguous parts, not start from scratch.
 * This is deliberately just Odoo's own pivot/graph mental model (pick a
 * model, pick dimensions, pick a measure, pick a chart) — the parser is a
 * shortcut on top of a UI that already works standalone.
 */
export class GuidedForm extends Component {
    static template = "bs_smart_kpi_dashboard.GuidedForm";
    static props = ["partialSpec", "options", "onSubmit"];

    setup() {
        const partial = this.props.partialSpec || {};
        this.state = useState({
            model: partial.model || (this.props.options[0] && this.props.options[0].model),
            groupby: partial.groupby || [],
            measure: (partial.measures && partial.measures[0]) || null,
            chart_type: partial.chart_type || "bar",
        });
    }

    get currentModelOptions() {
        return this.props.options.find((o) => o.model === this.state.model) || {};
    }

    toggleGroupby(fieldName) {
        const idx = this.state.groupby.indexOf(fieldName);
        if (idx === -1) {
            this.state.groupby.push(fieldName);
        } else {
            this.state.groupby.splice(idx, 1);
        }
    }

    onSubmit() {
        const spec = {
            model: this.state.model,
            groupby: this.state.groupby,
            measures: this.state.measure ? [this.state.measure] : [],
            domain: [],
            chart_type: this.state.chart_type,
            limit: null,
            orderby: null,
        };
        this.props.onSubmit(spec);
    }
}
