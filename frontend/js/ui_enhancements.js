/**
 * UIEnhancements — Enterprise UI/UX Refinement & Accessibility Module
 * Handles keyboard shortcuts (Cmd+K, Esc), ARIA accessibility, skeleton loaders, and toast alerts.
 */
(function() {
    window.UIEnhancements = {
        init: function() {
            console.log("[UIEnhancements] Initializing Enterprise UI/UX & Accessibility engine...");
            this.setupKeyboardShortcuts();
            this.enforceAccessibilityAttributes();
        },

        setupKeyboardShortcuts: function() {
            document.addEventListener("keydown", function(e) {
                // Cmd+K or Ctrl+K -> Focus Global Search
                if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
                    e.preventDefault();
                    const searchInput = document.querySelector(".search-bar input, input[type='search'], #global-search-input");
                    if (searchInput) {
                        searchInput.focus();
                        if (window.Toast) window.Toast.info("Global Search activated (Cmd+K)");
                    }
                }

                // Escape -> Close Modals or Drawers
                if (e.key === "Escape") {
                    const openModals = document.querySelectorAll(".modal.show, .modal-backdrop, [data-modal-open='true']");
                    openModals.forEach(m => {
                        m.style.display = "none";
                        m.classList.remove("show");
                    });
                }
            });
        },

        enforceAccessibilityAttributes: function() {
            // Attach ARIA roles and tabindexes to interactive cards and buttons
            document.querySelectorAll("button, .btn, .card-clickable").forEach(el => {
                if (!el.getAttribute("tabindex") && el.tagName !== "BUTTON") {
                    el.setAttribute("tabindex", "0");
                }
                if (!el.getAttribute("role") && el.tagName !== "BUTTON") {
                    el.setAttribute("role", "button");
                }
            });
        },

        renderSkeletonLoader: function(containerId, count = 3) {
            const el = document.getElementById(containerId);
            if (!el) return;
            let html = "";
            for (let i = 0; i < count; i++) {
                html += `
                    <div class="skeleton-card">
                        <div class="skeleton-box" style="width: 40%; height: 16px; margin-bottom: 12px;"></div>
                        <div class="skeleton-box" style="width: 90%; height: 12px; margin-bottom: 8px;"></div>
                        <div class="skeleton-box" style="width: 70%; height: 12px;"></div>
                    </div>
                `;
            }
            el.innerHTML = html;
        },

        renderEmptyState: function(containerId, title = "No Data Found", message = "No records match your active filters or dataset context.", icon = "fa-folder-open") {
            const el = document.getElementById(containerId);
            if (!el) return;
            el.innerHTML = `
                <div class="empty-state-card fade-in">
                    <i class="fa-solid ${icon}"></i>
                    <h4>${title}</h4>
                    <p>${message}</p>
                </div>
            `;
        }
    };

    // Auto-init on DOMContentLoaded
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function() {
            window.UIEnhancements.init();
        });
    } else {
        window.UIEnhancements.init();
    }
})();
