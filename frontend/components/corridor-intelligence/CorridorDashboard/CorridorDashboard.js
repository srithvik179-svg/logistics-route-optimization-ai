/**
 * CorridorDashboard Component
 * Renders the top executive widgets for Corridor Efficiency.
 */
(function() {
    const CorridorDashboard = {
        render(payload) {
            if (!payload) return;

            // 1. Overall Health Score Card
            window.EfficiencyCard.renderHealthCard("corridor-health-card", payload.network_health_score);

            // 2. Top Efficient Corridors
            window.EfficiencyCard.renderTopList("corridor-top-efficient", payload.top_efficient || [], "efficient");

            // 3. Top Inefficient Corridors
            window.EfficiencyCard.renderTopList("corridor-top-inefficient", payload.top_inefficient || [], "inefficient");

            // 4. Most Delayed & Highest Cost Widgets
            this.renderDetailedList("corridor-most-delayed", payload.most_delayed || [], "delay");
            this.renderDetailedList("corridor-highest-cost", payload.highest_cost || [], "cost");
        },

        renderDetailedList(containerId, list, mode = "delay") {
            const container = document.getElementById(containerId);
            if (!container) return;

            const title = mode === "delay" ? "Most Delayed Corridors" : "Highest Cost Routes";
            const icon = mode === "delay" ? "fa-hourglass-half text-warning" : "fa-hand-holding-dollar text-primary";

            let itemsHtml = "";
            if (list.length === 0) {
                itemsHtml = `<div style="text-align:center; color:var(--text-muted); font-size:11px; padding:var(--space-4);">No corridors found.</div>`;
            } else {
                list.forEach((item, index) => {
                    let valText = "";
                    if (mode === "delay") {
                        valText = `${item.delay_frequency.toFixed(1)}% delay`;
                    } else {
                        valText = `${window.Formatters.safeCurrency(item.avg_cost)}`;
                    }

                    itemsHtml += `
                        <div class="corridor-detail-row" style="display: flex; justify-content: space-between; align-items: center; padding: var(--space-2) 0; border-bottom: 1px solid rgba(63, 63, 70, 0.2);">
                            <div style="display: flex; flex-direction: column; gap: 2px;">
                                <span style="font-size: var(--font-size-xs); color: var(--text-primary); font-weight: var(--font-weight-medium);">${item.origin} → ${item.destination}</span>
                                <span style="font-size: 9px; color: var(--text-muted);">${item.distance} km | ${item.shipment_count} shipments</span>
                            </div>
                            <strong style="font-size: var(--font-size-xs); font-family: monospace; color: var(--text-primary);">${valText}</strong>
                        </div>
                    `;
                });
            }

            container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="height: 100%;">
                    <div class="card-header">
                        <h3><i class="fa-solid ${icon}"></i> ${title}</h3>
                    </div>
                    <div class="card-body" style="padding: var(--space-3); max-height: 280px; overflow-y: auto;">
                        ${itemsHtml}
                    </div>
                </div>
            `;
        }
    };
    window.CorridorDashboard = CorridorDashboard;
})();
