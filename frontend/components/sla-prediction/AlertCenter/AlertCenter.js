/**
 * AlertCenter Component
 * Proactive risk alert feed with severity indicators.
 */
(function() {
    const AlertCenter = {
        render(containerId, alerts) {
            const el = document.getElementById(containerId);
            if (!el) return;

            if (!alerts || !alerts.length) {
                el.innerHTML = `<div class="card glass-panel" style="padding:var(--space-4);text-align:center;color:var(--text-muted);font-size:var(--font-size-xs);">
                    <i class="fa-solid fa-shield-check" style="font-size:1.5rem;color:#10b981;margin-bottom:8px;display:block;"></i>
                    No active risk alerts. Network operating normally.
                </div>`;
                return;
            }

            const ICONS = { "Critical": "fa-circle-exclamation", "High": "fa-triangle-exclamation", "Moderate": "fa-circle-info" };

            const items = alerts.map(a => `
                <div style="display:flex;gap:var(--space-3);padding:var(--space-3);
                            background:rgba(9,9,11,0.5);border:1px solid ${a.color}30;
                            border-left:3px solid ${a.color};border-radius:var(--radius-md);align-items:start;">
                    <i class="fa-solid ${ICONS[a.severity] || 'fa-bell'}" style="color:${a.color};margin-top:2px;flex-shrink:0;"></i>
                    <div style="display:flex;flex-direction:column;gap:2px;flex:1;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span style="font-size:10px;font-weight:600;color:${a.color};">${a.severity.toUpperCase()} — ${a.type}</span>
                        </div>
                        <p style="font-size:11px;color:var(--text-secondary);margin:0;line-height:1.4;">${a.message}</p>
                        <span style="font-size:10px;color:var(--text-muted);"><i class="fa-solid fa-arrow-right"></i> ${a.action}</span>
                    </div>
                </div>`).join("");

            el.innerHTML = `
                <div class="card glass-panel fade-in-slide-up">
                    <div class="card-header" style="display:flex;justify-content:space-between;align-items:center;">
                        <h3><i class="fa-solid fa-bell text-danger"></i> Proactive Risk Alerts</h3>
                        <span class="badge" style="background:rgba(239,68,68,0.15);color:#ef4444;border:1px solid rgba(239,68,68,0.3);font-size:9px;padding:2px 8px;border-radius:999px;">${alerts.length} Active</span>
                    </div>
                    <div class="card-body" style="padding:var(--space-3);display:flex;flex-direction:column;gap:var(--space-2);max-height:320px;overflow-y:auto;">
                        ${items}
                    </div>
                </div>`;
        }
    };
    window.AlertCenter = AlertCenter;
})();
