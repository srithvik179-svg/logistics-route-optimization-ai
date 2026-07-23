/**
 * SLARecommendationPanel Component
 * AI-driven explainable recommendations for SLA prediction workspace.
 */
(function() {
    function safeText(val, fallback = "Not Available") {
        if (val === undefined || val === null) return fallback;
        const strVal = String(val).trim();
        if (!strVal || strVal.toLowerCase() === "undefined" || strVal.toLowerCase() === "null") {
            return fallback;
        }
        return strVal;
    }

    const SLARecommendationPanel = {
        render(containerId, recommendations) {
            const el = document.getElementById(containerId);
            if (!el) return;

            if (!Array.isArray(recommendations) || !recommendations.length) {
                el.innerHTML = `<div class="card glass-panel" style="padding:var(--space-6);text-align:center;color:var(--text-muted);">No SLA recommendations available.</div>`;
                return;
            }

            const items = recommendations.map((r, i) => {
                const title = safeText(r.title || r.corridor || r.affected_corridor, `SLA Insight #${i+1}`);
                const recText = safeText(r.recommendation || r.action || r.recommended_action || r.suggestion, "Review carrier allocation and transit buffers.");
                const benefit = safeText(r.benefit || r.business_impact || r.impact, "Maintains SLA target compliance.");

                return `
                <div style="display:flex;gap:var(--space-3);padding:var(--space-3);
                            background:rgba(9,9,11,0.4);border:1px solid rgba(59,130,246,0.15);
                            border-radius:var(--radius-md);align-items:start;">
                    <div style="width:24px;height:24px;border-radius:50%;background:rgba(59,130,246,0.2);
                                display:flex;align-items:center;justify-content:center;
                                font-size:10px;font-weight:700;color:#3b82f6;flex-shrink:0;">${i+1}</div>
                    <div style="display:flex;flex-direction:column;gap:3px;flex:1;">
                        <strong style="font-size:var(--font-size-xs);color:var(--text-primary);">${title}</strong>
                        <p style="font-size:11px;color:var(--text-secondary);margin:0;line-height:1.5;">${recText}</p>
                        <span style="font-size:10px;color:#10b981;"><i class="fa-solid fa-arrow-trend-up"></i> ${benefit}</span>
                    </div>
                </div>`;
            }).join("");

            el.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="height:100%;">
                    <div class="card-header">
                        <h3><i class="fa-solid fa-robot text-primary"></i> SLA Risk Recommendations</h3>
                    </div>
                    <div class="card-body" style="padding:var(--space-3);display:flex;flex-direction:column;gap:var(--space-3);max-height:400px;overflow-y:auto;">
                        ${items}
                    </div>
                </div>`;
        }
    };
    window.SLARecommendationPanel = SLARecommendationPanel;
})();
