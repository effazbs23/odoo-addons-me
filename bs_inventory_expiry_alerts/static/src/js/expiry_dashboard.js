/** @odoo-module **/

import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {Component, onWillStart, onMounted, useState} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";

export class ExpiryDashboard extends Component {
    static template = "bs_inventory_expiry_alerts.ExpiryDashboard";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            loading: true,
            kpis: {expiring_soon: 0, at_risk: 0, safe: 0, value_at_risk: 0},
            currencySymbol: "$",
            bucketLabels: [],
            bucketCounts: [],
            byWarehouse: [],
            totalLots: 0,
            tableRows: [],
            markdownCount: 0,
            transferCount: 0,
        });

        onWillStart(async () => {
            await this._loadData();
        });

        onMounted(() => {
            if (!this.state.loading) {
                this._renderCharts();
            }
        });
    }

    async _loadData() {
        this.state.loading = true;
        const result = await this.orm.call("stock.expiry.dashboard.line", "get_dashboard_data", []);
        this.state.kpis = result.kpis;
        this.state.currencySymbol = result.currency_symbol;
        this.state.bucketLabels = result.bucket_labels;
        this.state.bucketCounts = result.bucket_counts;
        this.state.byWarehouse = result.by_warehouse;
        this.state.totalLots = result.total_lots;
        this.state.tableRows = result.table_rows;
        this.state.markdownCount = result.markdown_count;
        this.state.transferCount = result.transfer_count;
        this.state.loading = false;
        setTimeout(() => this._renderCharts(), 50);
    }

    async _onRefresh() {
        await this._loadData();
    }

    _renderCharts() {
        if (!window.Chart) return;
        this._renderBucketChart();
        this._renderWarehouseChart();
    }

    _renderBucketChart() {
        const canvas = document.getElementById("bsExpiryBucketChart");
        if (!canvas) return;
        if (this.bucketChart) this.bucketChart.destroy();
        this.bucketChart = new Chart(canvas.getContext("2d"), {
            type: "bar",
            data: {
                labels: this.state.bucketLabels,
                datasets: [{
                    data: this.state.bucketCounts,
                    backgroundColor: ["#DC3545", "#F0AD4E", "#FFC107", "#5CB85C", "#4472C4"],
                    borderRadius: 4,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {legend: {display: false}},
                scales: {y: {beginAtZero: true, ticks: {precision: 0}}},
            },
        });
    }

    _renderWarehouseChart() {
        const canvas = document.getElementById("bsExpiryWarehouseChart");
        if (!canvas) return;
        if (this.warehouseChart) this.warehouseChart.destroy();
        const data = this.state.byWarehouse;
        this.warehouseChart = new Chart(canvas.getContext("2d"), {
            type: "doughnut",
            data: {
                labels: data.map((d) => d.name),
                datasets: [{
                    data: data.map((d) => d.count),
                    backgroundColor: data.map((d) => d.color),
                    borderWidth: 2,
                    borderColor: "#fff",
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "65%",
                plugins: {legend: {display: false}},
            },
        });
    }

    _openFiltered(domain, name) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: "stock.expiry.dashboard.line",
            view_mode: "list",
            views: [[false, "list"]],
            domain,
            target: "current",
        });
    }

    onViewRow(quantId) {
        this._openFiltered([["id", "=", quantId]], _t("Lot Detail"));
    }

    onViewSuggestions() {
        this._openFiltered([["suggested_action", "=", "markdown"]], _t("Markdown / Promotion Candidates"));
    }

    onViewTransfers() {
        this._openFiltered([["suggested_action", "=", "transfer"]], _t("Internal Transfer Candidates"));
    }
}

registry.category("actions").add("bs_inventory_expiry_alerts.dashboard", ExpiryDashboard);
