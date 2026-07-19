/**
 * FinancialCharts Component
 * Renders Plotly cost breakdowns and waterfall savings chart visualizations.
 */
(function() {
    const FinancialCharts = {
        render(breakdownData, waterfallData) {
            if (!breakdownData || !waterfallData) return;

            // 1. Cost Breakdown Bar Chart
            const traceBaseline = {
                x: breakdownData.categories,
                y: breakdownData.baseline,
                name: "Baseline Mesh",
                type: "bar",
                marker: { color: "var(--brand-blue)" }
            };

            const traceSimulated = {
                x: breakdownData.categories,
                y: breakdownData.simulated,
                name: "Simulated Scenario",
                type: "bar",
                marker: { color: "var(--primary-color)" }
            };

            const layoutBreakdown = {
                title: "Scenario Cost Breakdown Comparison",
                barmode: "group",
                paper_bgcolor: "transparent",
                plot_bgcolor: "transparent",
                font: { color: "var(--text-muted)", size: 10 },
                xaxis: { gridcolor: "rgba(63, 63, 70, 0.2)" },
                yaxis: { gridcolor: "rgba(63, 63, 70, 0.2)" },
                margin: { t: 40, b: 40, l: 50, r: 20 },
                height: 250
            };

            Plotly.newPlot("sim-chart-breakdown", [traceBaseline, traceSimulated], layoutBreakdown, { displayModeBar: false });

            // 2. Savings Waterfall Chart
            const traceWaterfall = {
                type: "waterfall",
                orientation: "v",
                measure: ["absolute", "relative", "relative", "relative", "total"],
                x: waterfallData.labels,
                textposition: "outside",
                text: waterfallData.values.map(v => `$${Math.abs(v).toFixed(0)}`),
                y: waterfallData.values,
                connector: { line: { color: "rgba(63, 63, 70, 0.4)" } },
                decreasing: { marker: { color: "var(--success-color)" } },
                increasing: { marker: { color: "var(--danger-color)" } },
                totals: { marker: { color: "var(--brand-blue)" } }
            };

            const layoutWaterfall = {
                title: "Financial Change Waterfall Path",
                paper_bgcolor: "transparent",
                plot_bgcolor: "transparent",
                font: { color: "var(--text-muted)", size: 10 },
                xaxis: { gridcolor: "rgba(63, 63, 70, 0.2)" },
                yaxis: { gridcolor: "rgba(63, 63, 70, 0.2)" },
                margin: { t: 40, b: 40, l: 50, r: 20 },
                height: 250
            };

            Plotly.newPlot("sim-chart-waterfall", [traceWaterfall], layoutWaterfall, { displayModeBar: false });
        }
    };
    window.FinancialCharts = FinancialCharts;
})();
