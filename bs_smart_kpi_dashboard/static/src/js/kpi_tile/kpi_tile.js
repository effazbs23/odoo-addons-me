/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useRef, onWillUpdateProps } from "@odoo/owl";

/**
 * Renders {chart_type, chart: {labels, datasets}} via Chart.js, pulled in
 * through the web.chartjs_lib bundle included in this module's manifest.
 */
export class KpiTile extends Component {
    static template = "bs_smart_kpi_dashboard.KpiTile";
    static props = ["name", "chart_type", "chart", "error?", "onDelete?", "onPin?"];

    setup() {
        this.canvasRef = useRef("canvas");
        this.chartInstance = null;

        onMounted(() => this._renderChart());
        onWillUpdateProps((nextProps) => this._renderChart(nextProps));
        onWillUnmount(() => {
            if (this.chartInstance) this.chartInstance.destroy();
        });
    }

    _renderChart(props = this.props) {
        if (props.error || !this.canvasRef.el || props.chart_type === "number") return;
        if (this.chartInstance) this.chartInstance.destroy();

        const ctx = this.canvasRef.el.getContext("2d");
        this.chartInstance = new Chart(ctx, {
            type: props.chart_type === "pie" ? "pie" : props.chart_type,
            data: {
                labels: props.chart.labels,
                datasets: props.chart.datasets.map((ds) => ({
                    label: ds.label,
                    data: ds.data,
                })),
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    // Pie/doughnut legends label each slice (one dataset,
                    // many categories); bar/line legends label each dataset
                    // (one category axis, several series) — the "many
                    // enough to need a legend" check differs accordingly.
                    legend: {
                        display: props.chart_type === "pie"
                            ? props.chart.labels.length > 1
                            : props.chart.datasets.length > 1,
                    },
                },
            },
        });
    }

    get singleNumberValue() {
        // "number" chart type: one measure, no groupby -> a single KPI value.
        const ds = this.props.chart && this.props.chart.datasets[0];
        return ds ? ds.data[0] : null;
    }
}
