/**
 * ExecutiveSummary Component
 * Renders business indexes and corporate overview evaluation metrics.
 */
(function() {
    const ExecutiveSummary = {
        render(containerId, summary) {
            const el = document.getElementById(containerId);
            if (!el || !summary) return;

            el.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="border: 1px solid rgba(63, 63, 70, 0.4); padding: var(--space-4);">
                    <div style="display:flex; justify-content:space-between; align-items:start; flex-wrap:wrap; gap:var(--space-3); margin-bottom:var(--space-3);">
                        <div>
                            <h3 style="margin:0 0 4px 0;"><i class="fa-solid fa-crown text-warning"></i> Business Performance Assessment</h3>
                            <p style="margin:0; font-size:11px; color:var(--text-muted);">Executive audit rating metrics compiled across all optimization endpoints.</p>
                        </div>
                        <div style="text-align:right;">
                            <span style="font-size:10px; color:var(--text-muted); text-transform:uppercase;">Health Score Index</span>
                            <div style="font-size:2rem; font-weight:800; color:#10b981; line-height:1.2;">
                                ${summary.business_health_score}<span style="font-size:12px; color:var(--text-muted);">/100</span>
                            </div>
                        </div>
                    </div>
                    <div style="padding:var(--space-3); background:rgba(9, 9, 11, 0.5); border:1px solid rgba(63, 63, 70, 0.3); border-radius:var(--radius-md); font-size:12px; color:var(--text-secondary); line-height:1.6; margin-bottom:var(--space-3);">
                        ${summary.business_overview}
                    </div>
                    <div class="grid-layout cols-2" style="gap:var(--space-3);">
                        <div style="padding:var(--space-3); background:rgba(16, 185, 129, 0.05); border:1px solid rgba(16, 185, 129, 0.2); border-radius:var(--radius-md); text-align:center;">
                            <span style="font-size:10px; color:var(--text-muted); text-transform:uppercase; display:block; margin-bottom:4px;">Projected Savings Impact</span>
                            <strong style="font-size:1.4rem; color:#10b981;">${window.Formatters.safeCurrency(summary.financial_impact_usd)}</strong>
                        </div>
                        <div style="padding:var(--space-3); background:rgba(239, 68, 68, 0.05); border:1px solid rgba(239, 68, 68, 0.2); border-radius:var(--radius-md); text-align:center;">
                            <span style="font-size:10px; color:var(--text-muted); text-transform:uppercase; display:block; margin-bottom:4px;">Active SLA Risk Alerts</span>
                            <strong style="font-size:1.4rem; color:#ef4444;">${summary.critical_risk_count} Critical</strong>
                        </div>
                    </div>
                </div>
            `;
        }
    };
    window.ExecutiveSummary = ExecutiveSummary;
})();
