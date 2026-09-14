/** @odoo-module **/

import { loadBundle } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { KeepLast } from "@web/core/utils/concurrency";
import { Layout } from "@web/search/layout";
import { Component, onWillStart, useEffect, useRef, useState } from "@odoo/owl";

const PALETTE = ["#00A0DB", "#2ECC71", "#A78BFA", "#FB923C", "#F472B6", "#94A3B8"];

export class DowntimeImpactDashboard extends Component {
    static template = "bs_maintenance_downtime_impact_report.Dashboard";
    static components = { Layout };
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.keepLast = new KeepLast();
        this.comboRef = useRef("comboCanvas");
        this.donutRef = useRef("donutCanvas");
        this.barRef = useRef("barCanvas");
        this.comboChart = null;
        this.donutChart = null;
        this.barChart = null;

        this.state = useState({
            dateFrom: "",
            dateTo: "",
            summary: null,
            trend: null,
            byWorkcenter: [],
            topEquipment: [],
            details: [],
            recentEvents: [],
            loading: true,
        });

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
        });

        useEffect(
            () => { this.fetchData(); },
            () => [this.state.dateFrom, this.state.dateTo]
        );

        useEffect(
            () => { this.renderCharts(); return () => { this.comboChart?.destroy(); this.donutChart?.destroy(); this.barChart?.destroy(); }; },
            () => [this.state.trend, this.state.byWorkcenter, this.state.topEquipment]
        );
    }

    get display() { return { controlPanel: {} }; }

    get baseDomain() {
        const domain = [];
        if (this.state.dateFrom) domain.push(["downtime_start", ">=", this.state.dateFrom]);
        if (this.state.dateTo) domain.push(["downtime_start", "<=", this.state.dateTo]);
        return domain;
    }

    onDateFromChange(ev) { this.state.dateFrom = ev.target.value; }
    onDateToChange(ev) { this.state.dateTo = ev.target.value; }

    async fetchData() {
        this.state.loading = true;
        const domain = this.baseDomain;
        const orm = this.orm;
        const model = "maintenance.downtime.impact.report";
        const data = await this.keepLast.add((async () => ({
            summary: await orm.call(model, "get_summary", [domain]),
            trend: await orm.call(model, "get_downtime_trend", [domain]),
            byWorkcenter: await orm.call(model, "get_impact_by_workcenter", [domain]),
            topEquipment: await orm.call(model, "get_top_equipment", [domain]),
            details: await orm.call(model, "get_details", [domain]),
            recentEvents: await orm.call(model, "get_recent_maintenance_events", [5]),
        }))());
        Object.assign(this.state, data);
        this.state.loading = false;
    }

    renderCharts() {
        this.comboChart?.destroy();
        this.donutChart?.destroy();
        this.barChart?.destroy();

        if (this.comboRef.el && this.state.trend && this.state.trend.categories.length) {
            this.comboChart = new Chart(this.comboRef.el, {
                data: {
                    labels: this.state.trend.categories,
                    datasets: [
                        { type: "bar", label: "Downtime (h)", data: this.state.trend.hours, backgroundColor: "#00A0DB", order: 2 },
                        { type: "line", label: "Missed Due Dates", data: this.state.trend.missed_counts, borderColor: "#FB923C", tension: 0.3, order: 1 },
                    ],
                },
                options: { maintainAspectRatio: false, scales: { y: { beginAtZero: true } } },
            });
        }
        if (this.donutRef.el && this.state.byWorkcenter.length) {
            this.donutChart = new Chart(this.donutRef.el, {
                type: "doughnut",
                data: {
                    labels: this.state.byWorkcenter.map((r) => r.workcenter),
                    datasets: [{ data: this.state.byWorkcenter.map((r) => r.cost), backgroundColor: PALETTE, borderWidth: 2, borderColor: "#fff" }],
                },
                options: { cutout: "65%", plugins: { legend: { display: true, position: "bottom" } }, maintainAspectRatio: false },
            });
        }
        if (this.barRef.el && this.state.topEquipment.length) {
            this.barChart = new Chart(this.barRef.el, {
                type: "bar",
                data: {
                    labels: this.state.topEquipment.map((r) => r.equipment),
                    datasets: [{ data: this.state.topEquipment.map((r) => r.hours), backgroundColor: PALETTE, borderRadius: 4 }],
                },
                options: { indexAxis: "y", plugins: { legend: { display: false } }, maintainAspectRatio: false, scales: { x: { beginAtZero: true } } },
            });
        }
    }

    exportXlsx = () => {
        const params = new URLSearchParams({ domain: JSON.stringify(this.baseDomain) });
        window.location = `/bs_maintenance_downtime_impact_report/export.xlsx?${params}`;
    };
}

registry.category("actions").add("bs_maintenance_downtime_dashboard", DowntimeImpactDashboard);
