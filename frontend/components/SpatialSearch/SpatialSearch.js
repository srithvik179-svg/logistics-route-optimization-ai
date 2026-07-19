/**
 * SpatialSearch Component
 * Floating search bar component enabling search of hubs, routes, and regions with smooth camera fly-to panning.
 */
(function() {
    let _hubs = [];
    let _tprs = [];

    const SpatialSearch = {
        render(containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;

            container.innerHTML = `
                <div style="position:relative; width: 280px; font-family:sans-serif;">
                    <div style="display:flex; align-items:center; background:rgba(9, 9, 11, 0.6); border: 1px solid rgba(63, 63, 70, 0.4); border-radius: 6px; padding: 4px 8px; width: 100%;">
                        <i class="fa-solid fa-magnifying-glass" style="color:var(--text-muted); font-size:12px; margin-right:8px;"></i>
                        <input type="text" id="spatial-search-input" placeholder="Search hubs, routes..." oninput="SpatialSearch.query(this.value)" style="background:none; border:none; color:#fff; font-size:11px; width:100%; outline:none;">
                    </div>
                    <div id="spatial-search-results" class="glass-panel" style="display:none; position:absolute; top:36px; left:0; width:100%; max-height:220px; overflow-y:auto; z-index:99999; border:1px solid rgba(63,63,70,0.4); border-radius:6px; box-shadow:0 10px 15px -3px rgba(0,0,0,0.3); background: rgba(9, 9, 11, 0.95);">
                        <!-- Dynamic search results lists -->
                    </div>
                </div>
            `;
        },

        setupData(hubs, tprs) {
            _hubs = hubs || [];
            _tprs = tprs || [];
        },

        query(val) {
            const resultsPanel = document.getElementById("spatial-search-results");
            if (!resultsPanel) return;

            if (!val.trim()) {
                resultsPanel.style.display = "none";
                return;
            }

            const q = val.toLowerCase();
            const filteredHubs = _hubs.filter(h => h.id.toLowerCase().includes(q) || h.name.toLowerCase().includes(q) || h.city.toLowerCase().includes(q));
            const filteredTprs = _tprs.filter(t => t.id.toLowerCase().includes(q) || t.name.toLowerCase().includes(q) || t.city.toLowerCase().includes(q));

            if (filteredHubs.length === 0 && filteredTprs.length === 0) {
                resultsPanel.innerHTML = `<div style="padding:10px; font-size:10px; color:var(--text-muted); text-align:center;">No results found</div>`;
                resultsPanel.style.display = "block";
                return;
            }

            resultsPanel.style.display = "block";
            resultsPanel.innerHTML = `
                <div style="display:flex; flex-direction:column; padding:4px 0;">
                    ${filteredHubs.map(h => `
                        <div class="spatial-search-item" onclick="SpatialSearch.selectItem(${h.lat}, ${h.lon}, 'hub', '${h.id}')">
                            <span style="font-weight:bold; color:#fff;"><i class="fa-solid fa-tower-broadcast text-primary"></i> ${h.id}</span>
                            <span style="font-size:9px; color:var(--text-muted);">${h.name}</span>
                        </div>
                    `).join('')}
                    ${filteredTprs.map(t => `
                        <div class="spatial-search-item" onclick="SpatialSearch.selectItem(${t.lat}, ${t.lon}, 'tpr', '${t.id}')">
                            <span style="font-weight:bold; color:#fff;"><i class="fa-solid fa-wrench text-warning"></i> ${t.id}</span>
                            <span style="font-size:9px; color:var(--text-muted);">${t.name}</span>
                        </div>
                    `).join('')}
                </div>
            `;

            if (!document.getElementById("spatial-search-item-styles")) {
                const style = document.createElement("style");
                style.id = "spatial-search-item-styles";
                style.textContent = `
                    .spatial-search-item {
                        display: flex; flex-direction: column; padding: 8px 12px; cursor: pointer; border-bottom: 1px solid rgba(63,63,70,0.1);
                    }
                    .spatial-search-item:hover {
                        background: rgba(59, 130, 246, 0.1);
                    }
                `;
                document.head.appendChild(style);
            }
        },

        selectItem(lat, lon, type, id) {
            const resultsPanel = document.getElementById("spatial-search-results");
            if (resultsPanel) resultsPanel.style.display = "none";

            const input = document.getElementById("spatial-search-input");
            if (input) input.value = id;

            // Pan smoothly on map
            const map = NetworkExplorer.getMap();
            if (map) {
                map.flyTo([lat, lon], 7, { animate: true, duration: 1.5 });
            }
        }
    };

    window.SpatialSearch = SpatialSearch;
})();
