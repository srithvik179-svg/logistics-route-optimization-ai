/**
 * RoutePanel Component
 * Displays detail cards for selected corridors (cost, transit, risk, alternative routes) and wires route playback triggers.
 */
(function() {
    let _activeFlow = null;

    const RoutePanel = {
        render(containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;

            container.innerHTML = `
                <div id="route-panel-overlay" class="card glass-panel" style="display:none; padding:var(--space-3); border:1px solid rgba(63,63,70,0.4); max-height:400px; overflow-y:auto;">
                    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(63,63,70,0.4); padding-bottom:var(--space-2); margin-bottom:var(--space-3);">
                        <h4 id="route-panel-title" style="margin:0; color:#fff; font-size:var(--font-size-md);">Corridor Details</h4>
                        <button class="btn btn-secondary btn-sm" onclick="RoutePanel.close()" style="padding:2px 6px;"><i class="fa-solid fa-xmark"></i></button>
                    </div>
                    <div id="route-panel-content" style="display:flex; flex-direction:column; gap:var(--space-3);">
                        <!-- Dynamic details injected here -->
                    </div>
                </div>
            `;
        },

        show(flow) {
            _activeFlow = flow;
            const overlay = document.getElementById("route-panel-overlay");
            if (!overlay) return;

            overlay.style.display = "block";

            const title = document.getElementById("route-panel-title");
            title.innerHTML = `<i class="fa-solid fa-circle-nodes text-primary"></i> ${flow.corridor || (flow.origin + ' → ' + flow.destination)}`;

            const isHighRisk = flow.missed_sla > 0 || (flow.risk_score && flow.risk_score > 60);

            const content = document.getElementById("route-panel-content");
            content.innerHTML = `
                <div style="display:flex; justify-content:space-between; font-size:11px;">
                    <span style="color:var(--text-muted);">Origin:</span>
                    <span style="color:#fff; font-weight:bold;">${flow.origin}</span>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:11px;">
                    <span style="color:var(--text-muted);">Destination:</span>
                    <span style="color:#fff; font-weight:bold;">${flow.destination}</span>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:11px;">
                    <span style="color:var(--text-muted);">Active Shipments:</span>
                    <span style="color:#fff; font-weight:bold;">${flow.shipment_count}</span>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:11px;">
                    <span style="color:var(--text-muted);">Avg Logistics Cost:</span>
                    <span style="color:#fff; font-weight:bold;">$${flow.avg_cost || flow.shipment_cost || 0.0}</span>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:11px;">
                    <span style="color:var(--text-muted);">Avg Transit Time:</span>
                    <span style="color:#fff; font-weight:bold;">${flow.avg_transit_days || 0.0} days</span>
                </div>

                <div style="display:flex; justify-content:space-between; font-size:11px; border-top:1px solid rgba(63,63,70,0.2); padding-top:var(--space-2);">
                    <span style="color:var(--text-muted);">SLA Status:</span>
                    <span style="color:${isHighRisk ? 'var(--danger-color)' : 'var(--success-color)'}; font-weight:bold;">
                        ${isHighRisk ? 'Risk Violation Warning' : 'SLA Target Met'}
                    </span>
                </div>

                <div style="display:flex; flex-direction:column; gap:var(--space-2); margin-top:var(--space-2);">
                    <button class="btn btn-primary btn-sm" onclick="RoutePanel.startPlayback()" style="width:100%;">
                        <i class="fa-solid fa-play"></i> Initialize Route Playback
                    </button>
                </div>
            `;
        },

        startPlayback() {
            if (!_activeFlow) return;
            
            // Build temporary segment coordinates along path
            const startLatLng = [_activeFlow.start_lat || 20.0, _activeFlow.start_lon || 78.0];
            const endLatLng = [_activeFlow.end_lat || 20.0, _activeFlow.end_lon || 78.0];

            // Generate intermediate points for smooth animation
            const latlngs = [];
            const steps = 15;
            for (let i = 0; i <= steps; i++) {
                const ratio = i / steps;
                const lat = startLatLng[0] + (_activeFlow.end_lat - _activeFlow.start_lat) * ratio;
                const lon = startLatLng[1] + (_activeFlow.end_lon - _activeFlow.start_lon) * ratio;
                latlngs.push([lat, lon]);
            }

            if (window.RoutePlayback) {
                window.RoutePlayback.setupRoute(latlngs, _activeFlow.corridor || "Custom Corridor");
                window.RoutePlayback.togglePlay();
            }
        },

        close() {
            const overlay = document.getElementById("route-panel-overlay");
            if (overlay) overlay.style.display = "none";
        }
    };

    window.RoutePanel = RoutePanel;
})();
