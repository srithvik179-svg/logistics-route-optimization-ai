/**
 * ReverseDashboard Component
 * Renders the top executive scoreboard cards for Reverse Logistics.
 */
(function() {
    const ReverseDashboard = {
        render(containerId, data) {
            const container = document.getElementById(containerId);
            if (!container) return;

            if (!data) {
                container.innerHTML = `<div class="card glass-panel text-center text-muted" style="padding:var(--space-6);">No returns analytics loaded.</div>`;
                return;
            }

            const today = data.summary.today_returns;
            const recovery = data.analytics.recovery_rate;
            const value = data.analytics.recovered_value;
            const pending = data.summary.pending_returns;
            const avgCost = data.analytics.avg_return_cost;
            const reverseSla = data.analytics.refurbishment_success_rate;
            const queue = data.summary.refurbishment_queue;
            const recycling = data.summary.recycling_volume;

            container.innerHTML = `
                <div class="grid-layout cols-4" style="margin-bottom: var(--space-6); width: 100%;">
                    
                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Today's Returns</span>
                        <span class="metric-value text-success">${today}</span>
                        <span class="metric-sub">${pending} total pending in system</span>
                    </div>

                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Asset Recovery Rate</span>
                        <span class="metric-value text-success">${recovery}%</span>
                        <span class="metric-sub">${reverseSla}% refurbishment success</span>
                    </div>

                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Recovered Asset Value</span>
                        <span class="metric-value text-success">${window.Formatters.safeCurrency(value)}</span>
                        <span class="metric-sub">Net recovered value (Austin Hub)</span>
                    </div>

                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Average Return Cost</span>
                        <span class="metric-value text-primary">${window.Formatters.safeCurrency(avgCost)}</span>
                        <span class="metric-sub">Average cost per reverse leg</span>
                    </div>

                </div>
                
                <div class="grid-layout cols-4" style="margin-bottom: var(--space-6); width: 100%;">
                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Refurbishment Queue</span>
                        <span class="metric-value text-primary">${queue}</span>
                        <span class="metric-sub">Active refurbishing processes</span>
                    </div>
                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Recycling Volume</span>
                        <span class="metric-value text-success">${recycling}</span>
                        <span class="metric-sub">Scrap parts recycled</span>
                    </div>
                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Scrap Scrap Value</span>
                        <span class="metric-value text-success">${window.Formatters.safeCurrency(data.analytics.scrap_value)}</span>
                        <span class="metric-sub">Salvaged metal scrap value</span>
                    </div>
                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Reverse Network Util</span>
                        <span class="metric-value text-primary">${data.analytics.reverse_network_utilization}%</span>
                        <span class="metric-sub">Reverse transit lane capacity</span>
                    </div>
                </div>
            `;
        }
    };
    window.ReverseDashboard = ReverseDashboard;
})();
