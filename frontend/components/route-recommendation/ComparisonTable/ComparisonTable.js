/**
 * ComparisonTable Component
 * Renders a side-by-side comparison table of route options with evaluation highlights.
 */
(function() {
    const ComparisonTable = {
        render(containerId, candidates, selectedId = null, onSelectCallback = null) {
            const container = document.getElementById(containerId);
            if (!container) return;

            if (!candidates || candidates.length === 0) {
                container.innerHTML = `
                    <div class="card glass-panel fade-in-slide-up" style="padding: var(--space-6); text-align: center; color: var(--text-muted);">
                        <p>Generate recommendations to compare alternative options.</p>
                    </div>
                `;
                return;
            }

            function toNum(val, fallback = 0) {
                if (val === undefined || val === null) return fallback;
                if (typeof val === 'number') return isNaN(val) ? fallback : val;
                const cleaned = String(val).replace(/[^0-9.]/g, '');
                const num = parseFloat(cleaned);
                return isNaN(num) ? fallback : num;
            }

            // Normalize candidates with fallbacks
            candidates.forEach((c, idx) => {
                if (!c.candidate_id) c.candidate_id = c.id || c.route_id || `cand-${idx + 1}`;
                if (!c.algorithm) c.algorithm = c.name || c.route_name || "A* Route Optimization";
                
                c.cost = toNum(c.cost || c.expected_cost || c.total_cost || c.estimated_cost, 850.0);
                c.distance = toNum(c.distance || (c.distance_km ? c.distance_km * 0.621371 : 0), 450.0);
                c.transit_time = toNum(c.transit_time || c.estimated_transit_days || (c.estimated_transit_hours ? c.estimated_transit_hours / 24.0 : 0), 1.2);
                c.risk_score = toNum(c.risk_score, 15.0);
                c.carbon_kg = toNum(c.carbon_kg, 200.0);

                if (c.confidence_score === undefined || c.confidence_score === null || isNaN(c.confidence_score)) {
                    const rawConf = c.confidence_pct || c.confidence || c.sla_compliance_pct || c.predicted_sla_pct;
                    c.confidence_score = toNum(rawConf, 95.0);
                    if (c.confidence_score > 1.0) c.confidence_score /= 100.0;
                }
                c.composite_score = toNum(c.composite_score || c.overall_score, 90.0);
                if (!c.path_nodes || !Array.isArray(c.path_nodes)) {
                    c.path_nodes = c.path || (c.path_str ? c.path_str.split(/\s*→\s*|\s*->\s*/) : ["HUB-ORIG", "HUB-DEST"]);
                }
            });

            // Find highlights across candidates
            const cheapest = minVal(candidates, "cost");
            const fastest = minVal(candidates, "transit_time");
            const safest = minVal(candidates, "risk_score");
            const reliable = maxVal(candidates, "confidence_score");
            const sustainable = minVal(candidates, "carbon_kg");

            let rowsHtml = "";
            candidates.forEach((c) => {
                const hours = c.transit_time * 24;
                const isSelected = selectedId === c.candidate_id;
                
                // Construct badges
                const badges = [];
                if (cheapest && c.candidate_id === cheapest.candidate_id) badges.push('<span class="badge success">Cheapest</span>');
                if (fastest && c.candidate_id === fastest.candidate_id) badges.push('<span class="badge info">Fastest</span>');
                if (safest && c.candidate_id === safest.candidate_id) badges.push('<span class="badge warning">Safest</span>');
                if (reliable && c.candidate_id === reliable.candidate_id) badges.push('<span class="badge primary">Reliable</span>');
                if (sustainable && c.candidate_id === sustainable.candidate_id) badges.push('<span class="badge info">Sustainable</span>');

                rowsHtml += `
                    <tr class="route-comp-row ${isSelected ? 'active-row' : ''}" data-id="${c.candidate_id}">
                        <td>
                            <div style="display:flex; align-items:center; gap:0.5rem;">
                                <input type="radio" name="comp-route-select" ${isSelected ? 'checked' : ''}>
                                <strong>${c.algorithm}</strong>
                            </div>
                        </td>
                        <td class="text-right">${window.Formatters.safeDistance(c.distance)}</td>
                        <td class="text-right">${hours.toFixed(1)} hrs</td>
                        <td class="text-right">${window.Formatters.safeCurrency(c.cost)}</td>
                        <td class="text-right">${c.path_nodes ? c.path_nodes.length : 2} hops</td>
                        <td class="text-right">${(c.confidence_score * 100).toFixed(0)}%</td>
                        <td>
                            <div style="display:flex; gap:4px; flex-wrap:wrap;">
                                ${badges.join("")}
                            </div>
                        </td>
                    </tr>
                `;
            });

            container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up">
                    <div class="card-header">
                        <h3><i class="fa-solid fa-code-compare text-primary"></i> Alternative Routes Comparison</h3>
                    </div>
                    <div class="card-body" style="padding: 0;">
                        <div class="table-container">
                            <table class="data-table comp-data-table">
                                <thead>
                                    <tr>
                                        <th>Route Engine</th>
                                        <th class="text-right">Distance</th>
                                        <th class="text-right">Estimated Time</th>
                                        <th class="text-right">Transportation Cost</th>
                                        <th class="text-right">Hops Count</th>
                                        <th class="text-right">SLA Confidence</th>
                                        <th>Evaluation Badges</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${rowsHtml}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;

            // Bind click handlers to table rows
            container.querySelectorAll(".route-comp-row").forEach(row => {
                row.addEventListener("click", () => {
                    const id = row.getAttribute("data-id");
                    const radio = row.querySelector("input[type='radio']");
                    if (radio) radio.checked = true;
                    
                    container.querySelectorAll(".route-comp-row").forEach(r => r.classList.remove("active-row"));
                    row.classList.add("active-row");

                    if (onSelectCallback) {
                        onSelectCallback(id);
                    }
                });
            });
        }
    };

    // Helper functions for finding min/max values in list
    function minVal(list, field) {
        return list.reduce((a, b) => {
            const valA = field === "hops" ? (a.path_nodes ? a.path_nodes.length : 2) : a[field];
            const valB = field === "hops" ? (b.path_nodes ? b.path_nodes.length : 2) : b[field];
            return valA < valB ? a : b;
        });
    }

    function maxVal(list, field) {
        return list.reduce((a, b) => a[field] > b[field] ? a : b);
    }

    window.ComparisonTable = ComparisonTable;
})();
