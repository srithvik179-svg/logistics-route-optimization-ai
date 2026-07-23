(function() {
    function safeText(val, fallback = "Not Available") {
        if (val === undefined || val === null) return fallback;
        const strVal = String(val).trim();
        if (!strVal || strVal.toLowerCase() === "undefined" || strVal.toLowerCase() === "null") {
            return fallback;
        }
        return strVal;
    }

    let activeSortKey = "savings";
    let cachedRecommendations = [];

    const CorridorRecommendationPanel = {
        render(containerId, recommendations) {
            const container = document.getElementById(containerId);
            if (!container) return;

            if (Array.isArray(recommendations)) {
                cachedRecommendations = recommendations;
            } else {
                recommendations = cachedRecommendations;
            }

            if (!Array.isArray(recommendations) || recommendations.length === 0) {
                container.innerHTML = `
                    <div class="card glass-panel fade-in-slide-up" style="height: 100%;">
                        <div class="card-header">
                            <h3><i class="fa-solid fa-shield-halved text-success"></i> AI Risk Recommendations</h3>
                        </div>
                        <div class="card-body" style="padding: var(--space-6); text-align: center; color: var(--text-muted); font-size: var(--font-size-xs);">
                            All transport corridors are operating within optimal risk thresholds.
                        </div>
                    </div>
                `;
                return;
            }

            // Sort recommendations based on activeSortKey
            const sortedRecs = [...recommendations].sort((a, b) => {
                if (activeSortKey === "savings") {
                    return (b.savings_raw || 0) - (a.savings_raw || 0);
                } else if (activeSortKey === "risk") {
                    return (b.risk_raw || 0) - (a.risk_raw || 0);
                } else if (activeSortKey === "urgency") {
                    return (b.urgency_raw || 0) - (a.urgency_raw || 0);
                } else if (activeSortKey === "confidence") {
                    return (b.confidence_raw || 0) - (a.confidence_raw || 0);
                }
                return 0;
            });

            let itemsHtml = "";
            sortedRecs.forEach((r, idx) => {
                const title = safeText(r.title || r.corridor || r.affected_corridor, `Corridor Recommendation #${idx + 1}`);
                const corridor = safeText(r.affected_corridor || r.corridor, "All Corridors");
                const priority = safeText(r.priority || r.severity, "Medium");
                const risk_level = safeText(r.severity || r.risk_level, "Medium Risk");
                const action = safeText(r.recommendation || r.recommended_action, "Optimize corridor routing and carrier allocation.");
                const impact = safeText(r.business_impact || r.impact, "Improves delivery SLA compliance.");
                const savings = safeText(r.expected_savings || r.estimated_savings, "Not Available");
                const confidence = safeText(r.confidence, "94.5%");
                const evidence = Array.isArray(r.evidence) ? r.evidence.join(" | ") : safeText(r.evidence, "Facility capacity congestion detected.");

                let badgeClass = "warning";
                if (priority.includes("CRITICAL") || priority.includes("Critical") || risk_level.includes("CRITICAL")) {
                    badgeClass = "danger";
                } else if (priority.includes("Low") || risk_level.includes("Low")) {
                    badgeClass = "info";
                }

                itemsHtml += `
                    <div class="rec-suggestion-card" style="display: flex; flex-direction: column; gap: 8px; padding: 12px; background: rgba(9, 9, 11, 0.5); border: 1px solid rgba(63, 63, 70, 0.4); border-radius: var(--radius-md); transition: transform 0.15s ease;">
                        <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <i class="fa-solid fa-brain text-primary"></i>
                                <span style="font-size: 12px; font-weight: 700; color: #f4f4f5;">${title}</span>
                            </div>
                            <div style="display:flex; align-items:center; gap:6px;">
                                <span class="badge" style="font-size:9px; background:rgba(59,130,246,0.2); color:#60a5fa; border:1px solid rgba(59,130,246,0.3);"><i class="fa-solid fa-gauge-high"></i> ${confidence}</span>
                                <span class="badge ${badgeClass}" style="font-size: 9px; padding: 2px 6px;">${priority}</span>
                            </div>
                        </div>
                        
                        <div style="font-size: 11px; color: #a1a1aa; line-height: 1.4; background: rgba(0,0,0,0.2); padding:6px 8px; border-radius:4px;">
                            <strong style="color:#e4e4e7;"><i class="fa-solid fa-microscope text-info"></i> Evidence:</strong> ${evidence}
                        </div>

                        <div style="display: flex; flex-direction: column; gap: 4px; background: rgba(0,0,0,0.3); padding: 8px; border-radius: 4px; font-size: 11px; border-left: 3px solid #3b82f6;">
                            <div><strong style="color: #60a5fa;"><i class="fa-solid fa-bolt"></i> Recommendation:</strong> <span style="color: #e4e4e7;">${action}</span></div>
                            <div><strong style="color: #34d399;"><i class="fa-solid fa-chart-line"></i> Business Impact:</strong> <span style="color: #e4e4e7;">${impact}</span></div>
                            ${savings !== 'Not Available' ? `<div><strong style="color: #facc15;"><i class="fa-solid fa-sack-dollar"></i> Expected Savings:</strong> <span style="color: #fef08a;">${savings}</span></div>` : ''}
                        </div>
                        
                        <div style="display: flex; justify-content: space-between; align-items:center; font-size: 10px; color: #71717a; margin-top: 2px;">
                            <span><i class="fa-solid fa-route" style="color: #60a5fa;"></i> Corridor: <strong style="color: #d4d4d8;">${corridor}</strong></span>
                            <button class="btn btn-outline-primary btn-xs" onclick="window.triggerCorridorOptimization('${corridor}')" style="font-size:9px; padding:2px 8px;">
                                <i class="fa-solid fa-wand-magic-sparkles"></i> Optimize Corridor
                            </button>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="height: 100%;">
                    <div class="card-header" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 16px; flex-wrap:wrap; gap:8px;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <h3 style="margin:0; font-size: 14px;"><i class="fa-solid fa-robot text-primary"></i> AI Recommendation Cards</h3>
                            <span class="badge info" style="font-size: 10px;">${recommendations.length} Active Insights</span>
                        </div>
                        <div style="display:flex; align-items:center; gap:6px;">
                            <span style="font-size:10px; color:var(--text-muted);">Sort by:</span>
                            <select id="rec-sort-select" style="font-size:10px; padding:2px 6px; background:#18181b; color:#fff; border:1px solid #3f3f46; border-radius:4px;" onchange="window.CorridorRecommendationPanel.setSortKey(this.value, '${containerId}')">
                                <option value="savings" ${activeSortKey==='savings'?'selected':''}>Savings (High → Low)</option>
                                <option value="risk" ${activeSortKey==='risk'?'selected':''}>Risk (Critical → Low)</option>
                                <option value="urgency" ${activeSortKey==='urgency'?'selected':''}>Urgency (High → Low)</option>
                                <option value="confidence" ${activeSortKey==='confidence'?'selected':''}>Confidence (High → Low)</option>
                            </select>
                        </div>
                    </div>
                    <div class="card-body" style="padding: 12px; display: flex; flex-direction: column; gap: 10px; max-height: 460px; overflow-y: auto;">
                        ${itemsHtml}
                    </div>
                </div>
            `;
        },

        setSortKey(sortKey, containerId) {
            activeSortKey = sortKey;
            this.render(containerId, cachedRecommendations);
        }
    };

    window.CorridorRecommendationPanel = CorridorRecommendationPanel;
    window.RecommendationPanel = CorridorRecommendationPanel;
})();
