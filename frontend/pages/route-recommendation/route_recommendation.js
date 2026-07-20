/**
 * Route Recommendation Workspace Orchestrator
 * Connects inputs, scorecard, comparisons, explanations, playback, and exports.
 */
(function() {
    let recMap = null;
    let candidatesList = [];
    let activeRoute = null;
    let nodeCoords = {};
    let activeGoal = "fastest_route";
    let activeVehicle = "Ground Transport";
    let activeSource = "";
    let activeDest = "";

    async function initRecommendationWorkspace() {
        console.log("[RouteRecommendation] Initializing Workspace...");

        // 1. Initialize Leaflet Map
        if (!recMap) {
            recMap = L.map("recommendation-map").setView([31.9686, -99.9018], 6);
            L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
                attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
                subdomains: 'abcd',
                maxZoom: 20
            }).addTo(recMap);
        } else {
            setTimeout(() => {
                recMap.invalidateSize();
            }, 100);
        }

        // 2. Initialize Playback
        window.RoutePlayback.init(recMap);

        // 3. Initialize OptimizationPanel
        window.OptimizationPanel.init("rec-inputs-panel", (inputs) => generateRecommendations(inputs));

        // 4. Initialize History
        window.RecommendationHistory.init("rec-history-panel", (historyItem) => loadHistoryItem(historyItem));

        // 5. Populate Hub Dropdowns by querying the existing network graph API
        try {
            const checkRes = await fetch("/api/dataset/status");
            let isValid = false;
            if (checkRes.ok) {
                const statusData = await checkRes.ok ? await checkRes.json() : null;
                isValid = statusData && statusData.validation_report && statusData.validation_report.is_valid;
            }

            if (!isValid) {
                const inputsPanel = document.getElementById("rec-inputs-panel");
                if (inputsPanel) {
                    inputsPanel.innerHTML = `
                        <div class="card glass-panel text-center" style="padding: 1.5rem; border: 1px dashed rgba(239, 68, 68, 0.4); border-radius: 8px;">
                            <i class="fa-solid fa-database text-danger" style="font-size: 1.5rem; margin-bottom: 0.5rem; opacity: 0.8;"></i>
                            <h5 style="color:#fff; margin-bottom: 0.25rem;">No Dataset Loaded</h5>
                            <p style="font-size: 10px; color: var(--text-muted); margin-bottom: 0.75rem;">Please upload the Dell FutureMinds dataset to run route optimizations.</p>
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
            if (!res.ok) throw new Error("Failed fetching network layout nodes");
            const data = await res.json();
            
            // Extract coordinates lookup map
            nodeCoords = {};
            (data.nodes || []).forEach(n => {
                nodeCoords[n.id] = [n.latitude, n.longitude];
            });

            // Populate selector inputs
            window.OptimizationPanel.populateHubs(data.nodes || []);
        } catch (err) {
            console.error("[RouteRecommendation] Population Error:", err);
            const inputsPanel = document.getElementById("rec-inputs-panel");
            if (inputsPanel) {
                inputsPanel.innerHTML = `
                    <div class="card glass-panel text-center" style="padding: 1rem; border: 1px solid rgba(239, 68, 68, 0.4);">
                        <i class="fa-solid fa-triangle-exclamation text-danger" style="font-size: 1.2rem; margin-bottom: 0.25rem;"></i>
                        <h6 style="color:#fff; margin-bottom: 0.25rem;">Failed to load hubs</h6>
                        <button class="btn btn-secondary btn-sm" onclick="loadRecommendationWorkspace()" style="font-size: 9px; padding: 2px 6px;">Retry</button>
                    </div>
                `;
            }
        }

        // Render initial empty states
        window.RecommendationCard.render("rec-scorecard-panel", null);
        window.DecisionExplanation.render("rec-explanation-panel", null);
        window.ComparisonTable.render("rec-comparison-panel", null);
    }

    async function generateRecommendations(inputs) {
        console.log("[RouteRecommendation] Running Optimization Engines...", inputs);
        
        activeGoal = inputs.goal;
        activeVehicle = inputs.vehicle;
        activeSource = inputs.source;
        activeDest = inputs.dest;

        // Show map loader
        window.LoadingSkeleton.showMapOverlay("recommendation-map", true);

        try {
            const res = await fetch("/api/ai-preparation/decision-support", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    source: inputs.source,
                    destination: inputs.dest,
                    filters: {
                        priority: inputs.priority,
                        vehicle_type: inputs.vehicle
                    }
                })
            });
            
            window.LoadingSkeleton.showMapOverlay("recommendation-map", false);
            if (!res.ok) throw new Error("Failed generating recommendations payload");
            const payload = await res.json();

            // Extract candidates from scenario list
            candidatesList = [];
            const scenarios = payload.scenarios || {};
            
            const uniqueCandIds = new Set();
            Object.keys(scenarios).forEach(key => {
                const cand = scenarios[key];
                if (cand && cand.candidate_id && !uniqueCandIds.has(cand.candidate_id)) {
                    uniqueCandIds.add(cand.candidate_id);
                    candidatesList.push(cand);
                }
            });

            if (candidatesList.length === 0) {
                alert("No viable routes found for this corridor.");
                return;
            }

            // Select recommendation based on optimization goal
            let selectedRoute = scenarios[inputs.goal] || scenarios["best_route"] || candidatesList[0];
            activeRoute = selectedRoute;

            // Render panels
            updateUIWithSelectedRoute();

        } catch (err) {
            console.error("[RouteRecommendation] Generation Error:", err);
            window.LoadingSkeleton.showMapOverlay("recommendation-map", false);
            alert("Connection error running optimization engines.");
        }
    }

    function updateUIWithSelectedRoute() {
        if (!activeRoute) return;

        // 1. Scorecard
        window.RecommendationCard.render("rec-scorecard-panel", activeRoute, activeVehicle);

        // 2. Explanation
        window.DecisionExplanation.render("rec-explanation-panel", activeRoute, activeGoal);

        // 3. Comparison
        window.ComparisonTable.render("rec-comparison-panel", candidatesList, activeRoute.candidate_id, (id) => {
            activeRoute = candidatesList.find(c => c.candidate_id === id);
            updateUIWithSelectedRoute();
        });

        // 4. Map Overlays
        window.RoutePlayback.drawRoutes(
            null, null, candidatesList, activeRoute.candidate_id, nodeCoords
        );

        // Enable Accept & Export controls
        const controls = document.getElementById("rec-actions-toolbar");
        if (controls) controls.style.display = "flex";
    }

    function loadHistoryItem(item) {
        console.log("[RouteRecommendation] Restoring accepted path from log:", item);
        activeSource = item.source;
        activeDest = item.dest;
        
        activeRoute = {
            candidate_id: "historic",
            algorithm: "Restored History",
            distance: item.distance || item.cost / 2.5, // approximate distance if missing
            cost: item.cost,
            transit_time: item.transit_time,
            path_nodes: item.path_nodes,
            confidence_score: 0.95
        };

        candidatesList = [activeRoute];
        updateUIWithSelectedRoute();
    }

    // Export & Decision Actions
    function acceptRecommendation() {
        if (!activeRoute) return;
        
        window.RecommendationHistory.addEntry(
            activeSource,
            activeDest,
            activeRoute.cost,
            activeRoute.transit_time,
            activeRoute.path_nodes
        );

        alert("Route Recommendation Accepted! Logged successfully in Decision history.");
    }

    function exportCSV() {
        if (!activeRoute) return;

        let csv = "Node ID,Sequence Order,Latitude,Longitude\n";
        (activeRoute.path_nodes || []).forEach((nodeId, idx) => {
            const coord = nodeCoords[nodeId] || [0, 0];
            csv += `"${nodeId}",${idx + 1},${coord[0]},${coord[1]}\n`;
        });

        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `route_${activeSource}_to_${activeDest}.csv`;
        a.click();
    }

    function exportPDF() {
        if (!activeRoute) return;
        
        // Dynamic printable view markup
        const printWindow = window.open("", "_blank");
        printWindow.document.write(`
            <html>
            <head>
                <title>AI Route Recommendation Report</title>
                <style>
                    body { font-family: sans-serif; padding: 2rem; color: #1f2937; }
                    h2 { color: #1e3a8a; border-bottom: 2px solid #e5e7eb; padding-bottom: 0.5rem; }
                    .stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-top: 1.5rem; }
                    .stat-item { padding: 1rem; background: #f3f4f6; border-radius: 6px; }
                    .stat-item span { display: block; font-size: 11px; color: #6b7280; text-transform: uppercase; }
                    .stat-item strong { font-size: 18px; color: #111827; }
                    .path-list { margin-top: 2rem; line-height: 1.6; }
                </style>
            </head>
            <body>
                <h2>AI Route Recommendation: ${activeSource} to ${activeDest}</h2>
                <p>Generated on ${new Date().toLocaleString()} | Selected Engine: <strong>${activeRoute.algorithm}</strong></p>
                
                <div class="stat-grid">
                    <div class="stat-item"><span>Distance</span><strong>${activeRoute.distance.toFixed(1)} km</strong></div>
                    <div class="stat-item"><span>Transit Time</span><strong>${(activeRoute.transit_time * 24).toFixed(1)} hrs</strong></div>
                    <div class="stat-item"><span>Transit Cost</span><strong>$${activeRoute.cost.toFixed(2)}</strong></div>
                    <div class="stat-item"><span>Confidence Index</span><strong>${(activeRoute.confidence_score * 100).toFixed(0)}%</strong></div>
                </div>

                <div class="path-list">
                    <h3>Optimal Path Hops:</h3>
                    <ol>
                        ${(activeRoute.path_nodes || []).map(n => `<li>${n}</li>`).join("")}
                    </ol>
                </div>

                <script>
                    window.onload = function() { window.print(); }
                </script>
            </body>
            </html>
        `);
        printWindow.document.close();
    }

    window.loadRecommendationWorkspace = initRecommendationWorkspace;
    window.acceptRecommendation = acceptRecommendation;
    window.exportRecommendationCSV = exportCSV;
    window.exportRecommendationPDF = exportPDF;
})();
