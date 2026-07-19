/**
 * DashboardGrid Component
 * Manages widget ordering, grid columns, layout profiles selection, and local persistence.
 */
(function() {
    const DashboardGrid = {
        activeLayoutName: "Default Overview",
        
        init(gridContainerId, preferenceSelectId = null) {
            const grid = document.getElementById(gridContainerId);
            if (!grid) return;
            
            this.grid = grid;
            this.prefSelect = preferenceSelectId ? document.getElementById(preferenceSelectId) : null;
            
            // Populate layouts selector if present
            this.populatePreferenceDropdown();
            
            // Load current layout preference
            this.loadLayout();
            
            // Setup events on current elements
            this.setupGridInteractions();
        },
        
        setupGridInteractions() {
            const widgets = this.grid.querySelectorAll(".widget-card");
            widgets.forEach(w => {
                // Drag and drop swapping
                window.Widget.makeDraggable(w, (dragged, target) => this.swapWidgets(dragged, target));
                
                // Resize anchors
                window.Widget.makeResizable(w, (resized) => this.saveLayout());
            });
        },
        
        swapWidgets(dragged, target) {
            const children = Array.from(this.grid.children);
            const draggedIdx = children.indexOf(dragged);
            const targetIdx = children.indexOf(target);
            
            if (draggedIdx < targetIdx) {
                this.grid.insertBefore(dragged, target.nextSibling);
            } else {
                this.grid.insertBefore(dragged, target);
            }
            
            console.log(`[DashboardGrid] Swapped widgets: ${dragged.id} <-> ${target.id}`);
            
            // Save state layout preferences
            this.saveLayout();
            
            // Notify Plotly charts inside to resize
            document.querySelectorAll(".plotly-graph-div, [id^='chart-']").forEach(c => {
                if (typeof Plotly !== "undefined") Plotly.Plots.resize(c.id);
            });
        },
        
        saveLayout(customName = null) {
            const name = customName || this.activeLayoutName;
            const config = [];
            const children = Array.from(this.grid.children);
            
            children.forEach(w => {
                if (!w.id) return;
                const gridColumn = window.getComputedStyle(w).gridColumnStart;
                const span = gridColumn && gridColumn.includes("span") 
                    ? parseInt(gridColumn.replace("span", "").trim()) 
                    : 1;
                
                config.push({
                    id: w.id,
                    span: span,
                    collapsed: w.classList.contains("collapsed"),
                    pinned: w.classList.contains("pinned")
                });
            });
            
            const storeKey = `dell_fm_layout_${name}`;
            localStorage.setItem(storeKey, JSON.stringify(config));
            console.log(`[DashboardGrid] Saved layout profile: ${name}`);
            
            // Save layouts index list
            let layoutsList = JSON.parse(localStorage.getItem("dell_fm_layouts_index") || "[]");
            if (!layoutsList.includes(name)) {
                layoutsList.push(name);
                localStorage.setItem("dell_fm_layouts_index", JSON.stringify(layoutsList));
                this.populatePreferenceDropdown();
            }
        },
        
        loadLayout(customName = null) {
            const name = customName || this.activeLayoutName;
            const storeKey = `dell_fm_layout_${name}`;
            const data = localStorage.getItem(storeKey);
            
            if (!data) {
                console.log(`[DashboardGrid] No custom layout data found for: ${name}`);
                return;
            }
            
            try {
                const config = JSON.parse(data);
                
                // Re-sort widget DOM elements based on layout order
                config.forEach(item => {
                    const el = document.getElementById(item.id);
                    if (el) {
                        // Apply styling settings
                        el.style.gridColumn = `span ${item.span || 1}`;
                        if (item.collapsed) el.classList.add("collapsed");
                        else el.classList.remove("collapsed");
                        
                        if (item.pinned) el.classList.add("pinned");
                        else el.classList.remove("pinned");
                        
                        // Move to end of grid (re-orders)
                        this.grid.appendChild(el);
                    }
                });
                
                this.activeLayoutName = name;
                if (this.prefSelect) this.prefSelect.value = name;
                console.log(`[DashboardGrid] Loaded layout profile: ${name}`);
            } catch (e) {
                console.error("[DashboardGrid] Error loading layout state:", e);
            }
        },
        
        populatePreferenceDropdown() {
            if (!this.prefSelect) return;
            
            let layoutsList = JSON.parse(localStorage.getItem("dell_fm_layouts_index") || "[]");
            if (layoutsList.length === 0) {
                layoutsList = ["Default Overview"];
                localStorage.setItem("dell_fm_layouts_index", JSON.stringify(layoutsList));
            }
            
            this.prefSelect.innerHTML = "";
            layoutsList.forEach(name => {
                const opt = document.createElement("option");
                opt.value = name;
                opt.textContent = name;
                this.prefSelect.appendChild(opt);
            });
            
            this.prefSelect.value = this.activeLayoutName;
            
            // Wire select changes
            this.prefSelect.onchange = () => {
                this.loadLayout(this.prefSelect.value);
            };
        },
        
        saveNewLayoutPrompt() {
            const name = prompt("Enter a name for this custom layout config:", "My Operations View");
            if (!name) return;
            
            this.activeLayoutName = name;
            this.saveLayout(name);
        }
    };
    window.DashboardGrid = DashboardGrid;
})();
