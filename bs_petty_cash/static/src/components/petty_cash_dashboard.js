/** @odoo-module **/

import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {Component, onWillStart, onMounted, useState} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {session} from "@web/session";

export class PettyCashDashboard extends Component {
    static template = "petty_cash.PettyCashDashboard";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        // Avoid useService("company") — it's unavailable in client action context
        // in Odoo 19. Use session instead, which is always available.
        this._companyId = session.company_id || false;
        this._companyName = session.company_name || "";

        this._loadDashboardData = this._loadDashboardData.bind(this);
        this._onFilterChange = this._onFilterChange.bind(this);
        this._onKpiClick = this._onKpiClick.bind(this);
        this._onActivityClick = this._onActivityClick.bind(this);
        this._openRecords = this._openRecords.bind(this);
        this._formatCurrency = this._formatCurrency.bind(this);
        this._formatNumber = this._formatNumber.bind(this);

        this.state = useState({
            loading: true,
            currencySymbol: "$",
            currentCompanyName: this._companyName,
            filters: {
                date_from: false,
                date_to: false,
                request_type: false,
                department_id: false,
                employee_id: false,
            },
            kpis: {},
            advanceTypeDistribution: [],
            monthlyTrend: [],
            topOutstandingEmployees: [],
            requestStatusFunnel: [],
            recentActivities: [],
            alerts: {},
            requestTypes: [
                {value: "purchase", label: _t("Purchase")},
                {value: "salary", label: _t("Salary")},
                {value: "tour_travel", label: _t("Tour & Travel")},
                {value: "operational_expenses", label: _t("Operational Expenses")},
            ],
        });

        onWillStart(async () => {
            await this._loadDashboardData();
        });

        onMounted(() => {
            if (!this.state.loading) {
                this._renderCharts();
            }
        });
    }

    _getActiveCompanyId() {
        return this._companyId || false;
    }

    async _loadDashboardData() {
        this.state.loading = true;
        try {
            const companyId = this._getActiveCompanyId();
            const result = await this.orm.call(
                "petty.cash.dashboard",
                "get_dashboard_data",
                [],
                {
                    date_from: this.state.filters.date_from,
                    date_to: this.state.filters.date_to,
                    request_type: this.state.filters.request_type,
                    department_id: this.state.filters.department_id,
                    employee_id: this.state.filters.employee_id,
                    company_id: companyId,
                }
            );

            if (result) {
                this.state.kpis = result.kpis || {};
                this.state.advanceTypeDistribution = result.advance_type_distribution || [];
                this.state.monthlyTrend = result.monthly_trend || [];
                this.state.topOutstandingEmployees = result.top_outstanding_employees || [];
                this.state.requestStatusFunnel = result.request_status_funnel || [];
                this.state.recentActivities = result.recent_activities || [];
                this.state.alerts = result.alerts || {};
                this.state.currencySymbol = result.currency_symbol || "$";

                if (result.filters) {
                    this.state.filters.date_from = result.filters.date_from;
                    this.state.filters.date_to = result.filters.date_to;
                }
            }
        } catch (error) {
            this.notification.add(_t("Failed to load dashboard data"), {
                title: _t("Error"),
                type: "danger",
            });
            console.error("Dashboard load error:", error);
        } finally {
            this.state.loading = false;
            setTimeout(() => this._renderCharts(), 100);
        }
    }

    async _onFilterChange(filterName, value) {
        this.state.filters[filterName] = value || false;
        await this._loadDashboardData();
    }

    async _openRecords(model, domain, name) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: name || _t("Records"),
            res_model: model,
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            target: "current",
        });
    }

    _buildCompanyDomain() {
        const companyId = this._getActiveCompanyId();
        if (companyId) return [["company_id", "=", companyId]];
        return [];
    }

    _onKpiClick(kpiKey) {
        const today = new Date().toISOString().split("T")[0];
        const companyDomain = this._buildCompanyDomain();

        switch (kpiKey) {
            case "total_advance_issued":
                this._openRecords("petty.cash.advance", [...companyDomain, ["state", "in", ["paid", "partially_settled", "settled"]]], _t("Issued Advances"));
                break;
            case "total_settled":
                this._openRecords("petty.cash.settlement", [...companyDomain, ["state", "=", "posted"]], _t("Posted Settlements"));
                break;
            case "outstanding_advance":
                this._openRecords("petty.cash.advance", [...companyDomain, ["state", "in", ["paid", "partially_settled"]], ["balance", ">", 0]], _t("Outstanding Advances"));
                break;
            case "overdue_advances":
                this._openRecords("petty.cash.advance", [...companyDomain, ["state", "in", ["paid", "partially_settled"]], ["balance", ">", 0], ["expected_settlement_date", "<", today]], _t("Overdue Advances"));
                break;
            case "active_advances":
                this._openRecords("petty.cash.advance", [...companyDomain, ["state", "in", ["paid", "partially_settled"]]], _t("Active Advances"));
                break;
            case "pending_settlements":
                this._openRecords("petty.cash.settlement", [...companyDomain, ["state", "in", ["draft", "submitted"]]], _t("Pending Settlements"));
                break;
            case "confirmed_advances":
                this._openRecords("petty.cash.advance", [...companyDomain, ["state", "=", "confirmed"]], _t("Advances Awaiting Payment"));
                break;
        }
    }

    _onActivityClick(activity) {
        if (activity.model && activity.record_id) {
            this.action.doAction({
                type: "ir.actions.act_window",
                res_model: activity.model,
                res_id: activity.record_id,
                views: [[false, "form"]],
                target: "current",
            });
        }
    }

    _renderCharts() {
        if (!window.Chart) return;
        this._renderAdvanceTypePieChart();
        this._renderMonthlyTrendChart();
        this._renderTopEmployeesChart();
        this._renderFunnelChart();
    }

    _renderAdvanceTypePieChart() {
        const canvas = document.getElementById("advanceTypePieChart");
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        const data = this.state.advanceTypeDistribution;
        if (this.pieChart) this.pieChart.destroy();
        this.pieChart = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: data.map((d) => d.label),
                datasets: [{data: data.map((d) => d.amount), backgroundColor: data.map((d) => d.color), borderWidth: 2, borderColor: "#fff"}],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {position: "bottom"},
                    tooltip: {callbacks: {label: (context) => { const item = data[context.dataIndex]; return `${item.label}: ${this._formatCurrency(item.amount)} (${item.percentage}%)`; }}},
                },
            },
        });
    }

    _renderMonthlyTrendChart() {
        const canvas = document.getElementById("monthlyTrendChart");
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        const data = this.state.monthlyTrend;
        if (this.trendChart) this.trendChart.destroy();
        this.trendChart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: data.map((d) => d.month_name),
                datasets: [
                    {type: "line", label: _t("Advances Issued"), data: data.map((d) => d.advances_issued), borderColor: "#4CAF50", backgroundColor: "rgba(76, 175, 80, 0.1)", tension: 0.4, fill: true},
                    {type: "bar", label: _t("Settlements Done"), data: data.map((d) => d.settlements_done), backgroundColor: "#2196F3"},
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {position: "top"},
                    tooltip: {callbacks: {label: (context) => `${context.dataset.label}: ${this._formatCurrency(context.parsed.y)}`}},
                },
                scales: {y: {beginAtZero: true, ticks: {callback: (value) => this._formatCurrency(value, true)}}},
            },
        });
    }

    _renderTopEmployeesChart() {
        const canvas = document.getElementById("topEmployeesChart");
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        const data = this.state.topOutstandingEmployees;
        if (this.employeesChart) this.employeesChart.destroy();
        this.employeesChart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: data.map((d) => d.employee_name),
                datasets: [{label: _t("Outstanding Balance"), data: data.map((d) => d.outstanding_balance), backgroundColor: data.map((d) => d.color)}],
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {display: false},
                    tooltip: {callbacks: {label: (context) => _t("Outstanding: ") + this._formatCurrency(context.parsed.x)}},
                },
                scales: {x: {beginAtZero: true, ticks: {callback: (value) => this._formatCurrency(value, true)}}},
            },
        });
    }

    _renderFunnelChart() {
        const canvas = document.getElementById("funnelChart");
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        const data = this.state.requestStatusFunnel;
        if (this.funnelChart) this.funnelChart.destroy();
        this.funnelChart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: data.map((d) => d.label),
                datasets: [{data: data.map((d) => d.count), backgroundColor: data.map((d) => d.color)}],
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {display: false},
                    tooltip: {callbacks: {label: (context) => { const item = data[context.dataIndex]; return `${item.label}: ${item.count} (${item.percentage}%)`; }}},
                },
                scales: {x: {beginAtZero: true}},
            },
        });
    }

    _formatCurrency(value, short = false) {
        const symbol = this.state.currencySymbol || "$";
        if (short && value >= 1000) {
            if (value >= 1000000) return `${symbol}${(value / 1000000).toFixed(1)}M`;
            return `${symbol}${(value / 1000).toFixed(1)}K`;
        }
        return `${symbol} ${value.toLocaleString("en-US", {minimumFractionDigits: 0, maximumFractionDigits: 0})}`;
    }

    _formatNumber(value) {
        return value.toLocaleString("en-US");
    }

    get totalPendingApprovals() {
        return this.state.kpis.pending_settlements?.value || 0;
    }

    get totalOverdue() {
        return this.state.kpis.overdue_advances?.value || 0;
    }

    get totalOutstanding() {
        return this._formatCurrency(this.state.kpis.outstanding_advance?.value || 0);
    }
}

registry.category("actions").add("petty_cash_dashboard_main", PettyCashDashboard);
