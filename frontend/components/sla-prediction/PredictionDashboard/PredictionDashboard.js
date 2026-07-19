/**
 * PredictionDashboard Component
 * Executive KPI scorecards for SLA breach prediction metrics.
 */
(function() {
    const RISK_COLORS = {
        "Very Low": "#10b981", "Low": "#06b6d4",
        "Moderate": "#f59e0b", "High": "#f97316", "Critical": "#ef4444"
    };

    const PredictionDashboard = {
        render(containerId, summary) {
            const el = document.getElementById(containerId);
            if (!el || !summary) return;

            const dist = summary.risk_distribution || {};
            const distHtml = Object.entries(dist).map(([lvl, cnt]) =>
                `<span style="display:inline-flex; align-items:center; gap:4px; font-size:10px; color:${RISK_COLORS[lvl] || '#aaa'};">
                    <span style="width:8px;height:8px;border-radius:50%;background:${RISK_COLORS[lvl]};display:inline-block;"></span>
                    ${lvl}: <strong>${cnt}</strong>
                </span>`
            ).join("&nbsp;&nbsp;");

            el.innerHTML = `
                <div class="grid-layout cols-4" style="margin-bottom:var(--space-5);">
                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Predicted SLA Compliance</span>
                        <span class="metric-value ${summary.predicted_sla_compliance >= 70 ? 'text-success' : 'text-danger'}">${summary.predicted_sla_compliance}%</span>
                        <span class="metric-sub">Forecast for current shipment cohort</span>
                    </div>
                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">High-Risk Shipments</span>
                        <span class="metric-value text-danger">${summary.high_risk_shipments}</span>
                        <span class="metric-sub">Require immediate intervention</span>
                    </div>
                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Critical Hubs</span>
                        <span class="metric-value text-danger">${summary.critical_hubs}</span>
                        <span class="metric-sub">At high congestion risk</span>
                    </div>
                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Upcoming Bottlenecks</span>
                        <span class="metric-value text-primary">${summary.upcoming_bottlenecks}</span>
                        <span class="metric-sub">Corridor risk forecast</span>
                    </div>
                </div>
                <div class="grid-layout cols-3" style="margin-bottom:var(--space-5);">
                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Avg Predicted Delay</span>
                        <span class="metric-value text-primary">${summary.avg_predicted_delay_hours}h</span>
                        <span class="metric-sub">Across all active shipments</span>
                    </div>
                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Recovery Success Rate</span>
                        <span class="metric-value text-success">${summary.recovery_success_rate}%</span>
                        <span class="metric-sub">Historical intervention effectiveness</span>
                    </div>
                    <div class="metric-card glass-panel fade-in-slide-up" style="justify-content:space-between;">
                        <span class="metric-label">Risk Distribution</span>
                        <div style="display:flex; flex-wrap:wrap; gap:var(--space-1); margin-top:var(--space-2);">${distHtml}</div>
                        <span class="metric-sub">Across all scored shipments</span>
                    </div>
                </div>
            `;
        }
    };
    window.PredictionDashboard = PredictionDashboard;
})();
