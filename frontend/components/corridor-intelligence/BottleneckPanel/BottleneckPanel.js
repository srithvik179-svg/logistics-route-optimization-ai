/**
 * BottleneckPanel Component
 * Renders warning alert blocks for detected bottlenecks.
 */
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
                            No critical bottlenecks detected. Corridors are clear.
                        </div>
                    </div>
                `;
                return;
            }

            let itemsHtml = "";
            bottlenecks.forEach(b => {
                let badgeClass = "warning";
                let icon = "fa-triangle-exclamation";
                if (b.severity === "Critical") {
                    badgeClass = "danger";
                    icon = "fa-circle-xmark";
                } else if (b.severity === "Low") {
                    badgeClass = "info";
                    icon = "fa-circle-info";
                }

                itemsHtml += `
                    <div class="bottleneck-card-alert" style="display: flex; gap: var(--space-3); padding: var(--space-3); background: rgba(9, 9, 11, 0.4); border: 1px solid rgba(63, 63, 70, 0.3); border-radius: var(--radius-md); align-items: start;">
                        <i class="fa-solid ${icon} text-${badgeClass}" style="margin-top: 2px;"></i>
                        <div style="display: flex; flex-direction: column; gap: 2px;">
                            <span style="font-size: var(--font-size-xs); font-weight: var(--font-weight-bold); color: var(--text-primary);">${b.corridor}</span>
                            <span style="font-size: 10px; color: var(--text-muted); font-weight: var(--font-weight-medium);">${b.type} — <strong class="text-${badgeClass}">${b.severity}</strong></span>
                            <p style="font-size: 11px; color: var(--text-secondary); margin: var(--space-1) 0 0 0; line-height: 1.4;">${b.details}</p>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="height: 100%;">
                    <div class="card-header">
                        <h3><i class="fa-solid fa-triangle-exclamation text-danger"></i> Active Bottleneck Audit</h3>
                    </div>
                    <div class="card-body" style="padding: var(--space-3); display: flex; flex-direction: column; gap: var(--space-3); max-height: 380px; overflow-y: auto;">
                        ${itemsHtml}
                    </div>
                </div>
            `;
        }
    };
    window.BottleneckPanel = BottleneckPanel;
})();
