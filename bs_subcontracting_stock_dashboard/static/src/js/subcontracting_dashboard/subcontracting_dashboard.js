/** @odoo-module **/

import { loadBundle } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { SelectMenu } from "@web/core/select_menu/select_menu";
import { useService } from "@web/core/utils/hooks";
import { KeepLast } from "@web/core/utils/concurrency";
import { Layout } from "@web/search/layout";
import { Component, onWillStart, useEffect, useRef, useState } from "@odoo/owl";

const PALETTE = ["#3B82F6", "#22D3EE", "#A78BFA", "#FB923C", "#2DD4BF", "#F472B6", "#94A3B8"];

export class SubcontractingStockDashboard extends Component {
    static template = "bs_subcontracting_stock_dashboard.Dashboard";
    static components = { Layout, SelectMenu };
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.keepLast = new KeepLast();
        this.donutRef = useRef("donutCanvas");
        this.barRef = useRef("barCanvas");
        this.donutChart = null;
        this.barChart = null;
        this.mode = this.props.action.params?.mode || "dashboard";

        this.state = useState({
            partnerId: 0,
            locationId: 0,
            partners: [],
            locations: [],
            summary: null,
            split: null,
            bySubcontractor: [],
            breakdown: [],
            aging: [],
            valueReport: null,
            loading: true,
        });

        onWillStart(async () => {
            const [partners, locations] = await Promise.all([
                this.orm.searchRead("res.partner", [["property_stock_subcontractor", "!=", false]], ["id", "name"]),
                this.orm.searchRead("stock.location", [], ["id", "display_name"], { limit: 200 }),
            ]);
            this.state.partners = partners;
            this.state.locations = locations;
            await loadBundle("web.chartjs_lib");
        });

        useEffect(
            () => { this.fetchData(); },
            () => [this.state.partnerId, this.state.locationId]
        );

        useEffect(
            () => { this.renderCharts(); return () => { this.donutChart?.destroy(); this.barChart?.destroy(); }; },
            () => [this.state.split, this.state.bySubcontractor]
        );
    }

    get display() { return { controlPanel: {} }; }
    get title() {
        return {
            dashboard: "Subcontractor-Owned Stock Dashboard",
            per_subcontractor: "Per-Subcontractor Breakdown",
            aging_report: "Aging Report",
            value_report: "Value Report",
        }[this.mode];
    }
    get subtitle() {
        return { dashboard: "Overview of company vs. subcontractor-owned stock at subcontracting locations." }[this.mode] || "";
    }
    choices(list, allLabel, labelField = "name") {
        return [{ value: 0, label: allLabel }, ...list.map((r) => ({ value: r.id, label: r[labelField] }))];
    }
    get partnerChoices() { return this.choices(this.state.partners, "All Subcontractors"); }
    get locationChoices() { return this.choices(this.state.locations, "All Locations", "display_name"); }

    get baseDomain() {
        const domain = [];
        if (this.state.partnerId) domain.push(["partner_id", "=", this.state.partnerId]);
        if (this.state.locationId) domain.push(["location_id", "=", this.state.locationId]);
        return domain;
    }

    async fetchData() {
        this.state.loading = true;
        const domain = this.baseDomain;
        const orm = this.orm;
        const mode = this.mode;
        const data = await this.keepLast.add((async () => {
            const result = {};
            result.summary = await orm.call("subcontracting.stock.report", "get_dashboard_summary", [domain]);
            if (mode === "dashboard") {
                result.split = await orm.call("subcontracting.stock.report", "get_ownership_split", [domain]);
                result.bySubcontractor = await orm.call("subcontracting.stock.report", "get_stock_by_subcontractor", [domain]);
            } else if (mode === "per_subcontractor") {
                result.breakdown = await orm.call("subcontracting.stock.report", "get_breakdown_by_subcontractor", [domain]);
            } else if (mode === "aging_report") {
                result.aging = await orm.call("subcontracting.stock.report", "get_aging_rows", [domain]);
            } else if (mode === "value_report") {
                result.valueReport = await orm.call("subcontracting.stock.report", "get_value_report", [domain]);
            }
            return result;
        })());
        this.state.summary = data.summary;
        this.state.split = data.split || null;
        this.state.bySubcontractor = data.bySubcontractor || [];
        this.state.breakdown = data.breakdown || [];
        this.state.aging = data.aging || [];
        this.state.valueReport = data.valueReport || null;
        this.state.loading = false;
    }

    bucketLabel(bucket) {
        return { b1: "0-7 days", b2: "8-14 days", b3: "15-30 days", b4: "30+ days" }[bucket] || bucket;
    }

    renderCharts() {
        this.donutChart?.destroy();
        this.barChart?.destroy();

        if (this.donutRef.el && this.state.split && (this.state.split.company || this.state.split.subcontractor)) {
            this.donutChart = new Chart(this.donutRef.el, {
                type: "doughnut",
                data: {
                    labels: ["Company-Owned", "Subcontractor-Owned"],
                    datasets: [{ data: [this.state.split.company, this.state.split.subcontractor], backgroundColor: ["#8E59FD", "#22D3EE"], borderWidth: 2, borderColor: "#fff" }],
                },
                options: { cutout: "65%", plugins: { legend: { display: true, position: "bottom" } }, maintainAspectRatio: false },
            });
        }
        if (this.barRef.el && this.state.bySubcontractor.length) {
            this.barChart = new Chart(this.barRef.el, {
                type: "bar",
                data: {
                    labels: this.state.bySubcontractor.map((r) => r.partner),
                    datasets: [{ data: this.state.bySubcontractor.map((r) => r.quantity), backgroundColor: PALETTE, borderRadius: 4 }],
                },
                options: { plugins: { legend: { display: false } }, maintainAspectRatio: false, scales: { y: { beginAtZero: true } } },
            });
        }
    }

    exportXlsx = () => {
        const params = new URLSearchParams({ mode: this.mode, domain: JSON.stringify(this.baseDomain) });
        window.location = `/bs_subcontracting_stock_dashboard/export.xlsx?${params}`;
    };
}

registry.category("actions").add("bs_subcontracting_stock_dashboard", SubcontractingStockDashboard);
