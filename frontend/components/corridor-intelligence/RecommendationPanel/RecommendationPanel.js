/**
 * RecommendationPanel Component
 * Renders actionable AI recommendations.
 */
(function() {
    const RecommendationPanel = {
        render(containerId, recommendations) {
            const container = document.getElementById(containerId);
            if (!container) return;

            if (!recommendations || recommendations.length === 0) {
                container.innerHTML = `
                    <div class="card glass-panel fade-in-slide-up" style="height: 100%;">
                        <div class="card-header">
                            <h3><i class="fa-solid fa-lightbulb text-success"></i> AI Improvement Recommendations</h3>
                        </div>
                        <div class="card-body" style="padding: var(--space-6); text-align: center; color: var(--text-muted); font-size: var(--font-size-xs);">
                            Logistics lines are performing optimally. No improvements requested.
                        </div>
                    </div>
                `;
                return;
            }

            let itemsHtml = "";
            recommendations.forEach(r => {
                let badgeClass = "warning";
                if (r.priority === "Critical" || r.priority === "High") {
                    badgeClass = "danger";
                } else if (r.priority === "Low") {
                    badgeClass = "info";
                }

                itemsHtml += `
                    <div class="rec-suggestion-card" style="display: flex; gap: var(--space-3); padding: var(--space-3); background: rgba(9, 9, 11, 0.4); border: 1px solid rgba(63, 63, 70, 0.3); border-radius: var(--radius-md); align-items: start;">
                        <i class="fa-solid fa-lightbulb text-success" style="margin-top: 2px;"></i>
                        <div style="display: flex; flex-direction: column; gap: 2px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                                <span style="font-size: var(--font-size-xs); font-weight: var(--font-weight-bold); color: var(--text-primary);">${r.corridor}</span>
                                <span class="badge ${badgeClass}" style="font-size: 9px; padding: 2px 6px;">${r.priority}</span>
                            </div>
                            <p style="font-size: 11px; color: var(--text-secondary); margin: var(--space-1) 0 4px 0; line-height: 1.4;">${r.suggestion}</p>
                            <span style="font-size: 10px; color: var(--text-muted);"><i class="fa-solid fa-arrow-trend-up text-success"></i> <strong>Impact:</strong> ${r.impact}</span>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="height: 100%;">
                    <div class="card-header">
                        <h3><i class="fa-solid fa-brain text-success"></i> AI Improvement Recommendations</h3>
                    </div>
                    <div class="card-body" style="padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-3); max-height: 380px; overflow-y: auto;">
                        ${itemsHtml}
                    </div>
                </div>
            `;
        }
    };
    window.RecommendationPanel = RecommendationPanel;
})();
