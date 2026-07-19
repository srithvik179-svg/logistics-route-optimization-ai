/**
 * RefurbishmentPanel Component
 * Renders the refurbishment queue with processing timelines and Plotly charts.
 */
(function() {
    const RefurbishmentPanel = {
        render(containerId, returns, analytics) {
            const container = document.getElementById(containerId);
            if (!container) return;

            const queue = (returns || []).filter(r => r.status === "Processing" || r.status === "Refurbished");
            const queueRows = queue.map(r => `
                <tr>
                    <td><code style="font-size:10px;">${r.return_id}</code></td>
                    <td>${r.part_number}</td>
                    <td style="text-align:right; font-size:11px;">${r.quantity}</td>
                    <td style="text-align:right; font-size:11px;">${window.Formatters.safeCurrency(r.part_value * 0.85)}</td>
                    <td><span class="badge ${r.status === 'Refurbished' ? 'badge-success' : 'badge-primary'}" style="font-size:9px;">${r.status}</span></td>
                    <td style="font-size:11px;">${r.estimated_completion}</td>
                </tr>
            `).join("");

            container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="height:100%;">
                    <div class="card-header" style="display:flex; justify-content:space-between; align-items:center;">
                        <h3><i class="fa-solid fa-screwdriver-wrench text-primary"></i> Refurbishment Queue</h3>
                        <span class="badge badge-primary">${queue.length} items</span>
                    </div>
                    <div class="card-body" style="padding:0; display:flex; flex-direction:column; gap:var(--space-3);">
                        <div id="refurb-chart" style="width:100%; height:180px; padding:var(--space-2);"></div>
                        <div class="table-container" style="max-height:200px; overflow-y:auto;">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Return ID</th>
                                        <th>Part#</th>
                                        <th class="text-right">Qty</th>
                                        <th class="text-right">Recovery Value</th>
                                        <th>Status</th>
                                        <th>Est. Completion</th>
                                    </tr>
                                </thead>
                                <tbody>${queueRows || '<tr><td colspan="6" class="text-center text-muted" style="padding:16px; font-size:11px;">No items in refurbishment queue.</td></tr>'}</tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;

            // Plotly donut for refurbishment
            const statuses = ["Processing", "Refurbished", "Recycled", "Pending"];
            const counts = statuses.map(s => (returns || []).filter(r => r.status === s).length);
            const colors = ["#3b82f6", "#10b981", "#06b6d4", "#ef4444"];

            Plotly.newPlot("refurb-chart", [{
                type: "pie",
                hole: 0.55,
                values: counts,
                labels: statuses,
                marker: { colors },
                textinfo: "none",
                hoverinfo: "label+value"
            }], {
                paper_bgcolor: "transparent", plot_bgcolor: "transparent",
                showlegend: true,
                legend: { font: { color: "#a1a1aa", size: 9 }, orientation: "h", x: 0.1, y: -0.1 },
                margin: { t: 10, b: 20, l: 10, r: 10 },
                height: 175
            }, { displayModeBar: false });
        }
    };
    window.RefurbishmentPanel = RefurbishmentPanel;
})();
