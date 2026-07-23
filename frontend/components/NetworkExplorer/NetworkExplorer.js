/**
 * NetworkExplorer Component
 * Central map container utilizing Leaflet to plot nodes, routes, alternatives, and overlays.
 */
(function() {
    let _map = null;
    let _layers = {
        hubs: L.layerGroup(),
        tprs: L.layerGroup(),
        flows: L.layerGroup(),
        alternatives: L.layerGroup(),
        playback: L.layerGroup(),
        congestion: L.layerGroup(),
        riskZones: L.layerGroup(),
        heatmap: L.layerGroup()
    };
    let _currentTileLayer = null;
    let _rawNetworkData = null;

    const MapStyle = {
        dark: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        light: "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
    };

    const NetworkExplorer = {
        init(containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;

            if (_map) {
                _map.remove();
                _map = null;
            }

            // Initial center coordinates (India-focused for actual Dell dataset, default zoom out)
            _map = L.map(containerId, {
                zoomControl: false,
                attributionControl: false,
                maxZoom: 18,
                minZoom: 2
            }).setView([20.5937, 78.9629], 5);

            // Add dark mode by default
            _currentTileLayer = L.tileLayer(MapStyle.dark, {
                subdomains: "abcd",
                maxZoom: 19
            }).addTo(_map);

            // Add all layer groups to map
            Object.values(_layers).forEach(layer => layer.addTo(_map));

            // Setup Custom Zoom & Controls
            L.control.scale({ position: "bottomleft" }).addTo(_map);

            console.log("[NetworkExplorer] Map canvas successfully initialized.");
        },

        setStyle(styleName) {
            if (!_map || !_currentTileLayer) return;
            const url = MapStyle[styleName] || MapStyle.dark;
            _currentTileLayer.setUrl(url);
            console.log(`[NetworkExplorer] Map tile style switched to: ${styleName}`);
        },

        async loadNetwork(filters = {}) {
            if (!_map) return;
            
            try {
                const res = await fetch("/api/geospatial/network", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ filters })
                });

                if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
                const data = await res.json();
                _rawNetworkData = data;

                this.renderNetwork(data);
                this.fitToNetwork();
            } catch (err) {
                console.error("[NetworkExplorer] Failed to load network layers:", err);
            }
        },

        renderNetwork(data) {
            this.clearAllLayers();

            const { hubs = [], repair_centers = [], flows = [] } = data;

            // 1. Render Hub Locations
            hubs.forEach(h => {
                const isCongested = h.utilization > 80;
                const markerHtml = `
                    <div class="hub-pulse-marker ${isCongested ? 'congested' : ''}" style="background:${isCongested ? 'var(--danger-color)' : 'var(--primary-color)'};">
                        <span class="hub-badge-text">${h.id}</span>
                    </div>
                `;
                const customIcon = L.divIcon({
                    html: markerHtml,
                    className: "custom-map-icon",
                    iconSize: [32, 32],
                    iconAnchor: [16, 16]
                });

                const marker = L.marker([h.lat, h.lon], { icon: customIcon })
                    .bindPopup(`
                        <div style="color:#fff; font-family:sans-serif; min-width:180px;">
                            <h4 style="margin:0 0 6px 0; border-bottom:1px solid rgba(255,255,255,0.2); pb:4px;">Hub: ${h.name} (${h.id})</h4>
                            <p style="margin:2px 0;"><strong>City:</strong> ${h.city}</p>
                            <p style="margin:2px 0;"><strong>State/Region:</strong> ${h.state}</p>
                            <p style="margin:2px 0;"><strong>Capacity:</strong> ${h.capacity}</p>
                            <p style="margin:2px 0;"><strong>Utilization:</strong> <span style="color:${isCongested ? '#ef4444' : '#10b981'}">${h.utilization}%</span></p>
                        </div>
                    `);

                marker.on("click", () => {
                    if (window.HubPanel) window.HubPanel.show(h);
                });

                marker.addTo(_layers.hubs);

                // If congested, also put in congestion overlay
                if (isCongested) {
                    const pulseCircle = L.circleMarker([h.lat, h.lon], {
                        radius: 20,
                        color: "red",
                        fillColor: "red",
                        fillOpacity: 0.2,
                        className: "congestion-pulse-circle"
                    });
                    pulseCircle.addTo(_layers.congestion);
                }
            });

            // 2. Render Repair Centers (TPRs)
            repair_centers.forEach(rc => {
                const markerHtml = `
                    <div class="rc-marker-badge">
                        <i class="fa-solid fa-wrench"></i>
                    </div>
                `;
                const customIcon = L.divIcon({
                    html: markerHtml,
                    className: "custom-map-icon",
                    iconSize: [28, 28],
                    iconAnchor: [14, 14]
                });

                const marker = L.marker([rc.lat, rc.lon], { icon: customIcon })
                    .bindPopup(`
                        <div style="color:#fff; font-family:sans-serif; min-width:180px;">
                            <h4 style="margin:0 0 6px 0; border-bottom:1px solid rgba(255,255,255,0.2); pb:4px;">Repair Center: ${rc.name}</h4>
                            <p style="margin:2px 0;"><strong>ID:</strong> ${rc.id}</p>
                            <p style="margin:2px 0;"><strong>Utilization:</strong> ${rc.utilization}%</p>
                            <p style="margin:2px 0;"><strong>Supported Parts:</strong> ${rc.supported_parts.join(', ')}</p>
                        </div>
                    `);

                marker.on("click", () => {
                    if (window.HubPanel) window.HubPanel.show(rc);
                });

                marker.addTo(_layers.tprs);
            });

            // 3. Render Route flows
            flows.forEach(flow => {
                const startLat = flow.origin_lat || flow.start_lat || 20.0;
                const startLon = flow.origin_lon || flow.start_lon || 78.0;
                const endLat = flow.dest_lat || flow.end_lat || 20.0;
                const endLon = flow.dest_lon || flow.end_lon || 78.0;
                const latlngs = [
                    [startLat, startLon],
                    [endLat, endLon]
                ];

                // Check SLA and Costs to decide colors
                const totalMiss = flow.missed_sla || 0;
                const isHighRisk = totalMiss > 0 || (flow.risk_score && flow.risk_score > 60);
                const color = isHighRisk ? "#ef4444" : "#10b981";

                const polyline = L.polyline(latlngs, {
                    color: color,
                    weight: Math.min(3 + (flow.shipment_count / 10), 8),
                    opacity: 0.8,
                    className: "animated-polyline-flow"
                }).addTo(_layers.flows);

                const originId = flow.origin_id || flow.origin || "Unknown";
                const destId = flow.destination_id || flow.destination || "Unknown";
                const avgTransit = flow.avg_transit_time || flow.avg_transit_days || 0;

                polyline.bindPopup(`
                    <div style="color:#fff; font-family:sans-serif;">
                        <h4 style="margin:0 0 4px 0;">Corridor: ${flow.corridor || (originId + ' → ' + destId)}</h4>
                        <p style="margin:2px 0;"><strong>Active Shipments:</strong> ${flow.shipment_count}</p>
                        <p style="margin:2px 0;"><strong>Average Cost:</strong> $${flow.avg_cost}</p>
                        <p style="margin:2px 0;"><strong>Average Transit:</strong> ${avgTransit} days</p>
                    </div>
                `);

                polyline.on("click", () => {
                    const normalizedFlow = {
                        origin: originId,
                        destination: destId,
                        shipment_count: flow.shipment_count,
                        avg_cost: flow.avg_cost,
                        avg_transit_days: avgTransit
                    };
                    if (window.RoutePanel) window.RoutePanel.show(normalizedFlow);
                });
            });

            // Add styled markers & flows stylesheet if missing
            if (!document.getElementById("explorer-styles")) {
                const style = document.createElement("style");
                style.id = "explorer-styles";
                style.textContent = `
                    .hub-pulse-marker {
                        width: 32px; height: 32px; border-radius: 50%;
                        display: flex; align-items: center; justify-content: center;
                        color: #fff; font-size: 8px; font-weight: bold;
                        border: 2px solid #fff; box-shadow: 0 0 10px rgba(0,0,0,0.5);
                        cursor: pointer;
                    }
                    .hub-pulse-marker.congested {
                        animation: mapMarkerCongest 1.5s infinite alternate;
                    }
                    .rc-marker-badge {
                        width: 26px; height: 26px; background: #f57c00; border-radius: 4px;
                        display: flex; align-items: center; justify-content: center;
                        color: #fff; font-size: 11px; border: 1.5px solid #fff;
                        box-shadow: 0 0 8px rgba(0,0,0,0.5); cursor: pointer;
                    }
                    @keyframes mapMarkerCongest {
                        from { box-shadow: 0 0 4px #ef4444; }
                        to { box-shadow: 0 0 16px #ef4444; }
                    }
                    .animated-polyline-flow {
                        stroke-dasharray: 8, 8;
                        animation: polylineDash 25s linear infinite;
                    }
                    @keyframes polylineDash {
                        to { stroke-dashoffset: -1000; }
                    }
                `;
                document.head.appendChild(style);
            }
        },

        fitToNetwork() {
            if (!_map) return;
            const bounds = [];
            
            // Collect all layer markers / geometries
            Object.values(_layers).forEach(layer => {
                layer.eachLayer(l => {
                    if (typeof l.getLatLng === "function") {
                        bounds.push(l.getLatLng());
                    } else if (typeof l.getLatLngs === "function") {
                        bounds.push(...l.getLatLngs());
                    }
                });
            });

            if (bounds.length > 0) {
                _map.fitBounds(L.latLngBounds(bounds), { padding: [40, 40] });
            }
        },

        clearAllLayers() {
            Object.values(_layers).forEach(layer => layer.clearLayers());
        },

        toggleLayer(layerName, visible) {
            if (!_map) return;
            const layer = _layers[layerName];
            if (!layer) return;

            if (visible) {
                if (!_map.hasLayer(layer)) _map.addLayer(layer);
            } else {
                if (_map.hasLayer(layer)) _map.removeLayer(layer);
            }
        },

        getMap() {
            return _map;
        },

        getPlaybackLayer() {
            return _layers.playback;
        }
    };

    window.NetworkExplorer = NetworkExplorer;
})();
