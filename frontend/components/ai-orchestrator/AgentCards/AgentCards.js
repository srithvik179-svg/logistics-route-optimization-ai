/**
 * AgentCards Component
 * Renders the registry of multi-agent definitions, roles, and status indicators.
 */
(function() {
    const AgentCards = {
        render(containerId, agents) {
            const el = document.getElementById(containerId);
            if (!el || !agents) return;

            const cards = agents.map(a => {
                const statusColor = a.status === "Healthy" ? "var(--success-color, #10b981)" : "var(--danger-color, #ef4444)";
                const depBadges = a.dependency.length > 0 
                    ? a.dependency.map(d => `<span class="badge badge-info" style="font-size:8px;padding:1px 4px;margin-right:2px;">${d}</span>`).join("")
                    : '<span style="font-size:8px;color:var(--text-muted);">None</span>';

                return `
                    <div class="card glass-panel fade-in-slide-up" style="border: 1px solid rgba(63, 63, 70, 0.4); padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-2); justify-content: space-between;">
                        <div>
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:var(--space-1);">
                                <h4 style="margin:0; font-size:var(--font-size-sm); color:var(--text-primary); font-weight:600;">${a.name}</h4>
                                <span style="font-size:8px; color:${statusColor}; font-weight:700;">● ${a.status.toUpperCase()}</span>
                            </div>
                            <p style="font-size:10px; color:var(--text-secondary); margin:0; line-height:1.4;">${a.role}</p>
                        </div>
                        <div style="border-top:1px solid rgba(63, 63, 70, 0.2); padding-top:var(--space-2); margin-top:var(--space-2); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:4px;">
                            <div style="font-size:9px; color:var(--text-muted);">
                                Dep: ${depBadges}
                            </div>
                            <div style="font-size:9px; color:var(--text-muted); text-align:right;">
                                Avg: <strong style="color:var(--text-primary);">${a.metrics.avg_ms}ms</strong> (${a.metrics.calls} calls)
                            </div>
                        </div>
                    </div>
                `;
            }).join("");

            el.innerHTML = `
                <div style="display:flex; flex-direction:column; gap:var(--space-3);">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3 style="margin:0;"><i class="fa-solid fa-users-gear text-primary"></i> AI Agent Registry</h3>
                        <span class="badge badge-primary" style="font-size:9px;">${agents.length} Registered</span>
                    </div>
                    <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap:var(--space-3);">
                        ${cards}
                    </div>
                </div>
            `;
        }
    };
    window.AgentCards = AgentCards;
})();
