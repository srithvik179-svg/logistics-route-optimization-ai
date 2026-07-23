/**
 * GlobalSearch Component
 * Enterprise search utility querying shipments, hubs, TPRs, parts, corridors, and partners.
 */
(function() {
    let debounceTimer = null;
    let selectedIndex = -1;

    const GlobalSearch = {
        init() {
            const input = document.getElementById("global-search-input");
            const clearBtn = document.getElementById("global-search-clear");
            const resultsBox = document.getElementById("global-search-results");

            if (!input) return;

            // Handle input change with 150ms debouncing
            input.addEventListener("input", (e) => {
                const val = e.target.value;
                if (clearBtn) {
                    clearBtn.style.display = val.length > 0 ? "flex" : "none";
                }
                
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.handleSearch(val);
                }, 150);
            });

            // Clear button click handler
            if (clearBtn) {
                clearBtn.addEventListener("click", () => {
                    input.value = "";
                    clearBtn.style.display = "none";
                    if (resultsBox) resultsBox.style.display = "none";
                    input.focus();
                });
            }

            // Keyboard navigation (Arrow keys, Enter, Escape)
            input.addEventListener("keydown", (e) => {
                if (!resultsBox || resultsBox.style.display === "none") return;
                const items = resultsBox.querySelectorAll(".search-result-item");
                if (!items || items.length === 0) return;

                if (e.key === "ArrowDown") {
                    e.preventDefault();
                    selectedIndex = (selectedIndex + 1) % items.length;
                    this.highlightItem(items, selectedIndex);
                } else if (e.key === "ArrowUp") {
                    e.preventDefault();
                    selectedIndex = (selectedIndex - 1 + items.length) % items.length;
                    this.highlightItem(items, selectedIndex);
                } else if (e.key === "Enter") {
                    e.preventDefault();
                    if (selectedIndex >= 0 && selectedIndex < items.length) {
                        items[selectedIndex].click();
                    } else if (items[0]) {
                        items[0].click();
                    }
                } else if (e.key === "Escape") {
                    resultsBox.style.display = "none";
                    selectedIndex = -1;
                }
            });

            // Close dropdown when clicking outside
            document.addEventListener("click", (e) => {
                const container = document.getElementById("global-search-container");
                if (container && !container.contains(e.target) && resultsBox) {
                    resultsBox.style.display = "none";
                    selectedIndex = -1;
                }
            });
        },

        highlightItem(items, index) {
            items.forEach((item, idx) => {
                if (idx === index) {
                    item.classList.add("active");
                    item.scrollIntoView({ block: "nearest" });
                } else {
                    item.classList.remove("active");
                }
            });
        },

        async handleSearch(val) {
            const resultsBox = document.getElementById("global-search-results");
            const spinner = document.getElementById("global-search-spinner");
            const clearBtn = document.getElementById("global-search-clear");
            
            if (!resultsBox) return;
            selectedIndex = -1;

            if (!val || val.trim().length < 2) {
                resultsBox.style.display = "none";
                if (spinner) spinner.style.display = "none";
                if (clearBtn && val.length > 0) clearBtn.style.display = "flex";
                return;
            }

            if (spinner) spinner.style.display = "block";
            if (clearBtn) clearBtn.style.display = "none";

            try {
                const response = await apiFetch("/api/command-center/search", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ query: val.trim() })
                });

                if (spinner) spinner.style.display = "none";
                if (clearBtn) clearBtn.style.display = "flex";

                // Unpack payload if unwrapped or standard
                const results = Array.isArray(response) ? response : (response.payload || []);

                if (!results || results.length === 0) {
                    resultsBox.innerHTML = `
                        <div style="padding:14px; font-size:12px; color:var(--text-muted); text-align:center;">
                            <i class="fa-solid fa-magnifying-glass text-muted" style="margin-bottom:4px; font-size:16px;"></i><br>
                            No records found for "<strong>${this.escapeHtml(val)}</strong>"
                        </div>`;
                } else {
                    resultsBox.innerHTML = results.map((r, i) => {
                        const badgeStyle = this.getBadgeStyle(r.category);
                        return `
                            <div class="search-result-item ${i === 0 ? 'active' : ''}" 
                                 onclick="GlobalSearch.navigate('${r.target_section}', '${r.id}')">
                                <div class="search-result-header">
                                    <span class="search-result-title">${this.escapeHtml(r.title)}</span>
                                    <span style="${badgeStyle}">${this.escapeHtml(r.category)}</span>
                                </div>
                                <div class="search-result-subtitle">${this.escapeHtml(r.subtitle)}</div>
                            </div>
                        `;
                    }).join("");
                    if (results.length > 0) selectedIndex = 0;
                }
                resultsBox.style.display = "block";

            } catch (err) {
                console.error("[GlobalSearch] Search Error:", err);
                if (spinner) spinner.style.display = "none";
                if (clearBtn) clearBtn.style.display = "flex";
            }
        },

        getBadgeStyle(category) {
            const cat = String(category || "").toLowerCase();
            if (cat.includes("shipment")) {
                return "background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: 600;";
            } else if (cat.includes("hub")) {
                return "background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: 600;";
            } else if (cat.includes("tpr") || cat.includes("repair")) {
                return "background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: 600;";
            } else if (cat.includes("part")) {
                return "background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: 600;";
            } else if (cat.includes("corridor")) {
                return "background: rgba(6, 182, 212, 0.15); color: #22d3ee; border: 1px solid rgba(6, 182, 212, 0.3); font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: 600;";
            } else {
                return "background: rgba(99, 102, 241, 0.15); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.3); font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: 600;";
            }
        },

        escapeHtml(str) {
            return String(str || "").replace(/[&<>"']/g, m => ({
                '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
            }[m]));
        },

        navigate(sectionId, id) {
            const resultsBox = document.getElementById("global-search-results");
            if (resultsBox) resultsBox.style.display = "none";

            const input = document.getElementById("global-search-input");
            const clearBtn = document.getElementById("global-search-clear");
            if (input) input.value = "";
            if (clearBtn) clearBtn.style.display = "none";

            const link = document.querySelector(`.nav-link[data-target="${sectionId}"]`);
            if (link) {
                link.click();
            }
        }
    };

    window.GlobalSearch = GlobalSearch;
    
    // Auto-initialize when DOM is ready
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => GlobalSearch.init());
    } else {
        GlobalSearch.init();
    }
})();
