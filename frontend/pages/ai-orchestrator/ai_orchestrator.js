/**
 * AI Orchestrator Workspace Page Controller
 * Fetches dashboard metadata, manages running flows, and refreshes metrics views.
 */
(function() {
    let _data = null;

    async function initAIOrchestratorWorkspace() {
        console.log("[AIOrchestrator] Initializing workspace dashboard...");

        // Spinner loadings
        ["orchestrator-dashboard", "orchestrator-history", "orchestrator-agent-cards"].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = `<div style="padding:var(--space-6); text-align:center; color:var(--text-muted);"><i class="fa-solid fa-spinner fa-spin" style="font-size:1.5rem;"></i></div>`;
        });

        // Blank flow viewers
        window.WorkflowViewer.render("orchestrator-flow-viewer", []);
        window.ExecutionTimeline.render("orchestrator-latency-timeline", []);
        window.DecisionPanel.render("orchestrator-decision-panel", null);

        try {
            _data = await apiFetch("/api/orchestrator/dashboard");

            // 1. Dashboard KPI stats widgets
            renderDashboardKPIs(_data.metrics);

            // 2. Agent cards list registry
            window.AgentCards.render("orchestrator-agent-cards", _data.agents);

            // 3. Prior execution history
            window.WorkflowHistory.render("orchestrator-history", _data.history);

        } catch (err) {
            console.error("[AIOrchestrator] Initialization Error:", err);
            const el = document.getElementById("orchestrator-dashboard");
            if (el) el.innerHTML = `<div class="card glass-panel" style="padding:var(--space-6); text-align:center; color:var(--danger-color);">
                <i class="fa-solid fa-triangle-exclamation"></i> Failed to load AI Orchestrator Dashboard.
            </div>`;
        }
    }

    function renderDashboardKPIs(metrics) {
        const el = document.getElementById("orchestrator-dashboard");
        if (!el || !metrics) return;

        el.innerHTML = `
            <div class="grid-layout cols-4" style="margin-bottom:var(--space-5);">
                <div class="metric-card glass-panel fade-in-slide-up">
                    <span class="metric-label">Active AI Workflows</span>
                    <span class="metric-value text-primary">${metrics.active_workflows}</span>
                    <span class="metric-sub">Currently running parallel tasks</span>
                </div>
                <div class="metric-card glass-panel fade-in-slide-up">
                    <span class="metric-label">Avg Decision Time</span>
                    <span class="metric-value text-success">${metrics.avg_decision_time_ms}ms</span>
                    <span class="metric-sub">Across all compiled pipelines</span>
                </div>
                <div class="metric-card glass-panel fade-in-slide-up">
                    <span class="metric-label">Optimization Success Rate</span>
                    <span class="metric-value text-success">${metrics.optimization_success_rate}%</span>
                    <span class="metric-sub">Conflict resolutions completed</span>
                </div>
                <div class="metric-card glass-panel fade-in-slide-up">
                    <span class="metric-label">Workflow Success %</span>
                    <span class="metric-value text-primary">${metrics.workflow_success_pct}%</span>
                    <span class="metric-sub">Target validation accuracy</span>
                </div>
            </div>
        `;
    }

    async function triggerOrchestratorWorkflow() {
        console.log("[AIOrchestrator] Triggering optimization workflow pipeline...");

        const runBtn = document.getElementById("trigger-workflow-btn");
        if (runBtn) {
            runBtn.disabled = true;
            runBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Running Pipeline...`;
        }

        try {
            const runResult = await apiFetch("/api/orchestrator/run", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ include_reverse: true, filters: window.GlobalFilters || {} })
            });

            // Refresh steps list & timeline chart & decision metrics panel
            window.WorkflowViewer.render("orchestrator-flow-viewer", runResult.execution_steps);
            window.ExecutionTimeline.render("orchestrator-latency-timeline", runResult.execution_steps);
            window.DecisionPanel.render("orchestrator-decision-panel", runResult.decision);

            // Re-fetch dashboard log history
            try {
                const refreshed = await apiFetch("/api/orchestrator/dashboard");
                renderDashboardKPIs(refreshed.metrics);
                window.AgentCards.render("orchestrator-agent-cards", refreshed.agents);
                window.WorkflowHistory.render("orchestrator-history", refreshed.history);
            } catch (_) {}

            // Small toast notification
            const toast = document.createElement("div");
            toast.style.cssText = `position:fixed; bottom:20px; right:20px; background:rgba(16,185,129,0.9); color:#fff;
                                   padding:10px 16px; border-radius:8px; font-size:12px; z-index:9999;
                                   animation: fadeIn 0.3s ease;`;
            toast.textContent = `✓ Workflow ${runResult.workflow_id} executed successfully!`;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);

        } catch (err) {
            console.error("[AIOrchestrator] Workflow Run Error:", err);
            alert("Orchestration pipeline execution failed. Please verify API logs.");
        } finally {
            if (runBtn) {
                runBtn.disabled = false;
                runBtn.innerHTML = `<i class="fa-solid fa-bolt"></i> Run Optimization Workflow`;
            }
        }
    }

    window.loadAIOrchestratorWorkspace = initAIOrchestratorWorkspace;
    window.triggerOrchestratorWorkflow = triggerOrchestratorWorkflow;
})();
