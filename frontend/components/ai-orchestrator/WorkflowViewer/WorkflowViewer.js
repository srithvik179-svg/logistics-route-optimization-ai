/**
 * WorkflowViewer Component
 * Interactive flowchart that visualizes the multi-agent pipeline stages.
 */
(function() {
    const WorkflowViewer = {
        render(containerId, executionSteps) {
            const el = document.getElementById(containerId);
            if (!el) return;

            if (!executionSteps || !executionSteps.length) {
                el.innerHTML = `
                    <div class="card glass-panel" style="padding:var(--space-6); text-align:center; color:var(--text-muted);">
                        <i class="fa-solid fa-play-circle" style="font-size:2.5rem; margin-bottom:var(--space-3); color:var(--text-muted); display:block;"></i>
                        Ready to trigger orchestration. Click "Run Optimization Workflow" above.
                    </div>`;
                return;
            }

            const stepsHtml = executionSteps.map((step, idx) => {
                const isLast = idx === executionSteps.length - 1;
                return `
                    <div style="display:flex; flex-direction:column; align-items:center; position:relative; flex:1; min-width:130px;">
                        <!-- Agent Node Card -->
                        <div class="card glass-panel fade-in-slide-up" 
                             style="width:100%; padding:var(--space-2) var(--space-3); border:1px solid rgba(16, 185, 129, 0.4); background:rgba(16, 185, 129, 0.05); text-align:center; position:relative; z-index:2; cursor:pointer;"
                             onclick="WorkflowViewer.showDetail('${step.name}', '${step.data_used}', '${step.explanation.replace(/'/g, "\\'")}', ${step.duration_ms})">
                            <span class="badge badge-success" style="font-size:8px; margin-bottom:4px;">Step ${idx + 1}</span>
                            <div style="font-weight:600; font-size:11px; color:#fff; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${step.name}</div>
                            <div style="font-size:9px; color:#10b981; margin-top:2px;"><i class="fa-solid fa-clock"></i> ${step.duration_ms}ms</div>
                        </div>

                        <!-- Directional Arrow to next node -->
                        ${!isLast ? `
                        <div class="arrow-connector" style="position:absolute; right:-20px; top:50%; transform:translateY(-50%); z-index:1; color:rgba(16, 185, 129, 0.6); font-size:14px;">
                            <i class="fa-solid fa-arrow-right"></i>
                        </div>` : ''}
                    </div>
                `;
            }).join("");

            el.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="border:1px solid rgba(63, 63, 70, 0.4);">
                    <div class="card-header">
                        <h3><i class="fa-solid fa-sitemap text-primary"></i> Multi-Agent Execution Path Flowchart</h3>
                    </div>
                    <div class="card-body" style="padding:var(--space-4); overflow-x:auto;">
                        <div style="display:flex; gap:30px; align-items:center; min-width:800px; padding:var(--space-2) 0;">
                            ${stepsHtml}
                        </div>
                        <div id="workflow-node-detail" style="margin-top:var(--space-4); padding:var(--space-3); background:rgba(9, 9, 11, 0.5); border:1px solid rgba(63, 63, 70, 0.3); border-radius:var(--radius-md); display:none;">
                            <h4 id="node-detail-title" style="margin:0 0 var(--space-1) 0; color:var(--text-primary); font-size:var(--font-size-sm);"></h4>
                            <p style="margin:0 0 4px 0; font-size:11px; color:var(--text-muted);">Data Source: <code id="node-detail-data" style="color:var(--text-secondary);"></code></p>
                            <p id="node-detail-desc" style="margin:0; font-size:11px; color:var(--text-secondary); line-height:1.5;"></p>
                        </div>
                    </div>
                </div>
            `;
        },

        showDetail(name, dataUsed, desc, duration) {
            const panel = document.getElementById("workflow-node-detail");
            const title = document.getElementById("node-detail-title");
            const data = document.getElementById("node-detail-data");
            const descEl = document.getElementById("node-detail-desc");

            if (!panel || !title || !data || !descEl) return;

            title.textContent = `${name} (Latency: ${duration}ms)`;
            data.textContent = dataUsed;
            descEl.textContent = desc;
            panel.style.display = "block";
        }
    };
    window.WorkflowViewer = WorkflowViewer;
})();
