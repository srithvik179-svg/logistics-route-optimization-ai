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
                { title: "Run A* Route Optimizer", icon: "fa-compass", target: "routes-section" }
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

    window.runAStarRouteOptimizer = async function() {
        try {
            if (window.Toast) window.Toast.info("Executing A* Route Pathfinding Optimization...");
            const res = await fetch("/api/astar-pathfinding/payload", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filters: window.GlobalFilters || {}, heuristic_type: "great-circle" })
            });
            if (!res.ok) throw new Error("A* Pathfinding calculation failed");
            const data = await res.json();
            if (window.Toast) window.Toast.success("A* Route Optimization Completed! Found optimal paths across logistics network.");
            if (typeof window.loadRouteIntelligence === "function") {
                window.loadRouteIntelligence();
            }
            return data;
        } catch (e) {
            console.warn("[QuickActions] A* Optimization error:", e);
            if (window.Toast) window.Toast.error("A* Optimization Error: " + e.message);
        }
    };

    window.navigateFromCommandCenter = function(targetId) {
        if (targetId === "route-section") targetId = "routes-section";

        const navLinks = document.querySelectorAll(".nav-link");
        const sections = document.querySelectorAll(".viewport-section");
        const headerTitle = document.getElementById("header-title");
        const targetSection = document.getElementById(targetId);

        if (targetSection) {
            // Deactivate all sections and nav links
            navLinks.forEach(l => l.classList.remove("active"));
            sections.forEach(s => s.classList.remove("active"));

            // Activate target section and matching nav link
            targetSection.classList.add("active");
            const activeLink = document.querySelector(`.nav-link[data-target="${targetId}"]`);
            if (activeLink) activeLink.classList.add("active");

            // Update Header Title
            if (headerTitle) {
                if (targetId === "routes-section") headerTitle.textContent = "A* Route Cost Optimizer & Intelligence";
                else if (targetId === "sla-section") headerTitle.textContent = "SLA Breach Prediction & Risk Forecasting";
                else if (targetId === "optimization-section") headerTitle.textContent = "Cost Optimization & What-If Simulation";
                else if (targetId === "corridor-section") headerTitle.textContent = "Corridor Efficiency Intelligence";
                else if (targetId === "reverse-section") headerTitle.textContent = "Reverse Logistics Intelligence Platform";
                else if (targetId === "orchestrator-section") headerTitle.textContent = "AI Orchestrator Platform";
                else if (targetId === "reports-section") headerTitle.textContent = "Executive Reports & Decision Support";
            }

            // Scroll smoothly to top of viewport
            window.scrollTo({ top: 0, behavior: 'smooth' });

            // Execute target section workspace loaders
            if (targetId === "routes-section") {
                if (typeof window.loadRouteIntelligence === "function") window.loadRouteIntelligence();
                if (typeof window.runAStarRouteOptimizer === "function") window.runAStarRouteOptimizer();
            } else if (targetId === "sla-section" && typeof window.loadSLAPredictionWorkspace === "function") {
                window.loadSLAPredictionWorkspace();
            } else if (targetId === "optimization-section" && typeof window.loadCostOptimizationWorkspace === "function") {
                window.loadCostOptimizationWorkspace();
            } else if (targetId === "corridor-section" && typeof window.loadCorridorWorkspace === "function") {
                window.loadCorridorWorkspace();
            } else if (targetId === "reverse-section" && typeof window.loadReverseLogisticsWorkspace === "function") {
                window.loadReverseLogisticsWorkspace();
            } else if (targetId === "orchestrator-section" && typeof window.loadOrchestratorWorkspace === "function") {
                window.loadOrchestratorWorkspace();
            } else if (targetId === "reports-section" && typeof window.loadExecutiveReports === "function") {
                window.loadExecutiveReports();
            }
        } else {
            console.warn("[QuickActions] Target section element not found:", targetId);
        }
    };

    window.QuickActions = QuickActions;
})();
