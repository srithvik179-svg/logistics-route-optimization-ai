/**
 * MapToolbar Component
 * Renders spatial utility controls including zoom overlays, fit network, reset view, and map style triggers.
 */
(function() {
    let _activeStyle = "dark";

    const MapToolbar = {
        render(containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;

            container.innerHTML = `
                <div class="card glass-panel" style="padding:4px var(--space-2); border:1px solid rgba(63,63,70,0.4); display:flex; align-items:center; gap:var(--space-2); width:fit-content; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                    <button class="btn btn-secondary btn-sm toolbar-btn" onclick="NetworkExplorer.getMap().zoomIn()" title="Zoom In">
                        <i class="fa-solid fa-plus"></i>
                    </button>
                    <button class="btn btn-secondary btn-sm toolbar-btn" onclick="NetworkExplorer.getMap().zoomOut()" title="Zoom Out">
                        <i class="fa-solid fa-minus"></i>
                    </button>
                    <button class="btn btn-secondary btn-sm toolbar-btn" onclick="NetworkExplorer.fitToNetwork()" title="Fit to Network">
                        <i class="fa-solid fa-expand"></i>
                    </button>
                    
                    <div style="width:1px; height:18px; background:rgba(63,63,70,0.4); margin:0 4px;"></div>

                    <button class="btn btn-secondary btn-sm toolbar-btn" onclick="MapToolbar.toggleStyle()" id="btn-map-style" title="Switch Theme Mode">
                        <i class="fa-solid fa-sun" id="theme-btn-icon"></i>
                    </button>

                    <button class="btn btn-secondary btn-sm toolbar-btn" onclick="MapToolbar.bookmarkCurrentView()" title="Save view bookmark">
                        <i class="fa-solid fa-bookmark"></i>
                    </button>
                </div>
            `;

            if (!document.getElementById("map-toolbar-styles")) {
                const style = document.createElement("style");
                style.id = "map-toolbar-styles";
                style.textContent = `
                    .toolbar-btn {
                        padding: 6px 10px; border-radius: 4px; display: flex; align-items: center; justify-content: center;
                    }
                `;
                document.head.appendChild(style);
            }
        },

        toggleStyle() {
            const icon = document.getElementById("theme-btn-icon");
            if (_activeStyle === "dark") {
                _activeStyle = "light";
                icon.className = "fa-solid fa-moon";
                NetworkExplorer.setStyle("light");
            } else {
                _activeStyle = "dark";
                icon.className = "fa-solid fa-sun";
                NetworkExplorer.setStyle("dark");
            }
        },

        bookmarkCurrentView() {
            const map = NetworkExplorer.getMap();
            if (!map) return;

            const center = map.getCenter();
            const zoom = map.getZoom();

            const name = prompt("Enter a name for this bookmark view:", `Bookmark View ${new Date().toLocaleTimeString()}`);
            if (!name) return;

            if (window.SavedViews) {
                window.SavedViews.addBookmark({ name, center, zoom });
            }
        }
    };

    window.MapToolbar = MapToolbar;
})();
