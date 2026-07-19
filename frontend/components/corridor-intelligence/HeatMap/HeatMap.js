/**
 * HeatMap Component
 * Visualizes logistics corridors on a Leaflet map using shipment volume and efficiency scales.
 */
(function() {
    const HeatMap = {
        map: null,
        layers: [],
        nodeCoords: {},

        init(containerId) {
            if (this.map) {
                setTimeout(() => this.map.invalidateSize(), 100);
                return;
            }

            this.map = L.map(containerId).setView([31.9686, -99.9018], 6);
            L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
                attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
                subdomains: 'abcd',
                maxZoom: 20
            }).addTo(this.map);
        },

        drawCorridors(corridors, nodes) {
            if (!this.map) return;

            // Clear previous layers
            this.layers.forEach(layer => this.map.removeLayer(layer));
            this.layers = [];

            // Build node coordinates cache
            this.nodeCoords = {};
            nodes.forEach(n => {
                this.nodeCoords[n.id] = [n.latitude, n.longitude];
            });

            if (corridors.length === 0) return;

            const bounds = [];

            // Draw corridor lanes
            corridors.forEach(c => {
                const origCoord = this.nodeCoords[c.origin];
                const destCoord = this.nodeCoords[c.destination];

                if (!origCoord || !destCoord) return;

                bounds.push(origCoord);
                bounds.push(destCoord);

                // Determine color based on Efficiency Score
                const eff = c.efficiency_score;
                let color = "#10b981"; // Green
                if (eff < 50.0) {
                    color = "#ef4444"; // Red
                } else if (eff < 75.0) {
                    color = "#f59e0b"; // Orange
                }

                // Thickness based on Shipment Volume
                const vol = c.shipment_count;
                const weight = Math.max(3, Math.min(12, 2 + (vol * 1.5)));

                const poly = L.polyline([origCoord, destCoord], {
                    color: color,
                    weight: weight,
                    opacity: 0.75,
                    lineJoin: "round"
                }).addTo(this.map);

                // Detailed tooltip layout
                const tooltipHtml = `
                    <div style="font-family: sans-serif; font-size: 11px; padding: 4px;">
                        <strong style="color:var(--brand-blue);">${c.origin} → ${c.destination}</strong><br>
                        <strong>Efficiency Score:</strong> ${eff.toFixed(1)}%<br>
                        <strong>Shipments Load:</strong> ${vol} units<br>
                        <strong>Avg Delay Rate:</strong> ${c.delay_rate.toFixed(1)}%<br>
                        <strong>Transportation Cost:</strong> $${c.avg_cost.toFixed(2)}<br>
                        <strong>Transit Duration:</strong> ${c.transit_time.toFixed(1)} days
                    </div>
                `;

                poly.bindTooltip(tooltipHtml, { sticky: true });
                this.layers.push(poly);
            });

            // Draw Hub markers with congestion overlays
            nodes.forEach(n => {
                const coord = [n.latitude, n.longitude];
                
                // Identify congestion if there are active delays on corridors starting/ending here
                const hubCorridors = corridors.filter(c => c.origin === n.id || c.destination === n.id);
                const avgCongestion = hubCorridors.length > 0 
                    ? hubCorridors.reduce((sum, curr) => sum + curr.congestion_score, 0) / hubCorridors.length
                    : 0;

                const isCongested = avgCongestion > 60;
                
                const marker = L.circleMarker(coord, {
                    radius: isCongested ? 8 : 5,
                    color: isCongested ? "var(--danger-color)" : "var(--brand-blue)",
                    fillColor: "#09090b",
                    fillOpacity: 1,
                    weight: 2
                }).addTo(this.map);

                // Add pulsing classes for congested hubs
                if (isCongested) {
                    setTimeout(() => {
                        const el = marker.getElement();
                        if (el) el.classList.add("hub-congestion-pulsing");
                    }, 100);
                }

                marker.bindTooltip(`<strong>Hub:</strong> ${n.name}<br><strong>Network Congestion:</strong> ${avgCongestion.toFixed(0)}/100`, { direction: "top" });
                this.layers.push(marker);
            });

            if (bounds.length >= 2) {
                this.map.fitBounds(L.latLngBounds(bounds), { padding: [30, 30] });
            }
        }
    };
    window.HeatMap = HeatMap;
})();
