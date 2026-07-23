(function() {
    const BottleneckPanel = {
        render(containerId, bottlenecks) {
            const container = document.getElementById(containerId);
            if (!container) return;

            if (!bottlenecks || bottlenecks.length === 0) {
                container.innerHTML = `
                    <div class="card glass-panel fade-in-slide-up" style="height: 100%;">
                        <div class="card-header">
                            <h3><i class="fa-solid fa-triangle-exclamation text-success"></i> Network Bottleneck Audit</h3>
                        </div>
                        <div class="card-body" style="padding: var(--space-6); text-align: center; color: var(--text-muted); font-size: var(--font-size-xs);">
                            No critical bottlenecks detected. Corridors are operating within normal parameters.
                        </div>
                    </div>
                `;
                return;
            }

            let itemsHtml = "";
            bottlenecks.forEach(b => {
                let badgeClass = "warning";
                let icon = "fa-triangle-exclamation";
                const sev = b.severity || "HIGH";
                if (sev.includes("CRITICAL") || sev === "Critical") {
                    badgeClass = "danger";
                    icon = "fa-circle-xmark";
                } else if (sev.includes("Low") || sev === "Low") {
                    badgeClass = "info";
                    icon = "fa-circle-info";
                }

                const corr = b.corridor || "Primary Corridor";
                const rootCauseDetails = b.root_cause_details || {};
                const impact = b.business_impact || {};
                const confidence = b.confidence_score || rootCauseDetails.confidence_score || "95.0%";

                itemsHtml += `
                    <div class="bottleneck-card-alert" style="display: flex; flex-direction:column; gap: 6px; padding: 10px 12px; background: rgba(9, 9, 11, 0.5); border: 1px solid rgba(63, 63, 70, 0.4); border-radius: var(--radius-md);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="display:flex; align-items:center; gap:6px;">
                                <i class="fa-solid ${icon} text-${badgeClass}"></i>
                                <span style="font-size: 12px; font-weight: 700; color: #f4f4f5;">${corr}</span>
                            </div>
                            <span class="badge ${badgeClass}" style="font-size:9px;">${sev}</span>
                        </div>

                        <div style="font-size: 11px; color: #d4d4d8; font-weight: 500;">
                            <strong>Root Cause:</strong> ${b.details}
                        </div>

                        ${impact.estimated_excess_cost ? `
                        <div style="display:flex; justify-content:space-between; font-size:10px; color:#a1a1aa; background:rgba(0,0,0,0.3); padding:4px 8px; border-radius:4px;">
                            <span>Excess Cost: <strong style="color:#ef4444;">${impact.estimated_excess_cost}</strong></span>
                            <span>Customer Delay: <strong style="color:#f59e0b;">${impact.customer_delay_days || '+2.5 days'}</strong></span>
                            <span>Confidence: <strong style="color:#60a5fa;">${confidence}</strong></span>
                        </div>
                        ` : ''}

                        <div style="display:flex; justify-content:flex-end; gap:6px; margin-top:2px;">
                            <button class="btn btn-outline-secondary btn-xs" onclick="window.openCorridorDrillDown('${corr}')" style="font-size:9px; padding:2px 8px;">
                                <i class="fa-solid fa-magnifying-glass"></i> Drill Down Details
                            </button>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="height: 100%;">
                    <div class="card-header" style="display:flex; justify-content:space-between; align-items:center; padding:10px 16px;">
                        <h3 style="margin:0; font-size:14px;"><i class="fa-solid fa-triangle-exclamation text-danger"></i> Active Bottleneck & Root Cause Audit</h3>
                        <span class="badge danger" style="font-size:10px;">${bottlenecks.length} Bottlenecks</span>
                    </div>
                    <div class="card-body" style="padding: 12px; display: flex; flex-direction: column; gap: 10px; max-height: 440px; overflow-y: auto;">
                        ${itemsHtml}
                    </div>
                </div>
            `;
        }
    };
    window.BottleneckPanel = BottleneckPanel;
})();
