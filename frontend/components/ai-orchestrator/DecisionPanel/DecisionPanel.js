/**
 * DecisionPanel Component
 * Displays trade-offs, confidence levels, conflict resolutions, and unified recommendations.
 */
(function() {
    const DecisionPanel = {
        render(containerId, decision) {
            const el = document.getElementById(containerId);
            if (!el) return;

            if (!decision) {
                el.innerHTML = `
                    <div class="card glass-panel" style="height:100%; display:flex; align-items:center; justify-content:center; padding:var(--space-6); color:var(--text-muted); font-size:11px;">
                        No active recommendation compiled.
                    </div>`;
                return;
            }

            const conflictHtml = decision.conflicts.length > 0 
                ? decision.conflicts.map(c => `
                    <div style="padding:var(--space-2); background:rgba(239, 68, 68, 0.08); border:1px solid rgba(239, 68, 68, 0.25); border-radius:var(--radius-md); font-size:11px; margin-bottom:var(--space-2);">
                        <strong style="color:#ef4444;"><i class="fa-solid fa-triangle-exclamation"></i> Conflict: ${c.type}</strong>
                        <p style="margin:2px 0; color:var(--text-secondary); line-height:1.4;">${c.description}</p>
                        <p style="margin:0; color:#10b981; font-weight:600;"><i class="fa-solid fa-shield-check"></i> Resolution: ${c.resolution}</p>
                    </div>`).join("")
                : `<div style="font-size:11px; color:#10b981; margin-bottom:var(--space-2);"><i class="fa-solid fa-circle-check"></i> No active routing conflicts detected.</div>`;

            const recsHtml = decision.recommendations.map(r => `
                <li style="font-size:11px; color:var(--text-secondary); line-height:1.5; margin-bottom:4px;">${r}</li>
            `).join("");

            el.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="height:100%;">
                    <div class="card-header" style="display:flex; justify-content:space-between; align-items:center;">
                        <h3><i class="fa-solid fa-brain text-success"></i> Unified Decision recommendation Engine</h3>
                        <div style="text-align:right;">
                            <span style="font-size:10px; color:var(--text-muted);">Confidence Score</span>
                            <div style="font-size:1.4rem; font-weight:700; color:#10b981;">${decision.confidence_score}%</div>
                        </div>
                    </div>
                    <div class="card-body" style="padding:var(--space-3); display:flex; flex-direction:column; gap:var(--space-3);">
                        
                        <!-- Routing Choices -->
                        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:var(--space-2);">
                            <div style="padding:var(--space-2); background:rgba(59, 130, 246, 0.08); border:1px solid rgba(59, 130, 246, 0.25); border-radius:var(--radius-md); text-align:center;">
                                <div style="font-size:9px; color:var(--text-muted);">RECOMMENDED ROUTE</div>
                                <strong style="font-size:11px; color:#fff;">${decision.best_route}</strong>
                            </div>
                            <div style="padding:var(--space-2); background:rgba(6, 182, 212, 0.08); border:1px solid rgba(6, 182, 212, 0.25); border-radius:var(--radius-md); text-align:center;">
                                <div style="font-size:9px; color:var(--text-muted);">LOWEST COST ROUTE</div>
                                <strong style="font-size:11px; color:#fff;">${decision.lowest_cost_route}</strong>
                            </div>
                        </div>

                        <!-- Impacts -->
                        <div style="font-size:11px; line-height:1.4; display:flex; flex-direction:column; gap:var(--space-1);">
                            <div><strong style="color:var(--text-primary);">Business Impact:</strong> <span style="color:var(--text-secondary);">${decision.business_impact}</span></div>
                            <div><strong style="color:var(--text-primary);">Network Impact:</strong> <span style="color:var(--text-secondary);">${decision.network_impact}</span></div>
                        </div>

                        <!-- Conflict Resolution -->
                        <div>
                            <h4 style="margin:0 0 6px 0; font-size:11px; color:var(--text-primary); font-weight:600;">Trade-off Conflict Resolutions</h4>
                            ${conflictHtml}
                        </div>

                        <!-- Unified Actionable Recommendations -->
                        <div>
                            <h4 style="margin:0 0 6px 0; font-size:11px; color:var(--text-primary); font-weight:600;">Unified Action Items</h4>
                            <ul style="margin:0; padding-left:14px;">${recsHtml}</ul>
                        </div>

                    </div>
                </div>
            `;
        }
    };
    window.DecisionPanel = DecisionPanel;
})();
