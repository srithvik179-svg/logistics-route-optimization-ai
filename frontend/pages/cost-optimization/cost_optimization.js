/**
 * Cost Optimization Workspace Controller
 * Connects parameter overrides, comparative tables, financial charts, and PDF exports.
 */
(function() {
    let activeScenarios = {};
    let baselineData = null;
    let simulatedData = null;
    let comparisonData = null;
    let recommendationsList = [];
    let chartsPayload = null;

    async function initCostOptimizationWorkspace() {
        console.log("[CostOptimization] Initializing Workspace...");

        // 1. Initialize ScenarioBuilder
        window.ScenarioBuilder.init("sim-builder-panel", (scenarios) => runSimulation(scenarios));

        // 2. Initialize SimulationHistory
        window.SimulationHistory.init("sim-history-panel", (scenarios) => runSimulation(scenarios));

        // 3. Populate Closed Lanes selector choices from network graph
        try {
            const checkRes = await fetch("/api/dataset/status");
            let isValid = false;
            if (checkRes.ok) {
                const statusData = await checkRes.json();
                isValid = !!(statusData.validation_report && statusData.validation_report.is_valid);
            }

            if (!isValid) {
                const simPanel = document.getElementById("sim-builder-panel");
                if (simPanel) {
                    simPanel.innerHTML = `
                        <div class="card glass-panel text-center" style="padding: 1.5rem; border: 1px dashed rgba(239, 68, 68, 0.4); border-radius: 8px;">
                            <i class="fa-solid fa-database text-danger" style="font-size: 1.5rem; margin-bottom: 0.5rem; opacity: 0.8;"></i>
                            <h5 style="color:#fff; margin-bottom: 0.25rem;">No Dataset Loaded</h5>
                            <p style="font-size: 10px; color: var(--text-muted); margin-bottom: 0.75rem;">Please upload the Dell FutureMinds dataset to run cost optimizations.</p>
                            <button class="btn btn-primary btn-sm" onclick="navigateToDataset()" style="font-size: 10px; padding:2px 8px;">Go to Import Screen</button>
                        </div>
                    `;
                }
                return;
            }

            const res = await fetch("/api/geospatial-network/payload", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filters: {} })
            });
            if (!res.ok) throw new Error("Failed fetching network layout");
            const data = await res.json();
            
            // Extract unique routes list
            const corridors = [];
            const seen = new Set();
            (data.routes || []).forEach(r => {
                const key = `${r.origin} -> ${r.destination}`;
                if (!seen.has(key)) {
                    seen.add(key);
                    corridors.push({ origin: r.origin, destination: r.destination });
                }
            });

            window.ScenarioBuilder.populateCorridors(corridors);
        } catch (err) {
            console.error("[CostOptimization] Population Error:", err);
            const simPanel = document.getElementById("sim-builder-panel");
            if (simPanel) {
                simPanel.innerHTML = `
                    <div class="card glass-panel text-center" style="padding: 1rem; border: 1px solid rgba(239, 68, 68, 0.4);">
                        <i class="fa-solid fa-triangle-exclamation text-danger" style="font-size: 1.2rem; margin-bottom: 0.25rem;"></i>
                        <h6 style="color:#fff; margin-bottom: 0.25rem;">Failed to load corridors</h6>
                        <button class="btn btn-secondary btn-sm" onclick="loadCostWorkspace()" style="font-size: 9px; padding: 2px 6px;">Retry</button>
                    </div>
                `;
            }
        }

        // Render empty states
        window.SavingsDashboard.render("sim-savings-dashboard", null);
        window.ScenarioComparison.render("sim-comparison-panel", null, null, null);
        renderRecommendations(null);
    }

    async function runSimulation(scenarios) {
        console.log("[CostOptimization] Running What-If Simulation...", scenarios);
        activeScenarios = scenarios;

        // Show loading state overlay on charts
        const chartBox = document.getElementById("sim-charts-panel");
        if (chartBox) {
            chartBox.innerHTML = `
                <div style="padding:var(--space-6); text-align:center; color:var(--text-muted); font-size:var(--font-size-xs);">
                    <i class="fa-solid fa-spinner fa-spin" style="font-size:2rem; margin-bottom:var(--space-2);"></i>
                    <p>Executing financial models...</p>
                </div>
            `;
        }

        try {
            const res = await fetch("/api/cost-optimization/simulate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    filters: {},
                    scenarios: scenarios
                })
            });

            if (!res.ok) throw new Error("Failed running cost simulation model");
            const payload = await res.json();

            baselineData = payload.baseline;
            simulatedData = payload.simulated;
            comparisonData = payload.comparison;
            recommendationsList = payload.recommendations || [];
            chartsPayload = payload.charts;

            // 1. Render Scorecards
            window.SavingsDashboard.render("sim-savings-dashboard", comparisonData);

            // 2. Render Side-by-Side Table
            window.ScenarioComparison.render(
                "sim-comparison-panel", baselineData, simulatedData, comparisonData
            );

            // 3. Render Financial Charts
            if (chartBox) {
                chartBox.innerHTML = `
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:var(--space-6);">
                        <div id="sim-chart-breakdown" class="sim-chart-div"></div>
                        <div id="sim-chart-waterfall" class="sim-chart-div"></div>
                    </div>
                `;
                window.FinancialCharts.render(chartsPayload.cost_breakdown, chartsPayload.waterfall);
            }

            // 4. Render AI suggestions list
            renderRecommendations(recommendationsList);

            // 5. Log entry in SimulationHistory
            window.SimulationHistory.addEntry(scenarios, comparisonData);

            // Enable Export controls
            const controls = document.getElementById("sim-actions-toolbar");
            if (controls) controls.style.display = "flex";

        } catch (err) {
            console.error("[CostOptimization] Simulation Error:", err);
            alert("Connection error running cost models simulation.");
        }
    }

    function renderRecommendations(list) {
        const container = document.getElementById("sim-recommendations-panel");
        if (!container) return;

        if (!list || list.length === 0) {
            container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="height: 100%;">
                    <div class="card-header">
                        <h3><i class="fa-solid fa-lightbulb text-success"></i> AI Cost-Saving Recommendations</h3>
                    </div>
                    <div class="card-body" style="padding: var(--space-6); text-align: center; color: var(--text-muted); font-size: var(--font-size-xs);">
                        Generate simulations to view data-driven recommendations.
                    </div>
                </div>
            `;
            return;
        }

        let itemsHtml = "";
        list.forEach(r => {
            itemsHtml += `
                <div style="display: flex; gap: var(--space-3); padding: var(--space-3); background: rgba(9, 9, 11, 0.4); border: 1px solid rgba(63, 63, 70, 0.3); border-radius: var(--radius-md); align-items: start;">
                    <i class="fa-solid fa-lightbulb text-success" style="margin-top: 2px;"></i>
                    <div style="display: flex; flex-direction: column; gap: 2px;">
                        <strong style="font-size: var(--font-size-xs); color: var(--text-primary);">${r.title}</strong>
                        <p style="font-size: 11px; color: var(--text-secondary); margin: var(--space-1) 0 4px 0; line-height: 1.4;">${r.recommendation}</p>
                        <span style="font-size: 10px; color: var(--text-muted);"><i class="fa-solid fa-arrow-trend-up text-success"></i> <strong>Estimated Benefit:</strong> ${r.benefit}</span>
                    </div>
                </div>
            `;
        });

        container.innerHTML = `
            <div class="card glass-panel fade-in-slide-up" style="height: 100%;">
                <div class="card-header">
                    <h3><i class="fa-solid fa-brain text-success"></i> AI Cost-Saving Recommendations</h3>
                </div>
                <div class="card-body" style="padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-3); max-height: 350px; overflow-y: auto;">
                    ${itemsHtml}
                </div>
            </div>
        `;
    }

    // Report Exporters
    function exportCSV() {
        if (!comparisonData) return;

        let csv = "Scenario Parameter,Value\n";
        csv += `Fuel Multiplier,${activeScenarios.fuel_multiplier}x\n`;
        csv += `Driver Multiplier,${activeScenarios.driver_multiplier}x\n`;
        csv += `Volume Multiplier,${activeScenarios.volume_multiplier}x\n`;
        csv += `Forced Mode,${activeScenarios.transport_mode}\n`;
        csv += `Closed Lanes,"${activeScenarios.close_routes.join(", ")}"\n\n`;

        csv += "Metric,Baseline,Simulated,Difference,Variance %\n";
        csv += `Total Cost,${baselineData.total_cost},${simulatedData.total_cost},${comparisonData.cost_diff},${comparisonData.cost_change_percent}%\n`;
        csv += `Transit Days,${baselineData.avg_transit_time},${simulatedData.avg_transit_time},${comparisonData.transit_diff},${comparisonData.transit_change_percent}%\n`;
        csv += `SLA met,${baselineData.delivery_success_rate}%,${simulatedData.delivery_success_rate}%,${comparisonData.sla_difference}%,--\n`;
        csv += `Carbon CO2,${baselineData.carbon_emissions},${simulatedData.carbon_emissions},${comparisonData.carbon_diff},${comparisonData.carbon_change_percent}%\n`;

        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "simulation_report.csv";
        a.click();
    }

    function exportPDF() {
        if (!comparisonData) return;

        const printWindow = window.open("", "_blank");
        printWindow.document.write(`
            <html>
            <head>
                <title>Executive What-If Cost Optimization Report</title>
                <style>
                    body { font-family: sans-serif; padding: 2rem; color: #1f2937; }
                    h2 { color: #1e3a8a; border-bottom: 2px solid #e5e7eb; padding-bottom: 0.5rem; }
                    table { width: 100%; border-collapse: collapse; margin-top: 1.5rem; }
                    th, td { border: 1px solid #e5e7eb; padding: 8px; text-align: left; font-size: 11px; }
                    th { background-color: #f3f4f6; }
                    .text-right { text-align: right; }
                </style>
            </head>
            <body>
                <h2>Executive What-If Simulation Report</h2>
                <p>Report compiled on: ${new Date().toLocaleString()}</p>
                
                <h3>Scenario Overrides:</h3>
                <ul>
                    <li>Fuel scale factor: <strong>${activeScenarios.fuel_multiplier}x</strong></li>
                    <li>Driver scale factor: <strong>${activeScenarios.driver_multiplier}x</strong></li>
                    <li>Volume scale factor: <strong>${activeScenarios.volume_multiplier}x</strong></li>
                    <li>Forced transportation mode: <strong>${activeScenarios.transport_mode}</strong></li>
                    <li>Closed Route Corridors: <strong>${activeScenarios.close_routes.join(", ") || "None"}</strong></li>
                </ul>

                <h3>Comparative Financial Metrics:</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Metrics Target</th>
                            <th class="text-right">Baseline Mesh</th>
                            <th class="text-right">Simulated Override</th>
                            <th class="text-right">Variance Delta</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Total Logistics Cost</td>
                            <td class="text-right">$${baselineData.total_cost.toFixed(2)}</td>
                            <td class="text-right">$${simulatedData.total_cost.toFixed(2)}</td>
                            <td class="text-right">$${comparisonData.cost_diff.toFixed(2)}</td>
                        </tr>
                        <tr>
                            <td>Average Transit Time</td>
                            <td class="text-right">${baselineData.avg_transit_time.toFixed(1)} days</td>
                            <td class="text-right">${simulatedData.avg_transit_time.toFixed(1)} days</td>
                            <td class="text-right">${comparisonData.transit_diff.toFixed(1)} days</td>
                        </tr>
                        <tr>
                            <td>SLA Compliance Met</td>
                            <td class="text-right">${baselineData.delivery_success_rate.toFixed(1)}%</td>
                            <td class="text-right">${simulatedData.delivery_success_rate.toFixed(1)}%</td>
                            <td class="text-right">${comparisonData.sla_difference.toFixed(1)}%</td>
                        </tr>
                        <tr>
                            <td>Carbon CO2 Emissions</td>
                            <td class="text-right">${baselineData.carbon_emissions.toFixed(1)} kg</td>
                            <td class="text-right">${simulatedData.carbon_emissions.toFixed(1)} kg</td>
                            <td class="text-right">${comparisonData.carbon_diff.toFixed(1)} kg</td>
                        </tr>
                    </tbody>
                </table>

                <script>
                    window.onload = function() { window.print(); }
                </script>
            </body>
            </html>
        `);
        printWindow.document.close();
    }

    window.loadCostOptimizationWorkspace = initCostOptimizationWorkspace;
    window.exportSimulationCSV = exportCSV;
    window.exportSimulationPDF = exportPDF;
})();
