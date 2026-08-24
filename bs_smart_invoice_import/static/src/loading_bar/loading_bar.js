/** @odoo-module **/

import { registry } from "@web/core/registry";
import { rpcBus } from "@web/core/network/rpc";
import { useBus } from "@web/core/utils/hooks";
import { Component, useState } from "@odoo/owl";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

// Only track this wizard's own long-running actions -- not every RPC that
// happens to fire while the dialog is open (e.g. unrelated background
// polling), so the bar only appears for the specific calls it's meant to
// give feedback on (Parse / Extract / Add Lines to Order, all of which can
// take a noticeable moment: LLM extraction in particular is a real network
// round-trip, not just a DB write).
const TRACKED_METHODS = new Set(["action_parse", "action_extract_invoice", "action_confirm"]);

export class QuickPasteLoadingBar extends Component {
    static template = "bs_smart_invoice_import.LoadingBar";
    static props = { ...standardWidgetProps };

    setup() {
        this.state = useState({ active: false });
        this.pendingIds = new Set();
        useBus(rpcBus, "RPC:REQUEST", (ev) => this.onRequest(ev.detail));
        useBus(rpcBus, "RPC:RESPONSE", (ev) => this.onResponse(ev.detail));
    }

    isTracked(detail) {
        const params = detail && detail.data && detail.data.params;
        return Boolean(
            params && params.model === "quick.paste.wizard" && TRACKED_METHODS.has(params.method)
        );
    }

    onRequest(detail) {
        if (!this.isTracked(detail)) {
            return;
        }
        this.pendingIds.add(detail.data.id);
        this.state.active = true;
    }

    onResponse(detail) {
        if (!this.isTracked(detail)) {
            return;
        }
        this.pendingIds.delete(detail.data.id);
        this.state.active = this.pendingIds.size > 0;
    }
}

export const quickPasteLoadingBar = {
    component: QuickPasteLoadingBar,
};

registry.category("view_widgets").add("quick_paste_loading_bar", quickPasteLoadingBar);
