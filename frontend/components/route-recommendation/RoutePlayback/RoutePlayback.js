/**
 * RoutePlayback Component
 * Manages Leaflet path overlays, route highlighting, and animated vehicle playback.
 */
(function() {
    const RoutePlayback = {
        map: null,
        layers: [],
        playbackMarker: null,
        animationInterval: null,
        isPlaying: false,
        pathCoords: [],
        currentStep: 0,
        speedMs: 300, // delay between nodes in ms

        init(leafletMap) {
            this.map = leafletMap;
            this.clear();
        },

        clear() {
            this.stop();
            this.layers.forEach(layer => {
                if (this.map) this.map.removeLayer(layer);
            });
            this.layers = [];
            
            if (this.playbackMarker && this.map) {
                this.map.removeLayer(this.playbackMarker);
            }
            this.playbackMarker = null;
            this.pathCoords = [];
            this.currentStep = 0;
            this.isPlaying = false;
            
            // Reset control button states if elements exist
            const playIcon = document.getElementById("pb-play-icon");
            if (playIcon) playIcon.className = "fa-solid fa-play";
        },

        drawRoutes(nodes, neighborMap, candidates, selectedId, nodeCoordinates) {
            this.clear();
            if (!this.map) return;

            const selected = candidates.find(c => c.candidate_id === selectedId);
            if (!selected) return;

            // Gather coordinates for mapping
            const getCoords = (nodeId) => {
                const coord = nodeCoordinates[nodeId];
                return coord ? [coord[0], coord[1]] : null;
            };

            // 1. Draw Alternative paths (thin dashed lines)
            candidates.forEach(c => {
                if (c.candidate_id === selectedId) return;

                const latlngs = (c.path_nodes || []).map(nodeId => getCoords(nodeId)).filter(coord => coord !== null);
                if (latlngs.length < 2) return;

                const poly = L.polyline(latlngs, {
                    color: "rgba(107, 114, 128, 0.6)", // gray
                    weight: 3,
                    dashArray: "6, 8"
                }).addTo(this.map);
                
                // Bind tooltip showing engine type
                poly.bindTooltip(`${c.algorithm} alternative path`, { sticky: true });
                this.layers.push(poly);
            });

            // 2. Draw Primary Path (thick brand blue line)
            const primaryLatlngs = (selected.path_nodes || []).map(nodeId => getCoords(nodeId)).filter(coord => coord !== null);
            if (primaryLatlngs.length >= 2) {
                const primaryPoly = L.polyline(primaryLatlngs, {
                    color: "var(--brand-blue)",
                    weight: 6,
                    shadowColor: "var(--brand-blue-glow)",
                    shadowBlur: 10
                }).addTo(this.map);
                
                primaryPoly.bindTooltip(`Selected Recommended Route (${selected.algorithm})`, { sticky: true });
                this.layers.push(primaryPoly);

                // Set zoom levels to fit
                const bounds = L.latLngBounds(primaryLatlngs);
                this.map.fitBounds(bounds, { padding: [40, 40] });

                // Set path coordinates for playback
                this.pathCoords = primaryLatlngs;
            }

            // 3. Draw Hub Markers along the primary path
            (selected.path_nodes || []).forEach((nodeId, idx) => {
                const coord = getCoords(nodeId);
                if (!coord) return;

                const isEnd = idx === 0 || idx === selected.path_nodes.length - 1;
                const marker = L.circleMarker(coord, {
                    radius: isEnd ? 8 : 5,
                    color: isEnd ? "var(--primary-color)" : "var(--brand-blue)",
                    fillColor: "#09090b",
                    fillOpacity: 1,
                    weight: 2
                }).addTo(this.map);

                marker.bindTooltip(`<strong>Node:</strong> ${nodeId}`, { permanent: false, direction: "top" });
                this.layers.push(marker);
            });
        },

        togglePlay() {
            if (this.isPlaying) {
                this.pause();
            } else {
                this.play();
            }
        },

        play() {
            if (this.pathCoords.length < 2) return;
            this.isPlaying = true;

            const playIcon = document.getElementById("pb-play-icon");
            if (playIcon) playIcon.className = "fa-solid fa-pause";

            // If animation reached end, reset to start
            if (this.currentStep >= this.pathCoords.length) {
                this.currentStep = 0;
            }

            // Create marker if it doesn't exist
            if (!this.playbackMarker) {
                this.playbackMarker = L.circleMarker(this.pathCoords[0], {
                    radius: 8,
                    color: "#ffffff",
                    fillColor: "var(--brand-blue)",
                    fillOpacity: 0.9,
                    weight: 3
                }).addTo(this.map);
                
                // Add pulse styling overlay
                this.playbackMarker.getElement().classList.add("playback-pulse-marker");
            }

            this.animationInterval = setInterval(() => {
                if (this.currentStep >= this.pathCoords.length) {
                    this.stop();
                    return;
                }

                // Update position
                const currentCoord = this.pathCoords[this.currentStep];
                this.playbackMarker.setLatLng(currentCoord);
                
                // Update indicator text
                const stepSpan = document.getElementById("pb-step-info");
                if (stepSpan) {
                    stepSpan.textContent = `Hops progress: ${this.currentStep + 1}/${this.pathCoords.length}`;
                }

                this.currentStep++;
            }, this.speedMs);
        },

        pause() {
            this.isPlaying = false;
            const playIcon = document.getElementById("pb-play-icon");
            if (playIcon) playIcon.className = "fa-solid fa-play";

            if (this.animationInterval) {
                clearInterval(this.animationInterval);
                this.animationInterval = null;
            }
        },

        stop() {
            this.pause();
            this.currentStep = 0;
            const stepSpan = document.getElementById("pb-step-info");
            if (stepSpan) {
                stepSpan.textContent = "Playback stopped";
            }
            if (this.playbackMarker && this.pathCoords.length > 0) {
                this.playbackMarker.setLatLng(this.pathCoords[0]);
            }
        },

        setSpeed(ms) {
            this.speedMs = ms;
            if (this.isPlaying) {
                this.pause();
                this.play();
            }
        }
    };
    window.RoutePlayback = RoutePlayback;
})();
