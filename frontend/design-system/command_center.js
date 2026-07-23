/**
 * Command Center Interactive Engine & UI Enhancer
 * Handles workspace switching, notifications list, search focus, SVG sparklines generation, and animations.
 */
(function() {
    if (window.__CommandCenterLoaded) return;
    window.__CommandCenterLoaded = true;

    console.log("[Command Center] UI Command Center Loaded");

    document.addEventListener("DOMContentLoaded", () => {
        initWorkspaceSwitcher();
        initNotificationsDropdown();
        initSearchFocusPalette();
        initQuickCreateModal();
        generateSparklines();
        initNestedMenus();
        
        console.log("[Command Center] Dashboard Components Rendered");
    });

    /**
     * Workspace Switcher Selection Dropdown
     */
    function initWorkspaceSwitcher() {
        const switcherBtn = document.getElementById("switcher-btn");
        const switcherDropdown = document.getElementById("switcher-dropdown");
        
        if (switcherBtn && switcherDropdown) {
            switcherBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                switcherDropdown.classList.toggle("active");
            });

            document.addEventListener("click", (e) => {
                if (!switcherDropdown.contains(e.target) && !switcherBtn.contains(e.target)) {
                    switcherDropdown.classList.remove("active");
                }
            });

            // Switch option highlight
            const options = switcherDropdown.querySelectorAll(".switcher-option");
            options.forEach(opt => {
                opt.addEventListener("click", () => {
                    options.forEach(o => o.classList.remove("active"));
                    opt.classList.add("active");
                    
                    const name = opt.querySelector("span").textContent;
                    const workspaceNameText = switcherBtn.querySelector(".workspace-name");
                    if (workspaceNameText) workspaceNameText.textContent = name;
                    
                    switcherDropdown.classList.remove("active");
                    console.log(`[Command Center] Workspace updated: ${name}`);
                });
            });
        } else {
            console.log("[Command Center] Environment initialized: Production Grid");
        }
    }

    /**
     * Interactive Notification Bell Menu Dropdown
     */
    function initNotificationsDropdown() {
        const bellBtn = document.getElementById("notification-bell-btn");
        const dropdown = document.getElementById("notification-dropdown");
        const badge = bellBtn ? bellBtn.querySelector(".bell-badge") : null;
        
        if (bellBtn && dropdown) {
            bellBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                dropdown.classList.toggle("active");
                
                // Clear notification dot indicator on click
                if (badge) badge.style.display = "none";
            });

            document.addEventListener("click", (e) => {
                if (!dropdown.contains(e.target) && !bellBtn.contains(e.target)) {
                    dropdown.classList.remove("active");
                }
            });
        }
    }

    /**
     * Focus search shortcut handlers
     */
    function initSearchFocusPalette() {
        const searchInput = document.getElementById("global-search-input");
        
        // Listen to keyboard shortcut '/' to focus search input
        window.addEventListener("keydown", (e) => {
            if (e.key === "/" && document.activeElement !== searchInput && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) {
                e.preventDefault();
                if (searchInput) {
                    searchInput.focus();
                    searchInput.select();
                }
            }
        });
    }

    /**
     * Generates custom SVG path strings inside KPI cards to simulate real-time metrics
     */
    function generateSparklines() {
        const sparklinePaths = [
            "M 0,14 Q 10,8 20,15 T 40,5 T 60,12 T 80,4 L 100,8",
            "M 0,5 Q 15,18 30,10 T 60,16 T 90,4 L 100,9",
            "M 0,18 Q 10,12 25,16 T 50,6 T 75,12 L 100,5",
            "M 0,10 Q 20,4 40,15 T 70,8 T 90,14 L 100,11",
            "M 0,16 Q 15,10 30,18 T 60,4 T 80,12 L 100,8"
        ];

        const cards = document.querySelectorAll(".metric-card, .exec-kpi-tile");
        cards.forEach((card, idx) => {
            const footer = card.querySelector(".card-kpi-footer");
            if (!footer) return;

            // Check if sparkline already exists
            if (footer.querySelector(".mini-sparkline")) return;

            const pathString = sparklinePaths[idx % sparklinePaths.length];
            const isDown = idx % 3 === 1; // mock some down trends
            const strokeColor = isDown ? "var(--danger-color)" : "var(--success-color)";
            
            const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            svg.setAttribute("class", "mini-sparkline");
            svg.setAttribute("viewBox", "0 0 100 20");
            svg.setAttribute("preserveAspectRatio", "none");
            
            const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
            path.setAttribute("d", pathString);
            path.setAttribute("fill", "none");
            path.setAttribute("stroke", strokeColor);
            path.setAttribute("stroke-width", "1.5");
            
            svg.appendChild(path);
            footer.insertBefore(svg, footer.firstChild);

            // Set trend colors and chevron icon text
            const trend = card.querySelector(".kpi-trend");
            if (trend) {
                trend.className = isDown ? "kpi-trend down" : "kpi-trend up";
                trend.innerHTML = isDown 
                    ? '<i class="fa-solid fa-arrow-trend-down"></i> -4.2%' 
                    : '<i class="fa-solid fa-arrow-trend-up"></i> +12.4%';
            }
        });
    }

    /**
     * Inits the quick dispatch order dispatcher modal form
     */
    function initQuickCreateModal() {
        const createBtn = document.getElementById("quick-create-btn");
        const actionBtn = document.getElementById("quick-action-dispatch");
        
        // Handle trigger click
        [createBtn, actionBtn].forEach(btn => {
            if (btn) {
                btn.addEventListener("click", (e) => {
                    e.preventDefault();
                    if (typeof window.openDispatchModal === "function") {
                        window.openDispatchModal();
                    } else {
                        console.warn("[DispatchModal] openDispatchModal function not available");
                    }
                });
            }
        });
    }

    /**
     * Sidebar nested links list expand logic
     */
    function initNestedMenus() {
        const toggleLinks = document.querySelectorAll(".sidebar-nav .has-submenu");
        toggleLinks.forEach(link => {
            link.addEventListener("click", (e) => {
                e.preventDefault();
                const submenu = link.nextElementSibling;
                if (submenu) {
                    submenu.classList.toggle("expanded");
                    const icon = link.querySelector(".submenu-chevron");
                    if (icon) {
                        icon.classList.toggle("fa-chevron-down");
                        icon.classList.toggle("fa-chevron-up");
                    }
                }
            });
        });
    }

    // Monitor view switches to redraw sparklines if clean cards are injected dynamically
    const observer = new MutationObserver(() => {
        generateSparklines();
    });
    observer.observe(document.body, { childList: true, subtree: true });
})();
