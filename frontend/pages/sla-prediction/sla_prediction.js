/**
 * SLA Prediction Workspace Controller
 * Fetches predictions + forecast, wires all components, handles exports.
 */
(function() {
    let _payload = null;
    let _forecast = null;

    async function initSLAPredictionWorkspace() {
        console.log("[SLAPrediction] Initializing workspace...");

        // Spinner states
        ["sla-dashboard", "sla-tracker", "sla-hub-panel",
         "sla-alert-center", "sla-rec-panel"].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = `<div style="padding:var(--space-6);text-align:center;color:var(--text-muted);"><i class="fa-solid fa-spinner fa-spin" style="font-size:1.5rem;"></i></div>`;
        });

        window.RiskHeatmap.init("sla-risk-map");

        try {
            // Fetch both endpoints in parallel
            const [predRes, fcstRes] = await Promise.all([
                fetch("/api/sla-prediction/payload", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ filters: {} }) }),
                fetch("/api/sla-prediction/forecast",  { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ filters: {} }) })
            ]);

            if (!predRes.ok) throw new Error("Prediction API failed");
            if (!fcstRes.ok) throw new Error("Forecast API failed");

            _payload  = await predRes.json();
            _forecast = await fcstRes.json();

            const { shipments, hubs, corridors, summary, charts, alerts, recommendations } = _payload;

            // 1. KPI scorecards
            window.PredictionDashboard.render("sla-dashboard", summary);

            // 2. Risk heatmap
            window.RiskHeatmap.render(shipments, hubs, corridors);

            // 3. 7-day timeline bar chart
            window.ForecastTimeline.renderTimeline("sla-forecast-timeline", _forecast.timeline, _forecast.peak_day);

            // 4. Plotly charts (rendered into sla-charts-panel divs)
            const chartsPanel = document.getElementById("sla-charts-panel");
            if (chartsPanel) {
                chartsPanel.innerHTML = `
                    <div class="card glass-panel">
                        <div class="card-header"><h3><i class="fa-solid fa-chart-pie text-primary"></i> Risk Analytics</h3></div>
                        <div class="card-body" style="padding:var(--space-2);display:grid;grid-template-columns:1fr 1fr;gap:var(--space-3);">
                            <div>
                                <p style="font-size:10px;color:var(--text-muted);text-align:center;margin-bottom:4px;">Risk Distribution</p>
                                <div id="sla-pie-chart"></div>
                            </div>
                            <div>
                                <p style="font-size:10px;color:var(--text-muted);text-align:center;margin-bottom:4px;">Hub Risk Scores</p>
                                <div id="sla-hub-bar"></div>
                            </div>
                        </div>
                    </div>
                    <div class="card glass-panel">
                        <div class="card-header"><h3><i class="fa-solid fa-wave-square text-danger"></i> Delay Forecast per Shipment</h3></div>
                        <div class="card-body" style="padding:var(--space-2);">
                            <div id="sla-delay-line"></div>
                        </div>
                    </div>`;
                window.ForecastTimeline.renderCharts(charts);
            }

            // 5. Shipment risk table
            window.ShipmentRiskTable.render("sla-tracker", shipments);

            // 6. Hub risk matrix
            window.HubRiskPanel.render("sla-hub-panel", hubs);

            // 7. Alerts
            window.AlertCenter.render("sla-alert-center", alerts);

            // 8. AI Recommendations
            window.RecommendationPanel.render("sla-rec-panel", recommendations);

        } catch (err) {
            console.error("[SLAPrediction] Error:", err);
            const el = document.getElementById("sla-dashboard");
            if (el) el.innerHTML = `<div class="card glass-panel" style="padding:var(--space-6);text-align:center;color:var(--danger-color);">
                <i class="fa-solid fa-triangle-exclamation"></i> Failed to load SLA prediction data.
            </div>`;
        }
    }

    function exportRiskCSV() {
        if (!_payload) return;
        let csv = "Shipment ID,Origin,Destination,Risk Score,Risk Level,Breach %,Delay (h),Confidence,Causes,Impact USD\n";
        _payload.shipments.forEach(s => {
            csv += `${s.transaction_id},${s.origin},${s.destination},${s.risk_score},${s.risk_level},${s.breach_probability},${s.estimated_delay_hours},${s.confidence_score},"${s.likely_causes.join('; ')}",${s.business_impact_usd}\n`;
        });
        const a = document.createElement("a");
        a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
        a.download = "sla_risk_report.csv";
        a.click();
    }

    function exportRiskPDF() {
        if (!_payload) return;
        const { shipments, hubs, summary } = _payload;
        const w = window.open("", "_blank");
        w.document.write(`<html><head><title>SLA Risk Report</title>
            <style>body{font-family:sans-serif;padding:2rem;color:#1f2937;}h2{color:#1e3a8a;border-bottom:2px solid #e5e7eb;padding-bottom:.5rem;}table{width:100%;border-collapse:collapse;margin-top:1rem;font-size:11px;}th,td{border:1px solid #e5e7eb;padding:6px 10px;}th{background:#f3f4f6;}.kpi{display:inline-block;background:#f0f9ff;border:1px solid #bae6fd;border-radius:6px;padding:8px 14px;margin:4px;text-align:center;}.kv{font-size:1.1rem;font-weight:700;color:#0369a1;display:block;}.kl{font-size:10px;color:#6b7280;}</style></head>
            <body>
            <h2>SLA Breach Prediction — Executive Risk Report</h2>
            <p>Generated: ${new Date().toLocaleString()}</p>
            <h3>Executive Summary</h3>
            <div>
                <div class="kpi"><span class="kv">${summary.predicted_sla_compliance}%</span><span class="kl">Predicted SLA Compliance</span></div>
                <div class="kpi"><span class="kv">${summary.high_risk_shipments}</span><span class="kl">High-Risk Shipments</span></div>
                <div class="kpi"><span class="kv">${summary.critical_hubs}</span><span class="kl">Critical Hubs</span></div>
                <div class="kpi"><span class="kv">${summary.avg_predicted_delay_hours}h</span><span class="kl">Avg Predicted Delay</span></div>
                <div class="kpi"><span class="kv">${summary.recovery_success_rate}%</span><span class="kl">Recovery Rate</span></div>
            </div>
            <h3>Shipment Risk Register</h3>
            <table><thead><tr><th>ID</th><th>Origin</th><th>Destination</th><th>Risk Level</th><th>Breach %</th><th>Delay (h)</th><th>Causes</th><th>Impact</th></tr></thead>
            <tbody>${shipments.map(s=>`<tr><td>${s.transaction_id}</td><td>${s.origin}</td><td>${s.destination}</td><td>${s.risk_level}</td><td>${s.breach_probability}%</td><td>${s.estimated_delay_hours}h</td><td>${s.likely_causes.join(", ")}</td><td>$${s.business_impact_usd}</td></tr>`).join("")}</tbody></table>
            <script>window.onload=function(){window.print();}</script></body></html>`);
        w.document.close();
    }

    window.loadSLAPredictionWorkspace = initSLAPredictionWorkspace;
    window.exportRiskCSV = exportRiskCSV;
    window.exportRiskPDF = exportRiskPDF;
})();
