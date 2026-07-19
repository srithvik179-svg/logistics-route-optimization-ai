/**
 * WorkflowHistory Component
 * Lists prior multi-agent orchestrator runs and execution duration logs.
 */
(function() {
    const WorkflowHistory = {
        render(containerId, history) {
            const el = document.getElementById(containerId);
            if (!el) return;

            if (!history || !history.length) {
                el.innerHTML = `
                    <div class="card glass-panel" style="padding:var(--space-6); text-align:center; color:var(--text-muted); font-size:11px;">
                        No history records registered.
                    </div>`;
                return;
            }

            const listHtml = history.map(h => {
                const badge = h.status === "Success" ? "badge-success" : "badge-danger";
                return `
                    <div style="padding:var(--space-3); background:rgba(9, 9, 11, 0.4); border:1px solid rgba(63, 63, 70, 0.3); border-radius:var(--radius-md); display:flex; flex-direction:column; gap:4px; margin-bottom:var(--space-2);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <code style="font-size:10px; font-weight:600; color:var(--text-secondary);">${h.id}</code>
                            <span class="badge ${badge}" style="font-size:8px; padding:1px 5px;">${h.status}</span>
                        </div>
                        <div style="font-size:10px; color:var(--text-muted);">
                            Executed: ${h.time.replace("T", " ")} (${h.duration_ms}ms)
                        </div>
                        <p style="margin:4px 0 0 0; font-size:11px; color:var(--text-secondary); line-height:1.4;">${h.summary}</p>
                    </div>
                `;
            }).join("");

            el.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="height:100%;">
                    <div class="card-header">
                        <h3><i class="fa-solid fa-history text-primary"></i> Execution History Logs</h3>
                    </div>
                    <div class="card-body" style="padding:var(--space-3); max-height:430px; overflow-y:auto;">
                        ${listHtml}
                    </div>
                </div>
            `;
        }
    };
    window.WorkflowHistory = WorkflowHistory;
})();
