/**
 * Corridor Intelligence Workspace Controller
 * Manages loading performance states, heatmap layers, bottlenecks, and dashboard listings.
 */
(function() {
    let corridorsList = [];
    let nodesList = [];

    async function initCorridorWorkspace() {
        console.log("[CorridorIntelligence] Initializing Workspace...");

        // 1. Initialize Map
        window.HeatMap.init("corridor-heatmap-map");

        // 2. Initialize Table
        window.CorridorTable.init(
            "corridor-table-panel",
            (data) => exportCorridorsCSV(data),
            (data) => exportCorridorsPDF(data)
        );

        // 3. Load corridor data
        await loadCorridorData();
    }

    async function loadCorridorData() {
        console.log("[CorridorIntelligence] Loading Corridor Analytics payload...");
        
        // Show map loader
        window.LoadingSkeleton.showMapOverlay("corridor-heatmap-map", true);

        try {
            const checkRes = await fetch("/api/dataset/status");
            let isValid = false;
            if (checkRes.ok) {
                const statusData = await checkRes.json();
                isValid = !!(statusData.validation_report && statusData.validation_report.is_valid);
            }

            if (!isValid) {
                window.LoadingSkeleton.showMapOverlay("corridor-heatmap-map", false);
                const mapOverlay = document.getElementById("corridor-heatmap-map");
                if (mapOverlay) {
                    mapOverlay.innerHTML = `
                        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; color:var(--text-muted); padding:2rem; text-align:center;">
                            <i class="fa-solid fa-database text-danger" style="font-size: 2.5rem; margin-bottom: 1rem; opacity:0.8;"></i>
                            <h4 style="color:#fff; margin-bottom:0.5rem;">No Dataset Loaded</h4>
                            <p style="font-size: 12px; margin-bottom: 1rem;">Please upload the Dell FutureMinds dataset to view corridors.</p>
                            <button class="btn btn-primary btn-sm" onclick="navigateToDataset()">Go to Import Screen</button>
                        </div>
                    `;
                }
                return;
            }

            // First fetch nodes layout
            const netRes = await fetch("/api/geospatial-network/payload", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filters: {} })
            });
            if (!netRes.ok) throw new Error("Failed fetching network layout nodes");
            const netData = await netRes.json();
            nodesList = netData.nodes || [];

            // Next fetch corridor intelligence
            const res = await fetch("/api/corridor-intelligence/payload", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filters: {} })
            });
            
            window.LoadingSkeleton.showMapOverlay("corridor-heatmap-map", false);
            if (!res.ok) throw new Error("Failed fetching corridor intelligence");
            const payload = await res.json();
            corridorsList = payload.corridors || [];

            // 1. Render Dashboard summary widgets
            window.CorridorDashboard.render(payload);

            // 2. Draw HeatMap polylines & congested hubs
            window.HeatMap.drawCorridors(corridorsList, nodesList);

            // 3. Render Bottlenecks
            window.BottleneckPanel.render("corridor-bottlenecks-panel", payload.bottlenecks || []);

            // 4. Render AI suggestions
            window.RecommendationPanel.render("corridor-suggestions-panel", payload.recommendations || []);

            // 5. Render registry table
            window.CorridorTable.render(corridorsList);

        } catch (err) {
            console.error("[CorridorIntelligence] Load Error:", err);
            window.LoadingSkeleton.showMapOverlay("corridor-heatmap-map", false);
            const mapOverlay = document.getElementById("corridor-heatmap-map");
            if (mapOverlay) {
                mapOverlay.innerHTML = `
                    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; color:var(--text-muted); padding:2rem; text-align:center;">
                        <i class="fa-solid fa-triangle-exclamation text-danger" style="font-size: 2.5rem; margin-bottom: 1rem; opacity:0.8;"></i>
                        <h4 style="color:#fff; margin-bottom:0.5rem;">Failed to load corridors</h4>
                        <p style="font-size: 12px; margin-bottom: 1rem;">Service connectivity issue detected.</p>
                        <button class="btn btn-secondary btn-sm" onclick="loadCorridorData()">Retry</button>
                    </div>
                `;
            }
        }
    }

    // CSV & PDF report exporter helpers
    function exportCorridorsCSV(data) {
        if (!data || data.length === 0) return;

        let csv = "Source,Destination,Distance(km),TransitTime(days),Shipments,DelayRate,Cost($),SLA compliance,EfficiencyScore\n";
        data.forEach(c => {
            csv += `"${c.origin}","${c.destination}",${c.distance.toFixed(1)},${c.transit_time.toFixed(1)},${c.shipment_count},${c.delay_rate.toFixed(1)},${c.avg_cost.toFixed(2)},${c.reliability_score.toFixed(1)},${c.efficiency_score.toFixed(1)}\n`;
        });

        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "corridor_efficiency_report.csv";
        a.click();
    }

    function exportCorridorsPDF(data) {
        if (!data || data.length === 0) return;

        const printWindow = window.open("", "_blank");
        printWindow.document.write(`
            <html>
            <head>
                <title>Corridor Efficiency Report</title>
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
                <h2>Corridor Efficiency Report</h2>
                <p>Report compiled on: ${new Date().toLocaleString()}</p>
                
                <table>
                    <thead>
                        <tr>
                            <th>Source</th>
                            <th>Destination</th>
                            <th class="text-right">Distance</th>
                            <th class="text-right">Transit Time</th>
                            <th class="text-right">Shipments</th>
                            <th class="text-right">Delay Rate</th>
                            <th class="text-right">Avg Cost</th>
                            <th class="text-right">SLA Met</th>
                            <th class="text-right">Efficiency</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.map(c => `
                            <tr>
                                <td>${c.origin}</td>
                                <td>${c.destination}</td>
                                <td class="text-right">${c.distance.toFixed(1)} km</td>
                                <td class="text-right">${c.transit_time.toFixed(1)} days</td>
                                <td class="text-right">${c.shipment_count}</td>
                                <td class="text-right">${c.delay_rate.toFixed(1)}%</td>
                                <td class="text-right">$${c.avg_cost.toFixed(2)}</td>
                                <td class="text-right">${c.reliability_score.toFixed(1)}%</td>
                                <td class="text-right"><strong>${c.efficiency_score.toFixed(0)}%</strong></td>
                            </tr>
                        `).join("")}
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

    window.loadCorridorWorkspace = initCorridorWorkspace;
})();
