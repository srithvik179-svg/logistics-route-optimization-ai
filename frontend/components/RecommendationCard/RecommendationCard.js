/**
 * RecommendationCard Component
 * Renders structured suggestion action cards that planners can trigger directly.
 */
(function() {
    const RecommendationCard = {
        renderHtml(action) {
            return `
                <div class="card glass-panel rec-card" style="padding:var(--space-3); border:1px solid rgba(63, 63, 70, 0.4); margin-top:8px; display:flex; flex-direction:column; gap:4px; transition:all 0.2s ease;">
                    <div style="font-size:11px; font-weight:bold; color:#fff; display:flex; justify-content:space-between; align-items:center;">
                        <span><i class="fa-solid fa-wand-magic-sparkles text-primary"></i> AI Recommendation</span>
                        <span style="font-size:9px; background:rgba(59, 130, 246, 0.1); color:var(--primary-color); padding:1px 5px; border-radius:3px; border:1px solid rgba(59, 130, 246, 0.2);">Actionable</span>
                    </div>
                    <div style="font-size:11px; color:#fff; line-height:1.4; margin-top:2px;">
                        ${action}
                    </div>
                    <div style="display:flex; justify-content:flex-end; margin-top:6px;">
                        <button class="btn btn-primary btn-sm" onclick="RecommendationCard.triggerAction('${action.replace(/'/g, "\\'")}')" style="font-size:9px; padding:3px 8px;">
                            Accept & Apply
                        </button>
                    </div>
                </div>
            `;
        },

        triggerAction(actionText) {
            console.log(`[CopilotAction] Planners accepted recommendation: ${actionText}`);
            alert(`Recommendation accepted: "${actionText}". Optimization algorithms configured.`);
        }
    };

    window.RecommendationCard = RecommendationCard;
})();
