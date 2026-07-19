/**
 * NetworkHealth Component
 * Displays the overall corporate logistics intelligence score and rating matrix.
 */
(function() {
    const NetworkHealth = {
        render(containerId, health) {
            const el = document.getElementById(containerId);
            if (!el || !health) return;

            el.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="height:100%;">
                    <div class="card-header" style="display:flex; justify-content:space-between; align-items:center;">
                        <h3><i class="fa-solid fa-heart-pulse text-success"></i> Unified Network Health score</h3>
                        <div style="font-size:1.8rem; font-weight:800; color:#10b981; line-height:1.2;">
                            ${health.overall_score}<span style="font-size:11px; color:var(--text-muted);">/100</span>
                        </div>
                    </div>
                    <div class="card-body" style="padding:var(--space-3); display:flex; flex-direction:column; gap:var(--space-2);">
                        <div style="font-size:11px; line-height:1.4; margin-bottom:4px; color:var(--text-secondary);">
                            Combined score based on route reliability, hub capacities, and predicted SLA metrics.
                        </div>
                        
                        <!-- Reliability -->
                        <div style="display:flex; justify-content:space-between; align-items:center; font-size:10px;">
                            <span>Route Reliability</span>
                            <strong>${health.route_reliability}%</strong>
                        </div>
                        <div style="width:100%; height:5px; background:rgba(63,63,70,0.3); border-radius:3px; overflow:hidden; margin-bottom:var(--space-1);">
                            <div style="width:${health.route_reliability}%; height:100%; background:#10b981;"></div>
                        </div>

                        <!-- SLA -->
                        <div style="display:flex; justify-content:space-between; align-items:center; font-size:10px;">
                            <span>SLA Compliance Target</span>
                            <strong>${health.sla_compliance}%</strong>
                        </div>
                        <div style="width:100%; height:5px; background:rgba(63,63,70,0.3); border-radius:3px; overflow:hidden; margin-bottom:var(--space-1);">
                            <div style="width:${health.sla_compliance}%; height:100%; background:#f59e0b;"></div>
                        </div>

                        <!-- Cost Efficiency -->
                        <div style="display:flex; justify-content:space-between; align-items:center; font-size:10px;">
                            <span>Fleet Cost Efficiency</span>
                            <strong>${health.cost_efficiency}%</strong>
                        </div>
                        <div style="width:100%; height:5px; background:rgba(63,63,70,0.3); border-radius:3px; overflow:hidden;">
                            <div style="width:${health.cost_efficiency}%; height:100%; background:#06b6d4;"></div>
                        </div>
                    </div>
                </div>
            `;
        }
    };
    window.NetworkHealth = NetworkHealth;
})();
