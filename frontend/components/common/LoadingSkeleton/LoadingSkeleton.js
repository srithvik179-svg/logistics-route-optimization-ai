/**
 * LoadingSkeleton UI helper
 * Dynamically injects shimmers inside containers.
 */
(function() {
    const LoadingSkeleton = {
        renderKPI(containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;
            container.innerHTML = `
                <div class="skeleton-card skeleton">
                    <div class="skeleton-line skeleton-title"></div>
                    <div class="skeleton-line skeleton-value"></div>
                    <div class="skeleton-line skeleton-subtext"></div>
                </div>
            `;
        },
        renderTable(containerId, cols = 5, rows = 5) {
            const container = document.getElementById(containerId);
            if (!container) return;
            let html = "";
            for (let r = 0; r < rows; r++) {
                html += "<tr>";
                for (let c = 0; c < cols; c++) {
                    html += `<td><div class="skeleton-line skeleton-table-cell skeleton"></div></td>`;
                }
                html += "</tr>";
            }
            container.innerHTML = html;
        },
        renderChart(containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;
            container.innerHTML = `
                <div class="skeleton-chart skeleton">
                    <div class="skeleton-chart-inner">
                        <div class="skeleton-chart-bar skeleton" style="height:40%"></div>
                        <div class="skeleton-chart-bar skeleton" style="height:70%"></div>
                        <div class="skeleton-chart-bar skeleton" style="height:55%"></div>
                        <div class="skeleton-chart-bar skeleton" style="height:85%"></div>
                        <div class="skeleton-chart-bar skeleton" style="height:35%"></div>
                    </div>
                </div>
            `;
        },
        showMapOverlay(mapContainerId, show = true) {
            const container = document.getElementById(mapContainerId);
            if (!container) return;
            
            let overlay = container.querySelector(".map-loading-overlay");
            if (!overlay) {
                overlay = document.createElement("div");
                overlay.className = "map-loading-overlay";
                overlay.innerHTML = `
                    <div class="map-loading-spinner">
                        <i class="fa-solid fa-circle-notch fa-spin"></i>
                        <span>Loading Map Layer...</span>
                    </div>
                `;
                container.appendChild(overlay);
            }
            overlay.style.display = show ? "flex" : "none";
        }
    };
    window.LoadingSkeleton = LoadingSkeleton;
})();
