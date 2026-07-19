/**
 * EfficiencyCard Component
 * Renders Network Health score and top/bottom lists for executive review.
 */
(function() {
    const EfficiencyCard = {
        renderHealthCard(containerId, score) {
            const container = document.getElementById(containerId);
            if (!container) return;

            // Health status tag
            let statusText = "Excellent Network Health";
            let statusClass = "text-success";
            if (score < 50) {
                statusText = "Critical Bottlenecks Detected";
                statusClass = "text-danger";
            } else if (score < 75) {
                statusText = "Moderate Congestion Noted";
                statusClass = "text-warning";
            }

            container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: var(--space-6); text-align: center;">
                    <span class="metric-label" style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: var(--font-weight-bold);">Overall Network Health</span>
                    <div style="font-size: 4rem; font-weight: var(--font-weight-bold); font-family: var(--font-heading); color: var(--text-primary); margin: var(--space-2) 0;">
                        <span id="network-health-val">${score}</span><span style="font-size: 2rem; color: var(--text-muted);">/100</span>
                    </div>
                    <div class="health-status ${statusClass}" style="font-size: var(--font-size-xs); font-weight: var(--font-weight-bold);"><i class="fa-solid fa-heart-pulse"></i> ${statusText}</div>
                </div>
            `;
        },

        renderTopList(containerId, list, type = "efficient") {
            const container = document.getElementById(containerId);
            if (!container) return;

            const title = type === "efficient" ? "Top 10 Efficient Corridors" : "Top 10 Inefficient Corridors";
            const icon = type === "efficient" ? "fa-circle-chevron-up text-success" : "fa-circle-chevron-down text-danger";

            let itemsHtml = "";
            if (list.length === 0) {
                itemsHtml = `<div style="text-align:center; color:var(--text-muted); font-size:11px; padding:var(--space-4);">No corridors found.</div>`;
            } else {
                list.forEach((item, index) => {
                    const score = Math.round(item.efficiency_score);
                    const colorClass = type === "efficient" ? "text-success" : "text-danger";
                    itemsHtml += `
                        <div class="corridor-rank-item" style="display: flex; justify-content: space-between; align-items: center; padding: var(--space-2) 0; border-bottom: 1px solid rgba(63,63,70,0.2);">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-size: var(--font-size-xs); color: var(--text-muted); font-family: monospace; width: 16px;">#${index + 1}</span>
                                <span style="font-size: var(--font-size-xs); color: var(--text-primary); font-weight: var(--font-weight-medium);">${item.origin} → ${item.destination}</span>
                            </div>
                            <strong class="${colorClass}" style="font-size: var(--font-size-xs); font-family: monospace;">${score}%</strong>
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
    window.EfficiencyCard = EfficiencyCard;
})();
