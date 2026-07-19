/**
 * HubRiskPanel Component
 * Hub congestion matrix with risk scores and predicted SLA impact.
 */
(function() {
    const HubRiskPanel = {
        render(containerId, hubs) {
            const el = document.getElementById(containerId);
            if (!el || !hubs) return;

            const rows = hubs.map(h => `
                <tr>
                    <td><strong>${h.hub}</strong></td>
                    <td style="text-align:right;font-size:11px;">${h.total_shipments}</td>
                    <td style="text-align:right;font-size:11px;">${h.queue_length}</td>
                    <td>
                        <div style="display:flex;align-items:center;gap:5px;">
                            <div style="width:${Math.round(h.capacity_utilization)}%;max-width:70px;height:5px;background:${h.risk_color};border-radius:3px;flex-shrink:0;"></div>
                            <span style="font-size:10px;color:${h.risk_color};">${h.capacity_utilization}%</span>
                        </div>
                    </td>
                    <td style="text-align:right;font-size:11px;color:${h.miss_rate>30?'#ef4444':'#a1a1aa'};">${h.miss_rate}%</td>
                    <td><span class="badge" style="background:${h.risk_color}22;color:${h.risk_color};border:1px solid ${h.risk_color}44;font-size:9px;padding:2px 7px;border-radius:999px;">${h.risk_level}</span></td>
                    <td style="text-align:right;font-size:11px;font-weight:600;color:${h.risk_color};">${h.risk_score}</td>
                    <td style="text-align:right;font-size:11px;">${h.predicted_sla_impact}%</td>
                </tr>`).join("");

            el.innerHTML = `
                <div class="card glass-panel fade-in-slide-up">
                    <div class="card-header">
                        <h3><i class="fa-solid fa-building text-primary"></i> Hub Risk Matrix</h3>
                    </div>
                    <div class="card-body" style="padding:0;">
                        <div class="table-container">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Hub</th>
                                        <th class="text-right">Shipments</th>
                                        <th class="text-right">Queue</th>
                                        <th>Capacity</th>
                                        <th class="text-right">SLA Miss</th>
                                        <th>Risk Level</th>
                                        <th class="text-right">Score</th>
                                        <th class="text-right">SLA Impact</th>
                                    </tr>
                                </thead>
                                <tbody>${rows || '<tr><td colspan="8" style="text-align:center;color:var(--text-muted);padding:16px;font-size:11px;">No hub data available.</td></tr>'}</tbody>
                            </table>
                        </div>
                    </div>
                </div>`;
        }
    };
    window.HubRiskPanel = HubRiskPanel;
})();
