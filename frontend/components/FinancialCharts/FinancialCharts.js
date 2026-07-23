/**
 * FinancialCharts Component
 * Renders Plotly cost breakdowns and waterfall savings chart visualizations.
 */
(function() {
    const FinancialCharts = {
        render(breakdownData, waterfallData) {
            const chart1 = document.getElementById("sim-chart-breakdown");
            const chart2 = document.getElementById("sim-chart-waterfall");
            if (!chart1 || !chart2) return;

            // 1. Cost Breakdown Bar Chart
            const categories = (breakdownData && Array.isArray(breakdownData.categories)) ? breakdownData.categories : ["Transportation", "Handling", "Holding"];
            const baselineCosts = (breakdownData && Array.isArray(breakdownData.baseline)) ? breakdownData.baseline : [3167733.8, 905066.8, 452533.4];
            const simulatedCosts = (breakdownData && Array.isArray(breakdownData.simulated)) ? breakdownData.simulated : [2122381.65, 606394.76, 303197.38];

            const traceBaseline = {
                x: categories,
                y: baselineCosts,
                name: "Baseline Mesh",
                type: "bar",
                marker: { color: "#3b82f6" }
            };

            const traceSimulated = {
                x: categories,
                y: simulatedCosts,
                name: "Simulated Scenario",
                type: "bar",
                marker: { color: "#f97316" }
            };

            const layoutBreakdown = {
                title: { text: "Scenario Cost Breakdown Comparison", font: { color: "#a1a1aa", size: 11 } },
                barmode: "group",
                paper_bgcolor: "transparent",
                plot_bgcolor: "transparent",
                font: { color: "#a1a1aa", size: 9 },
                xaxis: { gridcolor: "rgba(63, 63, 70, 0.2)" },
                yaxis: { gridcolor: "rgba(63, 63, 70, 0.2)" },
                legend: { font: { color: "#a1a1aa", size: 9 }, orientation: "h", x: 0.1, y: -0.2 },
                margin: { t: 30, b: 40, l: 50, r: 20 },
                height: 250
            };

            Plotly.newPlot("sim-chart-breakdown", [traceBaseline, traceSimulated], layoutBreakdown, { displayModeBar: false });

            // 2. Savings Waterfall Chart
            let wfLabels = [];
            let wfValues = [];
            let wfMeasures = [];

            if (waterfallData && Array.isArray(waterfallData.labels) && Array.isArray(waterfallData.values)) {
                wfLabels = waterfallData.labels;
                wfValues = waterfallData.values;
                wfMeasures = waterfallData.measures || ["absolute", "relative", "relative", "relative", "total"];
            } else {
                const baseVal = (waterfallData && waterfallData.baseline !== undefined) ? window.Formatters.parseRawNumber(waterfallData.baseline) : 4525334.0;
                const simVal = (waterfallData && waterfallData.simulated !== undefined) ? window.Formatters.parseRawNumber(waterfallData.simulated) : 3031973.78;
                const deltaVal = (waterfallData && waterfallData.delta !== undefined) ? window.Formatters.parseRawNumber(waterfallData.delta) : (simVal - baseVal);

                wfLabels = ["Baseline Cost", "Net Savings", "Simulated Cost"];
                wfValues = [baseVal, deltaVal, simVal];
                wfMeasures = ["absolute", "relative", "total"];
            }

            const traceWaterfall = {
                type: "waterfall",
                orientation: "v",
                measure: wfMeasures,
                x: wfLabels,
                textposition: "outside",
                text: wfValues.map(v => `$${window.Formatters.safeFixed(Math.abs(v), 0)}`),
                y: wfValues,
                connector: { line: { color: "rgba(63, 63, 70, 0.4)" } },
                decreasing: { marker: { color: "#10b981" } },
                increasing: { marker: { color: "#ef4444" } },
                totals: { marker: { color: "#3b82f6" } }
            };

            const layoutWaterfall = {
                title: { text: "Financial Change Waterfall Path", font: { color: "#a1a1aa", size: 11 } },
                paper_bgcolor: "transparent",
                plot_bgcolor: "transparent",
                font: { color: "#a1a1aa", size: 9 },
                xaxis: { gridcolor: "rgba(63, 63, 70, 0.2)" },
                yaxis: { gridcolor: "rgba(63, 63, 70, 0.2)" },
                margin: { t: 30, b: 40, l: 50, r: 20 },
                height: 250
            };

            Plotly.newPlot("sim-chart-waterfall", [traceWaterfall], layoutWaterfall, { displayModeBar: false });
        }
    };
    window.FinancialCharts = FinancialCharts;
})();
