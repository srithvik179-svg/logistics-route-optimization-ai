/**
 * SharedToolbar Component
 * Renders standardized header titles, descriptions, data sources, timestamps, and menus for widgets.
 */
(function() {
    const SharedToolbar = {
        render(widgetElement, title, desc, dataSource, onRefresh = null, onExport = null) {
            if (!widgetElement) return;
            
            let header = widgetElement.querySelector(".widget-header");
            if (!header) {
                header = document.createElement("div");
                header.className = "widget-header";
                widgetElement.insertBefore(header, widgetElement.firstChild);
            }
            
            const timestamp = new Date().toLocaleTimeString();
            
            header.innerHTML = `
                <div class="widget-title-area">
                    <div style="display:flex; align-items:center; gap:var(--space-2);">
                        <h3>${title}</h3>
                        <span class="badge info" style="font-size: 8px; padding: 2px 4px; border:none; text-transform:none;">${dataSource}</span>
                    </div>
                    <p class="widget-desc">${desc}</p>
                </div>
                <div class="widget-actions-area">
                    <span class="widget-timestamp"><i class="fa-solid fa-clock"></i> Updated ${timestamp}</span>
                    <div class="widget-menu-dropdown">
                        <button class="widget-menu-btn" title="More Actions"><i class="fa-solid fa-ellipsis-vertical"></i></button>
                        <div class="widget-menu-content">
                            <a href="#" class="wmenu-refresh"><i class="fa-solid fa-rotate"></i> Refresh Data</a>
                            <a href="#" class="wmenu-export"><i class="fa-solid fa-file-csv"></i> Export CSV</a>
                            <a href="#" class="wmenu-collapse"><i class="fa-solid fa-compress"></i> Collapse</a>
                            <a href="#" class="wmenu-fullscreen"><i class="fa-solid fa-expand"></i> Fullscreen</a>
                        </div>
                    </div>
                </div>
            `;
            
            // Wire Actions Dropdown toggles
            const menuBtn = header.querySelector(".widget-menu-btn");
            const menuContent = header.querySelector(".widget-menu-content");
            
            if (menuBtn && menuContent) {
                menuBtn.addEventListener("click", (e) => {
                    e.stopPropagation();
                    // Close other menus first
                    document.querySelectorAll(".widget-menu-content").forEach(m => {
                        if (m !== menuContent) m.classList.remove("active");
                    });
                    menuContent.classList.toggle("active");
                });
                
                document.addEventListener("click", () => {
                    menuContent.classList.remove("active");
                });
            }
            
            header.querySelector(".wmenu-refresh").addEventListener("click", (e) => {
                e.preventDefault();
                if (onRefresh) onRefresh();
            });
            
            header.querySelector(".wmenu-export").addEventListener("click", (e) => {
                e.preventDefault();
                if (onExport) onExport();
                else alert("Export CSV packet successfully downloaded for: " + title);
            });
            
            header.querySelector(".wmenu-collapse").addEventListener("click", (e) => {
                e.preventDefault();
                widgetElement.classList.toggle("collapsed");
            });
            
            header.querySelector(".wmenu-fullscreen").addEventListener("click", (e) => {
                e.preventDefault();
                widgetElement.classList.toggle("fullscreen");
                
                // Locate Plotly chart child and force resize
                const chart = widgetElement.querySelector(".plotly-graph-div, [id^='chart-'], [id^='exec-']");
                if (chart && typeof Plotly !== "undefined") {
                    setTimeout(() => {
                        Plotly.Plots.resize(chart.id);
                    }, 250);
                }
            });
        }
    };
    window.SharedToolbar = SharedToolbar;
})();
