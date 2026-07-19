/**
 * RecoveryPanel Component
 * Renders AI-generated data-driven recommendations for asset recovery.
 */
(function() {
    const RecoveryPanel = {
        render(containerId, recommendations, analytics) {
            const container = document.getElementById(containerId);
            if (!container) return;

            const recItems = (recommendations || []).map(r => `
                <div style="display:flex; gap:var(--space-3); padding:var(--space-3);
                            background:rgba(9,9,11,0.5); border:1px solid rgba(16,185,129,0.15);
                            border-radius:var(--radius-md); align-items:start;">
                    <i class="fa-solid fa-lightbulb" style="color:#10b981; margin-top:3px; flex-shrink:0;"></i>
                    <div style="display:flex; flex-direction:column; gap:3px;">
                        <strong style="font-size:var(--font-size-xs); color:var(--text-primary);">${r.title}</strong>
                        <p style="font-size:11px; color:var(--text-secondary); margin:0; line-height:1.5;">${r.recommendation}</p>
                        <span style="font-size:10px; color:#10b981;"><i class="fa-solid fa-arrow-trend-up"></i> ${r.benefit}</span>
                    </div>
                </div>
            `).join("");

            container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="height:100%;">
                    <div class="card-header">
                        <h3><i class="fa-solid fa-brain text-success"></i> AI Recovery Recommendations</h3>
                    </div>
                    <div class="card-body" style="display:flex; flex-direction:column; gap:var(--space-3); overflow-y:auto; max-height:340px; padding:var(--space-3);">
                        ${recItems || `<p style="color:var(--text-muted); font-size:var(--font-size-xs); text-align:center;">No recommendations available.</p>`}
                    </div>
                </div>
            `;
        }
    };
    window.RecoveryPanel = RecoveryPanel;
})();
