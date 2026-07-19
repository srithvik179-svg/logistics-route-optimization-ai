/**
 * RiskHeatmap Component
 * Leaflet map overlay showing high-risk corridors, congested hubs, and delayed shipments.
 */
(function() {
    let _map = null;
    let _layers = [];

    const HUB_COORDS = {
        "HUB-A": [30.2672, -97.7431],
        "HUB-B": [29.7604, -95.3698],
        "HUB-C": [32.7767, -96.7970],
        "HUB-D": [29.4241, -98.4936],
        "HUB-E": [35.2271, -101.8313]
    };

    const RiskHeatmap = {
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
                const div = L.DomUtil.create("div");
                div.style.cssText = "background:rgba(9,9,11,0.85);padding:8px 10px;border-radius:8px;border:1px solid rgba(63,63,70,0.4);font-size:9px;color:#a1a1aa;";
                div.innerHTML = `<strong style="color:#d4d4d8;">Risk Level</strong><br>
                    <span style="color:#ef4444;">● Critical</span>&nbsp;
                    <span style="color:#f97316;">● High</span>&nbsp;
                    <span style="color:#f59e0b;">● Moderate</span>&nbsp;
                    <span style="color:#06b6d4;">● Low</span>`;
                return div;
            };
            legend.addTo(_map);
        },

        render(shipments, hubs, corridors) {
            if (!_map) return;
            _layers.forEach(l => l.remove());
            _layers = [];

            // Hub circles — size/color by risk score
            hubs.forEach(h => {
                const coords = HUB_COORDS[h.hub];
                if (!coords) return;
                const radius = 8 + (h.risk_score / 100) * 16;
                const circle = L.circleMarker(coords, {
                    radius, color: h.risk_color, fillColor: h.risk_color,
                    fillOpacity: 0.35, weight: 2
                }).addTo(_map);
                circle.bindPopup(`
                    <div style="font-size:11px;line-height:1.6;">
                        <strong style="color:#fff;">${h.hub}</strong><br>
                        <span style="color:${h.risk_color};">● ${h.risk_level} Risk</span><br>
                        Risk Score: <strong>${h.risk_score}</strong><br>
                        Capacity: ${h.capacity_utilization}%&nbsp;|&nbsp;SLA Miss: ${h.miss_rate}%
                    </div>`);
                _layers.push(circle);
            });

            // Corridor lines — color/weight by risk score
            corridors.forEach(c => {
                const orig = HUB_COORDS[c.origin];
                const dest = HUB_COORDS[c.destination];
                if (!orig || !dest) return;
                const weight = 2 + (c.risk_score / 100) * 5;
                const line = L.polyline([orig, dest], {
                    color: c.risk_color, weight, opacity: 0.8,
                    dashArray: c.risk_level === "Critical" ? null : "8 4"
                }).addTo(_map);
                line.bindPopup(`
                    <div style="font-size:11px;line-height:1.6;">
                        <strong style="color:#fff;">${c.corridor}</strong><br>
                        <span style="color:${c.risk_color};">● ${c.risk_level}</span>
                        &nbsp;| Score: <strong>${c.risk_score}</strong><br>
                        SLA Miss: ${c.miss_rate}%&nbsp;|&nbsp;Trend: ${c.risk_trend}
                    </div>`);
                _layers.push(line);
            });
        }
    };
    window.RiskHeatmap = RiskHeatmap;
})();
