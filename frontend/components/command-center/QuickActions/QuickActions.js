/**
 * QuickActions Component
 * Operational shortcuts panel to trigger intelligence modules.
 */
(function() {
    const QuickActions = {
        render(containerId) {
            const el = document.getElementById(containerId);
            if (!el) return;

            const actions = [
                { title: "Run AI Orchestrator", icon: "fa-network-wired", target: "orchestrator-section" },
                { title: "Predict SLA Breach", icon: "fa-hourglass-half", target: "sla-section" },
                { title: "Optimize Cost Sim", icon: "fa-calculator", target: "optimization-section" },
                { title: "View Corridor Anal.", icon: "fa-chart-line", target: "corridor-section" },
                { title: "Reverse Logistics", icon: "fa-rotate-left", target: "reverse-section" },
                { title: "Generate Report", icon: "fa-file-invoice", target: "reports-section" },
                { title: "Open Cmd Palette", icon: "fa-terminal", action: "window.toggleCommandPalette()" },
                { title: "Run A* Route Optimizer", icon: "fa-compass", target: "route-section" }
            ];

            const btns = actions.map(act => {
                const clickAction = act.target 
                    ? `window.navigateFromCommandCenter('${act.target}')` 
                    : act.action;
                return `
                    <button class="btn btn-secondary fade-in-slide-up" 
                            style="display:flex; flex-direction:column; align-items:center; gap:var(--space-2); padding:var(--space-3) var(--space-2); border:1px solid rgba(63,63,70,0.4); text-align:center; height:100%; justify-content:center;"
                            onclick="${clickAction}">
                        <i class="fa-solid ${act.icon}" style="font-size:1.4rem; color:var(--text-primary);"></i>
                        <span style="font-size:10px; font-weight:600;">${act.title}</span>
                    </button>
                `;
            }).join("");

            el.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="height:100%;">
                    <div class="card-header">
                        <h3><i class="fa-solid fa-bolt text-primary"></i> Operations Quick Shortcuts</h3>
                    </div>
                    <div class="card-body" style="padding:var(--space-3); display:grid; grid-template-columns: repeat(4, 1fr); gap:var(--space-2);">
                        ${btns}
                    </div>
                </div>
            `;
        }
    };

    window.navigateFromCommandCenter = function(sectionId) {
        const link = document.querySelector(`.nav-link[data-target="${sectionId}"]`);
        if (link) {
            link.click();
        }
    };

    window.QuickActions = QuickActions;
})();
