/**
 * Geospatial Intelligence Main Page Controller
 * Orchestrates maps payload loads, search bindings, side draws, and timeline event filters.
 */
(function() {
    let _activeFilters = {};
    let _initialized = false;

    async function initGeospatialWorkspace() {
        console.log("[Geospatial] Initializing Geospatial Intelligence map workspace...");

        if (!_initialized) {
            // 1. Initialize NetworkExplorer Map
            window.NetworkExplorer.init("geospatial-map-canvas");

            // 2. Render overlays & control widgets
            window.LayerManager.render("geospatial-layer-container");
            window.RoutePlayback.render("geospatial-playback-container");
            window.HubPanel.render("geospatial-hub-container");
            window.RoutePanel.render("geospatial-route-container");
            window.MapToolbar.render("geospatial-toolbar-container");
            window.Timeline.render("geospatial-timeline-container");
            window.SpatialSearch.render("geospatial-search-overlay-container");
            window.SavedViews.render("geospatial-saved-views-container");
            _initialized = true;
        } else {
            const map = window.NetworkExplorer.getMap();
            if (map) {
                setTimeout(() => {
                    map.invalidateSize();
                }, 100);
            }
        }

        // Set loader spinner inside Map Card overlay
        const mapCanvas = document.getElementById("geospatial-map-canvas");
        const loader = document.createElement("div");
        loader.id = "map-loader-spinner";
        loader.style.cssText = `
            position: absolute; top:50%; left:50%; transform:translate(-50%, -50%);
            background: rgba(9,9,11,0.85); padding: 15px 30px; border-radius: 8px;
            border: 1px solid rgba(63,63,70,0.4); z-index:99999; color:#fff; font-size:12px;
            display: flex; align-items: center; gap: 10px; font-family:sans-serif;
        `;
        loader.innerHTML = `<i class="fa-solid fa-spinner fa-spin" style="color:var(--primary-color);"></i> Compiling network geospatial routing...`;
        mapCanvas.appendChild(loader);

        try {
            const statusData = await apiFetch("/api/dataset/status");
            const isValid = !!(statusData && (statusData.loaded || statusData.status === "LOADED" || (statusData.validation_report && statusData.validation_report.is_valid)));

            // Fetch initial payload
            const data = await apiFetch("/api/geospatial/network", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filters: window.GlobalFilters || {} })
            });

            // Check if zero records matched
            const emptyOverlayId = "geospatial-map-empty-overlay";
            let emptyOverlay = document.getElementById(emptyOverlayId);
            if (!data.hubs || data.hubs.length === 0) {
                if (!emptyOverlay) {
                    emptyOverlay = document.createElement("div");
                    emptyOverlay.id = emptyOverlayId;
                    emptyOverlay.style.cssText = `
                        position: absolute; top:50%; left:50%; transform:translate(-50%, -50%);
                        background: rgba(9,9,11,0.9); padding: 20px 40px; border-radius: 8px;
                        border: 1px solid rgba(239, 68, 68, 0.4); z-index:99999; color:#f87171; font-size:14px;
                        text-align: center; font-family:sans-serif;
                    `;
                    mapCanvas.appendChild(emptyOverlay);
                }
                emptyOverlay.style.display = "block";
                emptyOverlay.innerHTML = `<i class="fa-solid fa-triangle-exclamation" style="font-size:24px; margin-bottom:10px; display:block;"></i> No records match the selected filters.`;
            } else {
                if (emptyOverlay) emptyOverlay.style.display = "none";
            }

            // Populate Map nodes
            window.NetworkExplorer.renderNetwork(data);
            window.NetworkExplorer.fitToNetwork();

            // Setup Search suggestions data
            window.SpatialSearch.setupData(data.hubs, data.repair_centers);

            // Hide loader
            loader.remove();
        } catch (err) {
            console.error("[Geospatial] Initialization Error:", err);
            loader.innerHTML = `<span class="text-danger"><i class="fa-solid fa-triangle-exclamation"></i> Failed to compile map payload.</span>`;
        }
    }

    window.loadGeospatialWorkspace = initGeospatialWorkspace;
})();
