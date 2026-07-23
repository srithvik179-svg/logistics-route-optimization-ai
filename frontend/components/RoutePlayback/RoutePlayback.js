/**
 * RoutePlayback Component
 * Renders route playback buttons (play, pause, speed, segment) and animates marker dots along active route flows.
 */
(function() {
    let _activePlaybackMarker = null;
    let _playbackInterval = null;
    let _currentSegmentIndex = 0;
    let _segments = [];
    let _speedMultiplier = 1; // 1x, 2x, 4x, 8x
    let _isPlaying = false;

    const RoutePlayback = {
        render(containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;

            container.innerHTML = `
                <div class="card glass-panel" style="padding:var(--space-3); border:1px solid rgba(63,63,70,0.4); display:flex; flex-direction:column; gap:var(--space-2);">
                    <div style="font-size:11px; font-weight:bold; color:#fff; text-transform:uppercase;">
                        <i class="fa-solid fa-circle-play text-success"></i> Transit Route Playback Engine
                    </div>
                    <div style="display:flex; align-items:center; gap:var(--space-3); justify-content:space-between;">
                        <div style="display:flex; gap:var(--space-2);">
                            <button class="btn btn-secondary btn-sm" onclick="RoutePlayback.togglePlay()">
                                <i class="fa-solid fa-play" id="btn-playback-play-icon"></i>
                            </button>
                            <button class="btn btn-secondary btn-sm" onclick="RoutePlayback.reset()">
                                <i class="fa-solid fa-arrows-rotate"></i>
                            </button>
                        </div>
                        <div style="display:flex; align-items:center; gap:4px;">
                            <span style="font-size:10px; color:var(--text-muted);">Speed:</span>
                            <select id="playback-speed-select" onchange="RoutePlayback.setSpeed(this.value)" style="background:#27272a; border:1px solid #3f3f46; color:#fff; font-size:10px; border-radius:3px; padding:2px 4px;">
                                <option value="1">1x</option>
                                <option value="2">2x</option>
                                <option value="4">4x</option>
                                <option value="8">8x</option>
                            </select>
                        </div>
                    </div>
                    <div style="display:flex; flex-direction:column; gap:4px;">
                        <input type="range" id="playback-progress" min="0" max="100" value="0" oninput="RoutePlayback.seek(this.value)" style="width:100%; accent-color:var(--primary-color);">
                        <div style="display:flex; justify-content:space-between; font-size:9px; color:var(--text-muted);">
                            <span id="playback-status-text">Select shipment flow route</span>
                            <span id="playback-time-text">0.0%</span>
                        </div>
                    </div>
                </div>
            `;
        },

        setupRoute(latlngs, routeLabel = "Shipment") {
            this.reset();
            _segments = latlngs;
            document.getElementById("playback-status-text").textContent = `Ready: ${routeLabel}`;
        },

        togglePlay() {
            if (_segments.length === 0) {
                const statusText = document.getElementById("playback-status-text") || document.getElementById("pb-step-info");
                if (statusText) statusText.textContent = "Select a route flow or corridor on the map";
                return;
            }

            const playIcon = document.getElementById("btn-playback-play-icon");
            if (_isPlaying) {
                // Pause
                _isPlaying = false;
                playIcon.className = "fa-solid fa-play";
                clearInterval(_playbackInterval);
            } else {
                // Play
                _isPlaying = true;
                playIcon.className = "fa-solid fa-pause";
                
                const stepDuration = 1000 / _speedMultiplier;
                _playbackInterval = setInterval(() => {
                    this.stepForward();
                }, stepDuration);
            }
        },

        stepForward() {
            if (_currentSegmentIndex >= _segments.length - 1) {
                // Done
                this.togglePlay();
                _currentSegmentIndex = 0;
                return;
            }

            _currentSegmentIndex++;
            this.updateMarkerPosition();
        },

        updateMarkerPosition() {
            const pLayer = NetworkExplorer.getPlaybackLayer();
            if (_activePlaybackMarker) {
                pLayer.removeLayer(_activePlaybackMarker);
            }

            const currentPos = _segments[_currentSegmentIndex];
            _activePlaybackMarker = L.circleMarker(currentPos, {
                radius: 8,
                color: "#3b82f6",
                fillColor: "#fff",
                fillOpacity: 1,
                weight: 2
            }).addTo(pLayer);

            // Pan camera to follow shipment
            const map = NetworkExplorer.getMap();
            if (map) map.panTo(currentPos);

            // Update Progress bar
            const pct = Math.round((_currentSegmentIndex / (_segments.length - 1)) * 100);
            document.getElementById("playback-progress").value = pct;
            document.getElementById("playback-time-text").textContent = `${pct}%`;
        },

        seek(val) {
            if (_segments.length === 0) return;
            const pct = parseInt(val);
            _currentSegmentIndex = Math.round((pct / 100) * (_segments.length - 1));
            this.updateMarkerPosition();
        },

        setSpeed(val) {
            _speedMultiplier = parseInt(val);
            if (_isPlaying) {
                // Restart timer with new speed duration
                this.togglePlay(); // Pause
                this.togglePlay(); // Play
            }
        },

        reset() {
            _isPlaying = false;
            _currentSegmentIndex = 0;
            const playIcon = document.getElementById("btn-playback-play-icon");
            if (playIcon) playIcon.className = "fa-solid fa-play";
            
            clearInterval(_playbackInterval);

            const pLayer = NetworkExplorer.getPlaybackLayer();
            if (_activePlaybackMarker) {
                pLayer.removeLayer(_activePlaybackMarker);
                _activePlaybackMarker = null;
            }

            const progress = document.getElementById("playback-progress");
            if (progress) progress.value = 0;
            const timeText = document.getElementById("playback-time-text");
            if (timeText) timeText.textContent = "0.0%";
        }
    };

    window.RoutePlayback = RoutePlayback;
})();
