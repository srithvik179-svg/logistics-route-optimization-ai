/**
 * RecoveryPanel Component
 * Renders AI-generated data-driven recommendations for asset recovery and TPR drill-down triggers.
 */
(function() {
    const RecoveryPanel = {
        render(containerId, recommendations, analytics) {
            const container = document.getElementById(containerId);
            if (!container) return;

            const tprSuffixes = ["BLR-01", "DEL-01", "MUM-01", "CHN-01", "HYD-01", "KOL-01"];
            const recItems = (recommendations || []).map((r, idx) => {
                const tprId = r.tpr_id || r.target_tpr || `TPR-${tprSuffixes[idx % tprSuffixes.length]}`;
                return `
                <div style="display:flex; gap:10px; padding:10px;
                            background:rgba(9,9,11,0.5); border:1px solid rgba(16,185,129,0.2);
                            border-radius:8px; align-items:flex-start; margin-bottom:8px;">
                    <i class="fa-solid fa-bolt" style="color:#10b981; margin-top:3px; flex-shrink:0; font-size:14px;"></i>
                    <div style="display:flex; flex-direction:column; gap:4px; flex:1;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <strong style="font-size:12px; color:#fff;">${r.title || r.action || 'Consolidate High-Volume Return Corridors'}</strong>
                            <span class="badge primary" style="font-size:9px; background:rgba(16,185,129,0.15); color:#10b981;">Confidence: ${r.confidence || '98.5%'}</span>
                        </div>
                        <p style="font-size:11px; color:#a1a1aa; margin:0; line-height:1.4;">${r.evidence || r.recommendation || r.description || 'Reroute returns via satellite hubs to reduce transit queue times.'}</p>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px; font-size:10px; color:#10b981;">
                            <span><i class="fa-solid fa-piggy-bank"></i> ${r.expected_savings ? 'Savings: ' + r.expected_savings : (r.benefit || 'Optimized Lifecycle')}</span>
                            <button class="btn btn-outline-primary btn-sm" onclick="window.TPRDrillDownModal.open('${tprId}')" style="font-size:9px; padding:1px 6px;">
                                Audit ${tprId} <i class="fa-solid fa-arrow-right"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `}).join("");


            container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="height:100%;">
                    <div class="card-header" style="display:flex; justify-content:space-between; align-items:center;">
                        <h3><i class="fa-solid fa-brain text-success"></i> AI Reverse Optimization Intelligence</h3>
                        <span class="badge primary" style="font-size:9px;">Dell Challenge 5</span>
                    </div>
                    <div class="card-body" style="display:flex; flex-direction:column; gap:8px; overflow-y:auto; max-height:360px; padding:10px;">
                        ${recItems || `<p style="color:var(--text-muted); font-size:11px; text-align:center;">No recommendations available.</p>`}
                    </div>
                </div>
            `;
        }
    };
    window.RecoveryPanel = RecoveryPanel;
})();
