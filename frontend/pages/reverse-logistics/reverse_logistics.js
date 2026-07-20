/**
 * Reverse Logistics Workspace Controller
 * Orchestrates API calls, component rendering, map overlays, and PDF/CSV exports.
 */
(function() {
    let _data = null;

    async function initReverseLogisticsWorkspace() {
        console.log("[ReverseLogistics] Initializing workspace...");

        // Show loading states
        const containers = ["rl-dashboard", "rl-tracker", "rl-recovery-panel", "rl-refurb-panel", "rl-recycling-panel"];
        containers.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = `
                <div style="padding:var(--space-6); text-align:center; color:var(--text-muted);">
                    <i class="fa-solid fa-spinner fa-spin" style="font-size:1.5rem;"></i>
                </div>`;
        });

        // Initialize map immediately
        window.ReverseMap.init("rl-map");

        try {
            // Check dataset status first
            const checkRes = await fetch("/api/dataset/status");
            let isValid = false;
            if (checkRes.ok) {
                const statusData = await checkRes.json();
                isValid = !!(statusData.validation_report && statusData.validation_report.is_valid);
            }

            if (!isValid) {
                containers.forEach(id => {
                    const el = document.getElementById(id);
                    if (el) {
                        el.innerHTML = `
                            <div class="card glass-panel text-center" style="padding: 2rem; border: 1px dashed rgba(239, 68, 68, 0.4); border-radius: 8px;">
                                <i class="fa-solid fa-database text-danger" style="font-size: 2rem; margin-bottom: 1rem; opacity: 0.8;"></i>
                                <h4 style="color:#fff; margin-bottom: 0.5rem;">No Dataset Loaded</h4>
                                <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 1rem;">Please upload or import the Dell FutureMinds dataset to populate analytics dashboard widgets.</p>
                                <button class="btn btn-primary btn-sm" onclick="navigateToDataset()">Go to Import Screen</button>
                            </div>
                        `;
                    }
                });
                return;
            }

            const res = await fetch("/api/reverse-logistics/payload", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filters: {} })
            });
            if (!res.ok) throw new Error("Failed to fetch reverse logistics payload");
            _data = await res.json();

            const { returns, analytics, recommendations, summary } = _data;

            // 1. Dashboard KPI scorecards
            window.ReverseDashboard.render("rl-dashboard", _data);

            // 2. Map overlays
            window.ReverseMap.render(returns);

            // 3. Return tracker table
            window.ReturnTracker.render("rl-tracker", returns);

            // 4. AI Recovery recommendations
            window.RecoveryPanel.render("rl-recovery-panel", recommendations, analytics);

            // 5. Refurbishment queue + donut
            window.RefurbishmentPanel.render("rl-refurb-panel", returns, analytics);

            // 6. Recycling center + category bar chart
            window.RecyclingCenter.render("rl-recycling-panel", returns, analytics);

        } catch (err) {
            console.error("[ReverseLogistics] Load Error:", err);
            containers.forEach(id => {
                const el = document.getElementById(id);
                if (el) {
                    el.innerHTML = `
                        <div class="card glass-panel text-center" style="padding: 1.5rem; border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 8px;">
                            <i class="fa-solid fa-triangle-exclamation text-danger" style="font-size: 1.5rem; margin-bottom: 0.5rem;"></i>
                            <h5 style="color:#fff; margin-bottom: 0.25rem;">Failed to load Reverse Logistics</h5>
                            <p style="font-size: 11px; color: var(--text-muted); margin-bottom: 0.75rem;">Service connectivity issue detected.</p>
                            <button class="btn btn-secondary btn-sm" onclick="loadReverseLogisticsWorkspace()" style="padding: 2px 8px; font-size: 10px;">
                                <i class="fa-solid fa-rotate-right"></i> Retry
                            </button>
                        </div>
                    `;
                }
            });
        }
    }

    // CSV Export
    function exportReturnsCSV() {
        if (!_data) return;
        const { returns } = _data;
        let csv = "Return ID,Shipment ID,Origin,Destination,Status,Reason,Current Hub,Days In Transit,Est. Completion,Return Cost\n";
        returns.forEach(r => {
            csv += `${r.return_id},${r.shipment_id},${r.origin},${r.destination},${r.status},${r.reason},${r.current_hub},${r.days_in_transit},${r.estimated_completion},${r.return_cost}\n`;
        });
        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "reverse_logistics_report.csv";
        a.click();
    }

    // PDF Export
    function exportReturnsPDF() {
        if (!_data) return;
        const { returns, analytics, summary } = _data;
        const w = window.open("", "_blank");
        w.document.write(`
            <html>
            <head>
                <title>Reverse Logistics Executive Report</title>
                <style>
                    body { font-family: sans-serif; padding:2rem; color:#1f2937; }
                    h2 { color:#1e3a8a; border-bottom:2px solid #e5e7eb; padding-bottom:0.5rem; }
                    h3 { color:#374151; margin-top:1.5rem; }
                    table { width:100%; border-collapse:collapse; margin-top:1rem; font-size:11px; }
                    th, td { border:1px solid #e5e7eb; padding:6px 10px; text-align:left; }
                    th { background:#f3f4f6; font-weight:600; }
                    .kpi { display:inline-block; background:#f0f9ff; border:1px solid #bae6fd;
                           border-radius:6px; padding:8px 16px; margin:4px; text-align:center; }
                    .kpi-val { font-size:1.2rem; font-weight:700; color:#0369a1; display:block; }
                    .kpi-lbl { font-size:10px; color:#6b7280; }
                </style>
            </head>
            <body>
                <h2>Reverse Logistics Executive Intelligence Report</h2>
                <p>Generated: ${new Date().toLocaleString()}</p>

                <h3>Executive Summary</h3>
                <div>
                    <div class="kpi"><span class="kpi-val">${summary.today_returns}</span><span class="kpi-lbl">Today's Returns</span></div>
                    <div class="kpi"><span class="kpi-val">${analytics.recovery_rate}%</span><span class="kpi-lbl">Recovery Rate</span></div>
                    <div class="kpi"><span class="kpi-val">$${analytics.recovered_value.toFixed(2)}</span><span class="kpi-lbl">Recovered Value</span></div>
                    <div class="kpi"><span class="kpi-val">$${analytics.avg_return_cost.toFixed(2)}</span><span class="kpi-lbl">Avg Return Cost</span></div>
                    <div class="kpi"><span class="kpi-val">${analytics.refurbishment_success_rate}%</span><span class="kpi-lbl">Refurb Success</span></div>
                    <div class="kpi"><span class="kpi-val">${analytics.recycling_percentage}%</span><span class="kpi-lbl">Recycling %</span></div>
                </div>

                <h3>Return Shipment Register</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Return ID</th><th>Shipment ID</th><th>Origin</th><th>Destination</th>
                            <th>Status</th><th>Reason</th><th>Days</th><th>Cost</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${returns.map(r => `
                            <tr>
                                <td>${r.return_id}</td><td>${r.shipment_id}</td>
                                <td>${r.origin}</td><td>${r.destination}</td>
                                <td>${r.status}</td><td>${r.reason}</td>
                                <td>${r.days_in_transit}d</td><td>$${r.return_cost.toFixed(2)}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
                <script>window.onload = function() { window.print(); }</script>
            </body>
            </html>
        `);
        w.document.close();
    }

    window.loadReverseLogisticsWorkspace = initReverseLogisticsWorkspace;
    window.exportReturnsCSV = exportReturnsCSV;
    window.exportReturnsPDF = exportReturnsPDF;
})();
