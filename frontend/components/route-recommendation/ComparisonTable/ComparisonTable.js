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

            // Find highlights
            const cheapest = minVal(candidates, "cost");
            const fastest = minVal(candidates, "transit_time");
            const safest = minVal(candidates, "hops"); // fewer hops = safer
            const reliable = maxVal(candidates, "composite_score");
            const sustainable = minVal(candidates, "distance"); // shorter distance = lower carbon footprint

            let rowsHtml = "";
            candidates.forEach((c) => {
                const hours = c.transit_time * 24;
                const isSelected = selectedId === c.candidate_id;
                
                // Construct badges
                const badges = [];
                if (c.candidate_id === cheapest.candidate_id) badges.push('<span class="badge success">Cheapest</span>');
                if (c.candidate_id === fastest.candidate_id) badges.push('<span class="badge info">Fastest</span>');
                if (c.candidate_id === safest.candidate_id) badges.push('<span class="badge warning">Safest</span>');
                if (c.candidate_id === reliable.candidate_id) badges.push('<span class="badge primary">Reliable</span>');
                if (c.candidate_id === sustainable.candidate_id) badges.push('<span class="badge info">Sustainable</span>');

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
