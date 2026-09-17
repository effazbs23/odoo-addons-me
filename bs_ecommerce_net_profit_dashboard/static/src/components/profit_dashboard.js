/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

const CHANNEL_COLORS = { shopify: "#22c55e", amazon: "#f59e0b", woo: "#a855f7", pos: "#3b82f6" };

export class BsProfitDashboard extends Component {
    static template = "bs_ecommerce_net_profit_dashboard.BsProfitDashboard";

    setup() {
        this.orm = useService("orm");
        this.state = useState({ metrics: {}, loading: true });
        this.barCanvas = useRef("barChart");
        this.donutCanvas = useRef("donutChart");

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            this.state.metrics = await this.orm.call("bs.ecom.profit.engine", "get_net_margins", []);
            this.state.loading = false;
        });

        onMounted(() => this.renderCharts());
    }

    renderCharts() {
        const channels = this.state.metrics.channels || [];
        if (!channels.length || !this.barCanvas.el) {
            return;
        }
        const labels = channels.map((c) => c.label);
        const colors = channels.map((c) => CHANNEL_COLORS[c.code]);

        new Chart(this.barCanvas.el, {
            type: "bar",
            data: {
                labels,
                datasets: [
                    { label: "Net Profit", data: channels.map((c) => c.net_profit), backgroundColor: "#3b82f6" },
                ],
            },
            options: { responsive: true, plugins: { legend: { display: false } } },
        });

        new Chart(this.donutCanvas.el, {
            type: "doughnut",
            data: {
                labels,
                datasets: [{ data: channels.map((c) => c.gross_revenue), backgroundColor: colors }],
            },
            options: { responsive: true },
        });
    }
}
registry.category("actions").add("bs_ecommerce_net_profit_dashboard_action", BsProfitDashboard);
