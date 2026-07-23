/**
 * FilterBar Component
 * Renders a global analytics filter toolbar and synchronizes filters across viewports.
 * Dropdown values match the actual Dell_Logistics_Route_Optimization.xlsx dataset.
 */
(function() {
    window.GlobalFilters = {
        start_date: "",
        end_date: "",
        hub: "",
        region: "",
        route: "",
        shipment_type: "",
        transport_mode: "",
        priority: "",
        status: "",
        search: ""
    };

    const FilterBar = {
        init(containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;

            container.innerHTML = `
                <div class="global-filter-bar glass-panel fade-in-slide-up">
                    <div class="filter-header">
                        <h4><i class="fa-solid fa-filter text-primary"></i> Global Workspace Filters</h4>
                        <div class="filter-actions">
                            <button class="btn btn-secondary btn-sm" id="btn-global-filter-reset"><i class="fa-solid fa-trash-can"></i> Reset</button>
                            <button class="btn btn-primary btn-sm" id="btn-global-filter-apply"><i class="fa-solid fa-circle-check"></i> Apply Filters</button>
                        </div>
                    </div>
                    <div class="filter-grid">
                        <div class="filter-item">
                            <label>Start Date</label>
                            <input type="date" id="gfilter-start-date" class="form-control">
                        </div>
                        <div class="filter-item">
                            <label>End Date</label>
                            <input type="date" id="gfilter-end-date" class="form-control">
                        </div>
                        <div class="filter-item">
                            <label>Hub Location</label>
                            <select id="gfilter-hub" class="form-control">
                                <option value="">All Hubs</option>
                                <option value="HUB-AHM">Ahmedabad Satellite (HUB-AHM)</option>
                                <option value="HUB-AMS">Amsterdam Hub (HUB-AMS)</option>
                                <option value="HUB-BLR">Bangalore Hub (HUB-BLR)</option>
                                <option value="HUB-CHE">Chennai Hub (HUB-CHE)</option>
                                <option value="HUB-DEL">Delhi Hub (HUB-DEL)</option>
                                <option value="HUB-DXB">Dubai Hub (HUB-DXB)</option>
                                <option value="HUB-HYD">Hyderabad Hub (HUB-HYD)</option>
                                <option value="HUB-KOL">Kolkata Satellite (HUB-KOL)</option>
                                <option value="HUB-KUL">Kuala Lumpur Hub (HUB-KUL)</option>
                                <option value="HUB-MUM">Mumbai Hub (HUB-MUM)</option>
                                <option value="HUB-PUN">Pune Satellite (HUB-PUN)</option>
                                <option value="HUB-SIN">Singapore Hub (HUB-SIN)</option>
                            </select>
                        </div>
                        <div class="filter-item">
                            <label>Region</label>
                            <select id="gfilter-region" class="form-control">
                                <option value="">All Regions</option>
                                <option value="Asia Pacific">Asia Pacific</option>
                                <option value="East India">East India</option>
                                <option value="Europe">Europe</option>
                                <option value="Middle East">Middle East</option>
                                <option value="North India">North India</option>
                                <option value="South India">South India</option>
                                <option value="West India">West India</option>
                            </select>
                        </div>
                        <div class="filter-item">
                            <label>Route Origin/Dest</label>
                            <input type="text" id="gfilter-route" class="form-control" placeholder="e.g. HUB-DEL-Bangalore">
                        </div>
                        <div class="filter-item">
                            <label>Flow Type</label>
                            <select id="gfilter-shipment-type" class="form-control">
                                <option value="">All Flows</option>
                                <option value="Forward">Forward</option>
                                <option value="Reverse">Reverse</option>
                            </select>
                        </div>
                        <div class="filter-item">
                            <label>Logistics Partner</label>
                            <select id="gfilter-transport-mode" class="form-control">
                                <option value="">All Partners</option>
                                <option value="AirFreight Partners">AirFreight Partners</option>
                                <option value="FastTrack Logistics">FastTrack Logistics</option>
                                <option value="GlobalShip Express">GlobalShip Express</option>
                                <option value="GroundLink Network">GroundLink Network</option>
                                <option value="SwiftCargo India">SwiftCargo India</option>
                            </select>
                        </div>
                        <div class="filter-item">
                            <label>Priority</label>
                            <select id="gfilter-priority" class="form-control">
                                <option value="">All Priorities</option>
                                <option value="P1-Critical">P1 - Critical</option>
                                <option value="P2-High">P2 - High</option>
                                <option value="P3-Medium">P3 - Medium</option>
                                <option value="P4-Low">P4 - Low</option>
                            </select>
                        </div>
                        <div class="filter-item">
                            <label>SLA Status</label>
                            <select id="gfilter-status" class="form-control">
                                <option value="">All SLA Statuses</option>
                                <option value="NO">SLA Met (NO Breach)</option>
                                <option value="YES">SLA Breached (YES)</option>
                            </select>
                        </div>
                        <div class="filter-item filter-search-wrapper">
                            <label>Search Text</label>
                            <input type="text" id="gfilter-search" class="form-control" placeholder="Part No, Hub ID, destination...">
                        </div>
                    </div>
                </div>
            `;

            // Wire events
            document.getElementById("btn-global-filter-apply").addEventListener("click", () => this.apply());
            document.getElementById("btn-global-filter-reset").addEventListener("click", () => this.reset());
        },

        apply() {
            // Read UI values
            window.GlobalFilters.start_date    = document.getElementById("gfilter-start-date").value;
            window.GlobalFilters.end_date      = document.getElementById("gfilter-end-date").value;
            window.GlobalFilters.hub           = document.getElementById("gfilter-hub").value;
            window.GlobalFilters.region        = document.getElementById("gfilter-region").value;
            window.GlobalFilters.route         = document.getElementById("gfilter-route").value;
            window.GlobalFilters.shipment_type = document.getElementById("gfilter-shipment-type").value;
            window.GlobalFilters.transport_mode= document.getElementById("gfilter-transport-mode").value;
            window.GlobalFilters.priority      = document.getElementById("gfilter-priority").value;
            window.GlobalFilters.status        = document.getElementById("gfilter-status").value;
            window.GlobalFilters.search        = document.getElementById("gfilter-search").value;

            console.log("[FilterBar] Applying Global Filters:", window.GlobalFilters);

            // Sync with sub-states
            this.syncFilters();

            // Trigger reloads on whichever section is currently active
            const activeSection = document.querySelector(".viewport-section.active");
            if (activeSection) {
                const targetId = activeSection.id;
                console.log(`[FilterBar] Refreshing active section: ${targetId}`);

                const sectionLoaders = {
                    "dashboard-section":     "loadExecutiveDashboard",
                    "network-map-section":   "loadNetworkMap",
                    "routes-section":        "loadRouteIntelligence",
                    "performance-section":   "loadLogisticsPerformance",
                    "workspace-section":     "loadWorkspace",
                    "recommendation-section":"loadRecommendationWorkspace",
                    "corridor-section":      "loadCorridorWorkspace",
                    "optimization-section":  "loadCostOptimizationWorkspace",
                    "reverse-section":       "loadReverseLogisticsWorkspace",
                    "circular-section":      "loadCircularSupplyChainWorkspace",
                    "command-3d-section":    "load3DCommandCenterWorkspace",
                    "sla-section":           "loadSLAPredictionWorkspace",
                    "orchestrator-section":  "loadAIOrchestratorWorkspace",
                    "reports-section":       "loadExecutiveReportsWorkspace",
                    "command-center-section":"loadCommandCenterWorkspace",
                    "geospatial-section":    "loadGeospatialWorkspace",
                    "copilot-section":       "loadCopilotWorkspace",
                    "executive-section":     "loadExecutiveCommandCenter",
                    "admin-section":         "loadAdminCenter"
                };

                const loaderName = sectionLoaders[targetId];
                if (loaderName && typeof window[loaderName] === "function") {
                    window[loaderName]();
                }
            }
        },

        reset() {
            document.getElementById("gfilter-start-date").value    = "";
            document.getElementById("gfilter-end-date").value      = "";
            document.getElementById("gfilter-hub").value           = "";
            document.getElementById("gfilter-region").value        = "";
            document.getElementById("gfilter-route").value         = "";
            document.getElementById("gfilter-shipment-type").value = "";
            document.getElementById("gfilter-transport-mode").value= "";
            document.getElementById("gfilter-priority").value      = "";
            document.getElementById("gfilter-status").value        = "";
            document.getElementById("gfilter-search").value        = "";

            this.apply();
        },

        syncFilters() {
            const gf = window.GlobalFilters;

            const syncState = (state) => {
                if (!state) return;
                state.filters = state.filters || {};
                state.filters.start_date    = gf.start_date;
                state.filters.end_date      = gf.end_date;
                state.filters.hub           = gf.hub;
                state.filters.region        = gf.region;
                state.filters.route         = gf.route;
                state.filters.shipment_type = gf.shipment_type;
                state.filters.transport_mode= gf.transport_mode;
                state.filters.priority      = gf.priority;
                state.filters.status        = gf.status;
                state.filters.search        = gf.search;
            };

            syncState(window.perfState);
            syncState(window.routeState);
            syncState(window.mapState);
            syncState(window.biState);

            // Sync Executive Command filters
            if (window.execFilters) {
                window.execFilters.region  = gf.region;
                window.execFilters.partner = gf.transport_mode;
            }
        },

        updateDropdowns(hubs, regions) {
            // Dynamic update not needed — dropdowns are now dataset-accurate hardcoded values
            // This method is kept for API compatibility
        }
    };
    window.FilterBar = FilterBar;
})();
