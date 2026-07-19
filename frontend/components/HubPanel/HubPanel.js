/**
 * HubPanel Component
 * Displays contextual analytics, utilization meters, and connected routes when a hub or repair center is clicked.
 */
(function() {
    const HubPanel = {
        render(containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;

            // Renders empty/collapsed container
            container.innerHTML = `
                <div id="hub-panel-overlay" class="card glass-panel hub-panel-overlay-hidden" style="display:none; padding:var(--space-3); border:1px solid rgba(63,63,70,0.4); max-height:400px; overflow-y:auto;">
                    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(63,63,70,0.4); padding-bottom:var(--space-2); margin-bottom:var(--space-3);">
                        <h4 id="hub-panel-title" style="margin:0; color:#fff; font-size:var(--font-size-md);">Hub Details</h4>
                        <button class="btn btn-secondary btn-sm" onclick="HubPanel.close()" style="padding:2px 6px;"><i class="fa-solid fa-xmark"></i></button>
                    </div>
                    <div id="hub-panel-content" style="display:flex; flex-direction:column; gap:var(--space-3);">
                        <!-- Dynamic details injected here -->
                    </div>
                </div>
            `;
        },

        show(node) {
            const overlay = document.getElementById("hub-panel-overlay");
            if (!overlay) return;

            overlay.style.display = "block";

            const title = document.getElementById("hub-panel-title");
            title.innerHTML = `<i class="fa-solid fa-square-poll-vertical text-primary"></i> ${node.name || node.id}`;

            const isRC = node.type === "Repair Center";
            const utilizationColor = node.utilization > 80 ? "var(--danger-color)" : (node.utilization > 50 ? "var(--warning-color)" : "var(--success-color)");

            const content = document.getElementById("hub-panel-content");
            content.innerHTML = `
                <div style="display:flex; justify-content:space-between; font-size:11px;">
                    <span style="color:var(--text-muted);">Asset Type:</span>
                    <span style="color:#fff; font-weight:bold;">${node.type}</span>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:11px;">
                    <span style="color:var(--text-muted);">Location:</span>
                    <span style="color:#fff;">${node.city || 'N/A'}, ${node.state || 'N/A'}</span>
                </div>
                
                <div style="margin-top:var(--space-2);">
                    <div style="display:flex; justify-content:space-between; font-size:10px; margin-bottom:4px;">
                        <span style="color:var(--text-muted);">Capacity Utilization:</span>
                        <span style="color:${utilizationColor}; font-weight:bold;">${node.utilization}%</span>
                    </div>
                    <div style="width:100%; height:6px; background:rgba(63,63,70,0.6); border-radius:3px; overflow:hidden;">
                        <div style="width:${node.utilization}%; height:100%; background:${utilizationColor}; border-radius:3px;"></div>
                    </div>
                </div>

                <div style="display:flex; flex-direction:column; gap:4px; margin-top:var(--space-2); background:rgba(9,9,11,0.4); padding:6px; border-radius:4px; border:1px solid rgba(63,63,70,0.2);">
                    <div style="font-size:10px; font-weight:bold; color:var(--text-secondary); text-transform:uppercase;">
                        <i class="fa-solid fa-circle-info"></i> ${isRC ? 'Supported Part Types' : 'Operational Status'}
                    </div>
                    <div style="font-size:11px; color:#fff;">
                        ${isRC ? node.supported_parts.join(', ') : (node.inventory_summary || 'Normal operations')}
                    </div>
                </div>

                <div style="display:flex; flex-direction:column; gap:var(--space-1); margin-top:var(--space-2);">
                    <div style="font-size:10px; font-weight:bold; color:var(--text-secondary); text-transform:uppercase;">AI Optimization Target</div>
                    <p style="font-size:11px; color:var(--text-muted); line-height:1.4; margin:0;">
                        ${node.utilization > 80 
                            ? 'Congestion exceeds critical threshold. Shift inbound flows to neighboring hubs using Genetic Optimizer.' 
                            : 'Asset health stable. Optimal loading configuration maintained.'}
                    </p>
                </div>
            `;
        },

        close() {
            const overlay = document.getElementById("hub-panel-overlay");
            if (overlay) overlay.style.display = "none";
        }
    };

    window.HubPanel = HubPanel;
})();
