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
        "HUB-BLR": [12.9716, 77.5946],
        "HUB-DEL": [28.6139, 77.2090],
        "HUB-MUM": [19.0760, 72.8777],
        "HUB-CHE": [13.0827, 80.2707],
        "HUB-HYD": [17.3850, 78.4867],
        "HUB-KOL": [22.5726, 88.3639],
        "HUB-PUN": [18.5204, 73.8567],
        "HUB-AHM": [23.0225, 72.5714],
        "HUB-JAI": [26.9124, 75.7873],
        "HUB-LKO": [26.8467, 80.9462],
        "TPR-BLR-01": [12.9716, 77.5946],
        "TPR-HYD-01": [17.3850, 78.4867],
        "TPR-DEL-01": [28.6139, 77.2090],
        "TPR-CHE-01": [13.0827, 80.2707],
        "TPR-MUM-01": [19.0760, 72.8777]
    };

    const ReverseMap = {
        init(mapId) {
            const el = document.getElementById(mapId);
            if (!el) return;
            if (_map) { _map.remove(); _map = null; }

            _map = L.map(mapId, { zoomControl: true, attributionControl: false }).setView([20.5937, 78.9629], 5);

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

        render(returns, nodeCoordinates = null) {
            if (!_map) return;

            // Clear existing layers
            _polylines.forEach(p => p.remove());
            _markers.forEach(m => m.remove());
            _polylines = []; _markers = [];

            // Resolve coordinates mapping
            const coordsLookup = nodeCoordinates || HUB_COORDS;

            // Draw hub markers
            Object.entries(coordsLookup).forEach(([hub, coords]) => {
                if (hub.toUpperCase().startsWith("TPR")) return; // skip repair centers

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

            // Draw dynamic special markers for Repair/Refurbishment/Recycling Centers
            Object.entries(coordsLookup).forEach(([nodeId, coords]) => {
                if (!nodeId.toUpperCase().startsWith("TPR")) return;

                const isRecycle = nodeId.endsWith("02") || nodeId.includes("RECYCLE");
                const color = isRecycle ? "#06b6d4" : "#10b981";
                const fillColor = isRecycle ? "#0c4a6e" : "#065f46";
                const centerType = isRecycle ? "Recycling Center" : "Refurbishment Center";

                const marker = L.circleMarker(coords, {
                    radius: 12, color, fillColor, fillOpacity: 0.9, weight: 2
                }).addTo(_map);
                marker.bindPopup(`<strong style="color:${color};">${nodeId}</strong><br><span style="font-size:10px; color:#a1a1aa;">${centerType}</span>`);
                _markers.push(marker);
            });

            // Draw return flow polylines
            returns.forEach(ret => {
                const origCoords = coordsLookup[ret.origin];
                const destCoords = coordsLookup[ret.destination];
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
