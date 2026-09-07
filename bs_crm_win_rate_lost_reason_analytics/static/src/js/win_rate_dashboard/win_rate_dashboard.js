/** @odoo-module **/

import { loadBundle } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { SelectMenu } from "@web/core/select_menu/select_menu";
import { useService } from "@web/core/utils/hooks";
import { KeepLast } from "@web/core/utils/concurrency";
import { Layout } from "@web/search/layout";
import { Component, onWillStart, useEffect, useRef, useState } from "@odoo/owl";

const DATE_RANGE_CHOICES = [
    { value: "last_7", label: "Last 7 Days" },
    { value: "last_30", label: "Last 30 Days" },
    { value: "last_90", label: "Last 90 Days" },
    { value: "this_month", label: "This Month" },
    { value: "this_quarter", label: "This Quarter" },
    { value: "this_year", label: "This Year" },
    { value: "all", label: "All Time" },
];

// Fixed palette so a category keeps the same color across the donut and
// its legend, and doesn't reshuffle as the data changes.
const CATEGORY_COLORS = {
    pricing: "#3B82F6",
    timing: "#22D3EE",
    competitor: "#A78BFA",
    no_budget: "#FB923C",
    no_response: "#2DD4BF",
    not_a_fit: "#F472B6",
    other: "#94A3B8",
    none: "#CBD5E1",
};
const SOURCE_COLOR = "#3B82F6";

export class CrmWinRateDashboard extends Component {
    static template = "bs_crm_win_rate_lost_reason_analytics.WinRateDashboard";
    static components = { Layout, SelectMenu };
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.keepLast = new KeepLast();
        this.donutRef = useRef("donutCanvas");
        this.sourceRef = useRef("sourceCanvas");
        this.donutChart = null;
        this.sourceChart = null;

        this.dateRangeChoices = DATE_RANGE_CHOICES;

        this.state = useState({
            dateRange: "last_30",
            teamId: 0,
            userId: 0,
            teams: [],
            salespeople: [],
            data: null,
            loading: true,
        });

        onWillStart(async () => {
            const filters = await this.orm.call("crm.lead", "get_win_rate_dashboard_filters", []);
            this.state.teams = filters.teams;
            this.state.salespeople = filters.salespeople;
            await loadBundle("web.chartjs_lib");
        });

        useEffect(
            () => {
                this.fetchData();
            },
            () => [this.state.dateRange, this.state.teamId, this.state.userId]
        );

        useEffect(
            () => {
                if (this.state.data) {
                    this.renderCharts();
                }
                return () => {
                    this.donutChart?.destroy();
                    this.sourceChart?.destroy();
                };
            },
            () => [this.state.data]
        );
    }

    get display() {
        return { controlPanel: {} };
    }

    get teamChoices() {
        return [{ value: 0, label: "All Teams" }, ...this.state.teams.map((t) => ({ value: t.id, label: t.name }))];
    }

    get funnelRows() {
        const funnel = this.state.data?.funnel || [];
        const maxCount = Math.max(1, ...funnel.map((r) => r.count));
        return funnel.map((r) => ({ ...r, widthPct: Math.max(6, Math.round((r.count / maxCount) * 100)) }));
    }

    get salespersonChoices() {
        return [
            { value: 0, label: "All Salespersons" },
            ...this.state.salespeople.map((u) => ({ value: u.id, label: u.name })),
        ];
    }

    categoryColor(category) {
        return CATEGORY_COLORS[category] || CATEGORY_COLORS.other;
    }

    deltaClass(delta) {
        if (delta === null || delta === undefined) return "o_wrd_delta_muted";
        return delta >= 0 ? "o_wrd_delta_up" : "o_wrd_delta_down";
    }

    deltaLabel(delta) {
        if (delta === null || delta === undefined) return "—";
        const arrow = delta >= 0 ? "↑" : "↓";
        return `${arrow} ${Math.abs(delta)}%`;
    }

    async fetchData() {
        this.state.loading = true;
        const data = await this.keepLast.add(
            this.orm.call("crm.lead", "get_win_rate_dashboard_data", [], {
                date_range: this.state.dateRange,
                team_id: this.state.teamId || null,
                user_id: this.state.userId || null,
            })
        );
        this.state.data = data;
        this.state.loading = false;
    }

    renderCharts() {
        this.donutChart?.destroy();
        this.sourceChart?.destroy();

        const reasons = this.state.data.lost_reasons;
        if (this.donutRef.el && reasons.length) {
            this.donutChart = new Chart(this.donutRef.el, {
                type: "doughnut",
                data: {
                    labels: reasons.map((r) => r.label),
                    datasets: [
                        {
                            data: reasons.map((r) => r.count),
                            backgroundColor: reasons.map((r) => CATEGORY_COLORS[r.category] || CATEGORY_COLORS.other),
                            borderWidth: 2,
                            borderColor: "#ffffff",
                        },
                    ],
                },
                options: {
                    cutout: "70%",
                    plugins: { legend: { display: false }, tooltip: { enabled: true } },
                    maintainAspectRatio: false,
                },
            });
        }

        const sources = this.state.data.sources;
        if (this.sourceRef.el && sources.length) {
            this.sourceChart = new Chart(this.sourceRef.el, {
                type: "bar",
                data: {
                    labels: sources.map((s) => s.label),
                    datasets: [
                        {
                            data: sources.map((s) => s.count),
                            backgroundColor: SOURCE_COLOR,
                            borderRadius: 4,
                            maxBarThickness: 40,
                        },
                    ],
                },
                options: {
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
                    maintainAspectRatio: false,
                },
            });
        }
    }
}

registry.category("actions").add("bs_crm_win_rate_dashboard", CrmWinRateDashboard);
