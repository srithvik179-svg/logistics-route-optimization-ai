/**
 * ReverseMap Component
 * Renders Leaflet map showing return shipment flows, refurbishment hubs, and recycling centers.
 */
(function() {
    let _map = null;
    let _polylines = [];
    let _markers = [];

    const STATUS_COLORS = {
        "Pending": "#ef4444",
        "In Transit": "#f97316",
        "Processing": "#3b82f6",
        "Refurbished": "#10b981",
        "Recycled": "#06b6d4"
    };

    const HUB_COORDS = {
        "HUB-A": [30.2672, -97.7431],  // Austin, TX
        "HUB-B": [29.7604, -95.3698],  // Houston, TX
        "HUB-C": [32.7767, -96.7970],  // Dallas, TX
        "HUB-D": [29.4241, -98.4936],  // San Antonio, TX
        "HUB-E": [35.2271, -101.8313]  // Amarillo, TX
    };

    const ReverseMap = {
        init(mapId) {
            const el = document.getElementById(mapId);
            if (!el) return;
            if (_map) { _map.remove(); _map = null; }

            _map = L.map(mapId, { zoomControl: true, attributionControl: false }).setView([31.5, -97.5], 6);

            L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
                subdomains: "abcd", maxZoom: 19
            }).addTo(_map);

            // Legend
            const legend = L.control({ position: "bottomright" });
            legend.onAdd = function() {
                const div = L.DomUtil.create("div", "reverse-map-legend");
                div.innerHTML = `
                    <strong style="font-size:10px; color:#d4d4d8;">Return Status</strong><br>
                    ${Object.entries(STATUS_COLORS).map(([s, c]) =>
                        `<span style="display:inline-block; width:10px; height:10px; background:${c}; border-radius:50%; margin-right:4px;"></span>
                         <span style="font-size:9px; color:#a1a1aa;">${s}</span><br>`
                    ).join("")}
                `;
                div.style.cssText = "background:rgba(9,9,11,0.85); padding:8px 10px; border-radius:8px; border:1px solid rgba(63,63,70,0.4);";
                return div;
            };
            legend.addTo(_map);
        },

        render(returns) {
            if (!_map) return;

            // Clear existing layers
            _polylines.forEach(p => p.remove());
            _markers.forEach(m => m.remove());
            _polylines = []; _markers = [];

            // Draw hub markers
            Object.entries(HUB_COORDS).forEach(([hub, coords]) => {
                const marker = L.circleMarker(coords, {
                    radius: 8, color: "#3b82f6", fillColor: "#1d4ed8",
                    fillOpacity: 0.9, weight: 2
                }).addTo(_map);
                marker.bindPopup(`<strong style="color:#fff;">${hub}</strong><br><span style="font-size:10px; color:#a1a1aa;">Network Hub</span>`);
                _markers.push(marker);

                const label = L.tooltip({ permanent: true, direction: "top", className: "hub-tooltip" })
                    .setContent(`<span style="font-size:9px; font-weight:600;">${hub}</span>`);
                marker.bindTooltip(label);
            });

            // Draw special markers for Refurbishment and Recycling Centers
            const refurbMarker = L.circleMarker([30.2672, -97.7431], {
                radius: 12, color: "#10b981", fillColor: "#065f46", fillOpacity: 0.9, weight: 2
            }).addTo(_map);
            refurbMarker.bindPopup(`<strong style="color:#10b981;">Austin Refurbishment Center</strong><br><span style="font-size:10px; color:#a1a1aa;">Primary recovery facility</span>`);
            _markers.push(refurbMarker);

            const recycleMarker = L.circleMarker([29.7604, -95.3698], {
                radius: 12, color: "#06b6d4", fillColor: "#0c4a6e", fillOpacity: 0.9, weight: 2
            }).addTo(_map);
            recycleMarker.bindPopup(`<strong style="color:#06b6d4;">Houston Recycling Center</strong><br><span style="font-size:10px; color:#a1a1aa;">Certified green recycling hub</span>`);
            _markers.push(recycleMarker);

            // Draw return flow polylines
            returns.forEach(ret => {
                const origCoords = HUB_COORDS[ret.origin];
                const destCoords = HUB_COORDS[ret.destination];
                if (!origCoords || !destCoords) return;

                const color = STATUS_COLORS[ret.status] || "#6b7280";
                const line = L.polyline([origCoords, destCoords], {
                    color, weight: 2.5, opacity: 0.75, dashArray: "6 4"
                }).addTo(_map);

                line.bindPopup(`
                    <div style="font-size:11px; line-height:1.5;">
                        <strong style="color:#fff;">${ret.return_id}</strong><br>
                        <span style="color:#a1a1aa;">Route: ${ret.origin} → ${ret.destination}</span><br>
                        <span style="color:${color};">● ${ret.status}</span><br>
                        <span style="color:#a1a1aa;">Reason: ${ret.reason}</span>
                    </div>
                `);
                _polylines.push(line);
            });
        }
    };

    window.ReverseMap = ReverseMap;
})();
