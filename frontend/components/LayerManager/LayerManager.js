/**
 * LayerManager Component
 * Side overlay widget allowing users to select active network and analytics map layers.
 */
(function() {
    const LayerManager = {
        render(containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;

            container.innerHTML = `
                <div class="card glass-panel layer-manager-card" style="padding:var(--space-3); border:1px solid rgba(63,63,70,0.4);">
                    <div style="font-size:11px; font-weight:bold; color:#fff; text-transform:uppercase; margin-bottom:var(--space-2); display:flex; justify-content:space-between; align-items:center;">
                        <span><i class="fa-solid fa-layer-group text-primary"></i> Layer Manager</span>
                        <span style="font-size:9px; color:var(--text-muted);">Active layers</span>
                    </div>
                    <div style="display:flex; flex-direction:column; gap:6px;">
                        <label class="layer-checkbox-label">
                            <input type="checkbox" checked onchange="NetworkExplorer.toggleLayer('hubs', this.checked)">
                            <span>Hub Locations</span>
                        </label>
                        <label class="layer-checkbox-label">
                            <input type="checkbox" checked onchange="NetworkExplorer.toggleLayer('tprs', this.checked)">
                            <span>Repair Centers (TPRs)</span>
                        </label>
                        <label class="layer-checkbox-label">
                            <input type="checkbox" checked onchange="NetworkExplorer.toggleLayer('flows', this.checked)">
                            <span>Active Route Flows</span>
                        </label>
                        <label class="layer-checkbox-label">
                            <input type="checkbox" onchange="NetworkExplorer.toggleLayer('congestion', this.checked)">
                            <span class="text-danger"><i class="fa-solid fa-triangle-exclamation"></i> Congestion Overlays</span>
                        </label>
                        <label class="layer-checkbox-label">
                            <input type="checkbox" onchange="NetworkExplorer.toggleLayer('riskZones', this.checked)">
                            <span class="text-warning"><i class="fa-solid fa-circle-radiation"></i> SLA Risk Heatmap</span>
                        </label>
                    </div>
                </div>
            `;

            if (!document.getElementById("layer-manager-styles")) {
                const style = document.createElement("style");
                style.id = "layer-manager-styles";
                style.textContent = `
                    .layer-checkbox-label {
                        display: flex; align-items: center; gap: 8px;
                        font-size: 11px; color: var(--text-secondary); cursor: pointer;
                        user-select: none; transition: color 0.2s ease;
                    }
                    .layer-checkbox-label:hover {
                        color: #fff;
                    }
                    .layer-checkbox-label input[type="checkbox"] {
                        accent-color: var(--primary-color);
                    }
                `;
                document.head.appendChild(style);
            }

            console.log("[LayerManager] Rendered layer checkboxes.");
        }
    };

    window.LayerManager = LayerManager;
})();
