/**
 * ExpandablePanel Component
 * Renders an off-canvas drawer/panel for inspection details.
 */
(function() {
    const ExpandablePanel = {
        render(title, contentHtml) {
            let drawer = document.getElementById("expandable-details-drawer");
            if (!drawer) {
                drawer = document.createElement("div");
                drawer.id = "expandable-details-drawer";
                drawer.className = "details-drawer glass-panel";
                document.body.appendChild(drawer);
            }
            
            drawer.innerHTML = `
                <div class="drawer-header">
                    <h3>${title}</h3>
                    <button class="drawer-close-btn" onclick="ExpandablePanel.close()"><i class="fa-solid fa-xmark"></i></button>
                </div>
                <div class="drawer-body">
                    ${contentHtml}
                </div>
            `;
            
            // Slide in
            setTimeout(() => {
                drawer.classList.add("active");
            }, 50);
        },
        close() {
            const drawer = document.getElementById("expandable-details-drawer");
            if (drawer) drawer.classList.remove("active");
        }
    };
    window.ExpandablePanel = ExpandablePanel;
})();
