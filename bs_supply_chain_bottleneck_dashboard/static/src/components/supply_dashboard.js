/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class BsSupplyDashboard extends Component {
    static template = "bs_supply_chain_bottleneck_dashboard.BsSupplyDashboard";

    setup() {
        this.orm = useService("orm");
        this.state = useState({ vendors: [], loading: true });
        onWillStart(async () => {
            const vendors = await this.orm.searchRead(
                "res.partner",
                [["supplier_rank", ">", 0]],
                ["name", "bs_vendor_delay_index"]
            );
            vendors.sort((a, b) => b.bs_vendor_delay_index - a.bs_vendor_delay_index);
            this.state.vendors = vendors;
            this.state.totalSuppliers = vendors.length;
            const late = vendors.filter((v) => v.bs_vendor_delay_index > 0);
            this.state.avgDelay = late.length
                ? (late.reduce((s, v) => s + v.bs_vendor_delay_index, 0) / late.length).toFixed(1)
                : "0.0";
            this.state.latePct = vendors.length
                ? Math.round((late.length / vendors.length) * 100)
                : 0;
            this.state.loading = false;
        });
    }

    statusClass(days) {
        if (days >= 4) return "bg-danger";
        if (days >= 2) return "bg-warning";
        return "bg-success";
    }
}
registry.category("actions").add("bs_supply_chain_bottleneck_dashboard_action", BsSupplyDashboard);
