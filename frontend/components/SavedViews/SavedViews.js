/**
 * SavedViews Component
 * Manages spatial view bookmarks so users can save and reload custom map coordinates/zooms.
 */
(function() {
    let _bookmarks = [];

    const SavedViews = {
        render(containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;

            this.updateHtml(container);
        },

        addBookmark(bm) {
            _bookmarks.push(bm);
            this.saveToStorage();
            
            const container = document.getElementById("saved-views-container");
            if (container) this.updateHtml(container);
        },

        removeBookmark(idx) {
            _bookmarks.splice(idx, 1);
            this.saveToStorage();

            const container = document.getElementById("saved-views-container");
            if (container) this.updateHtml(container);
        },

        selectBookmark(idx) {
            const bm = _bookmarks[idx];
            if (!bm) return;

            const map = NetworkExplorer.getMap();
            if (map) {
                map.flyTo(bm.center, bm.zoom, { animate: true, duration: 1.2 });
            }
        },

        saveToStorage() {
            localStorage.setItem("dell_gis_bookmarks", JSON.stringify(_bookmarks));
        },

        loadFromStorage() {
            const stored = localStorage.getItem("dell_gis_bookmarks");
            if (stored) {
                try {
                    _bookmarks = JSON.parse(stored);
                } catch(e) {
                    _bookmarks = [];
                }
            }
        },

        updateHtml(container) {
            this.loadFromStorage();

            container.innerHTML = `
                <div class="card glass-panel" style="padding:var(--space-3); border:1px solid rgba(63,63,70,0.4); display:flex; flex-direction:column; gap:6px;">
                    <div style="font-size:11px; font-weight:bold; color:#fff; text-transform:uppercase;">
                        <i class="fa-solid fa-star text-warning"></i> Bookmarked Views
                    </div>
                    <div id="bookmark-views-list" style="display:flex; flex-direction:column; gap:4px; max-height:100px; overflow-y:auto;">
                        ${_bookmarks.length === 0 
                            ? `<div style="font-size:10px; color:var(--text-muted); text-align:center; padding:10px;">No saved views. Click bookmark on toolbar.</div>`
                            : _bookmarks.map((b, idx) => `
                                <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(9,9,11,0.4); padding:6px; border-radius:4px; border:1px solid rgba(63,63,70,0.1);">
                                    <span onclick="SavedViews.selectBookmark(${idx})" style="font-size:10px; color:#fff; cursor:pointer; font-weight:500;">
                                        <i class="fa-solid fa-location-dot text-primary"></i> ${b.name}
                                    </span>
                                    <button class="btn btn-secondary btn-sm" onclick="SavedViews.removeBookmark(${idx})" style="padding:1px 4px; font-size:8px; border:none;">
                                        <i class="fa-solid fa-trash-can text-danger"></i>
                                    </button>
                                </div>
                            `).join('')
                        }
                    </div>
                </div>
            `;
        }
    };

    window.SavedViews = SavedViews;
})();
