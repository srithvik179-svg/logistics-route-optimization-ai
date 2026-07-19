/**
 * MissionControl Component
 * Consolidated executive operations cockpit widget displaying key logistics health metrics.
 */
(function() {
    const MissionControl = {
        render(containerId, kpis) {
            const el = document.getElementById(containerId);
            if (!el || !kpis) return;

            el.innerHTML = `
                <div class="grid-layout cols-4" style="gap:var(--space-4);">
                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Shipments In Transit</span>
                        <span class="metric-value text-primary">${kpis.shipments_in_transit}</span>
                        <span class="metric-sub">Active consignments in network</span>
                    </div>
                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Delayed Shipments</span>
                        <span class="metric-value text-danger">${kpis.delayed_shipments}</span>
                        <span class="metric-sub">SLA risk exceptions</span>
                    </div>
                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Active Critical Alerts</span>
                        <span class="metric-value text-danger">${kpis.critical_alerts}</span>
                        <span class="metric-sub">Require immediate assignment</span>
                    </div>
                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Operational Cost Today</span>
                        <span class="metric-value text-success">${window.Formatters.safeCurrency(kpis.cost_today_usd)}</span>
                        <span class="metric-sub">Estimated shipping cost</span>
                    </div>
                </div>
                <div class="grid-layout cols-4" style="gap:var(--space-4); margin-top:var(--space-4);">
                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Average SLA Rate</span>
                        <span class="metric-value text-success">${kpis.avg_sla_percentage}%</span>
                        <span class="metric-sub">On-time compliance rating</span>
                    </div>
                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Hub Capacity Util.</span>
                        <span class="metric-value text-primary">${kpis.hub_utilization_pct}%</span>
                        <span class="metric-sub">Average across 5 key hubs</span>
                    </div>
                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Vehicle Utilization</span>
                        <span class="metric-value text-primary">${kpis.vehicle_utilization_pct}%</span>
                        <span class="metric-sub">Fleet space allocation score</span>
                    </div>
                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">AI recommendation Sync</span>
                        <span class="metric-value text-success" style="font-size:1.4rem;">${kpis.ai_recommendation_status}</span>
                        <span class="metric-sub">Decision engine status</span>
                    </div>
                </div>
            `;
        }
    };
    window.MissionControl = MissionControl;
})();
