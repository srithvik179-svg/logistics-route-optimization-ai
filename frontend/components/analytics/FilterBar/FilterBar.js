/**
 * FilterBar Component
 * Renders a global analytics filter toolbar and synchronizes filters across viewports.
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
                                <option value="Austin Hub">Austin Hub</option>
                                <option value="Dallas Hub">Dallas Hub</option>
                                <option value="Houston Hub">Houston Hub</option>
                                <option value="El Paso Hub">El Paso Hub</option>
                            </select>
                        </div>
                        <div class="filter-item">
                            <label>Region</label>
                            <select id="gfilter-region" class="form-control">
                                <option value="">All Regions</option>
                                <option value="North">North</option>
                                <option value="South">South</option>
                                <option value="East">East</option>
                                <option value="West">West</option>
                            </select>
                        </div>
                        <div class="filter-item">
                            <label>Route Origin/Dest</label>
                            <input type="text" id="gfilter-route" class="form-control" placeholder="e.g. Austin-Dallas">
                        </div>
                        <div class="filter-item">
                            <label>Shipment Type</label>
                            <select id="gfilter-shipment-type" class="form-control">
                                <option value="">All Types</option>
                                <option value="Parts Replacement">Parts Replacement</option>
                                <option value="Standard Delivery">Standard Delivery</option>
                            </select>
                        </div>
                        <div class="filter-item">
                            <label>Transport Mode</label>
                            <select id="gfilter-transport-mode" class="form-control">
                                <option value="">All Modes</option>
                                <option value="Air Freight">Air Freight</option>
                                <option value="Ground Transport">Ground Transport</option>
                            </select>
                        </div>
                        <div class="filter-item">
                            <label>Priority</label>
                            <select id="gfilter-priority" class="form-control">
                                <option value="">All Priorities</option>
                                <option value="High Priority">High Priority</option>
                                <option value="Medium Priority">Medium Priority</option>
                                <option value="Low Priority">Low Priority</option>
                            </select>
                        </div>
                        <div class="filter-item">
                            <label>SLA Status</label>
                            <select id="gfilter-status" class="form-control">
                                <option value="">All Statuses</option>
                                <option value="MET">MET SLA</option>
                                <option value="MISSED">MISSED SLA</option>
                            </select>
                        </div>
                        <div class="filter-item filter-search-wrapper">
                            <label>Search Text</label>
                            <input type="text" id="gfilter-search" class="form-control" placeholder="Search orders...">
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
            window.GlobalFilters.start_date = document.getElementById("gfilter-start-date").value;
            window.GlobalFilters.end_date = document.getElementById("gfilter-end-date").value;
            window.GlobalFilters.hub = document.getElementById("gfilter-hub").value;
            window.GlobalFilters.region = document.getElementById("gfilter-region").value;
            window.GlobalFilters.route = document.getElementById("gfilter-route").value;
            window.GlobalFilters.shipment_type = document.getElementById("gfilter-shipment-type").value;
            window.GlobalFilters.transport_mode = document.getElementById("gfilter-transport-mode").value;
            window.GlobalFilters.priority = document.getElementById("gfilter-priority").value;
            window.GlobalFilters.status = document.getElementById("gfilter-status").value;
            window.GlobalFilters.search = document.getElementById("gfilter-search").value;

            console.log("[FilterBar] Applying Global Filters:", window.GlobalFilters);

            // Sync with sub-states
            this.syncFilters();

            // Trigger reloads on whichever section is currently active
            const activeSection = document.querySelector(".viewport-section.active");
            if (activeSection) {
                const targetId = activeSection.id;
                console.log(`[FilterBar] Refreshing active section: ${targetId}`);
                if (targetId === "dashboard-section" && typeof window.loadExecutiveDashboard === "function") {
                    window.loadExecutiveDashboard();
                } else if (targetId === "routes-section" && typeof window.loadRouteIntelligence === "function") {
                    window.loadRouteIntelligence();
                } else if (targetId === "performance-section" && typeof window.loadLogisticsPerformance === "function") {
                    window.loadLogisticsPerformance();
                } else if (targetId === "network-map-section" && typeof window.loadNetworkMap === "function") {
                    window.loadNetworkMap();
                } else if (targetId === "executive-section" && typeof window.loadExecutiveCommandCenter === "function") {
                    window.loadExecutiveCommandCenter();
                }
            }
        },

        reset() {
            document.getElementById("gfilter-start-date").value = "";
            document.getElementById("gfilter-end-date").value = "";
            document.getElementById("gfilter-hub").value = "";
            document.getElementById("gfilter-region").value = "";
            document.getElementById("gfilter-route").value = "";
            document.getElementById("gfilter-shipment-type").value = "";
            document.getElementById("gfilter-transport-mode").value = "";
            document.getElementById("gfilter-priority").value = "";
            document.getElementById("gfilter-status").value = "";
            document.getElementById("gfilter-search").value = "";

            this.apply();
        },

        syncFilters() {
            const gf = window.GlobalFilters;

            // Sync performance filters
            if (window.perfState) {
                window.perfState.filters.start_date = gf.start_date;
                window.perfState.filters.end_date = gf.end_date;
                window.perfState.filters.hub = gf.hub;
                window.perfState.filters.priority = gf.priority;
                window.perfState.filters.status = gf.status;
            }

            // Sync route filters
            if (window.routeState) {
                window.routeState.filters.start_date = gf.start_date;
                window.routeState.filters.end_date = gf.end_date;
                window.routeState.filters.hub = gf.hub;
                window.routeState.filters.priority = gf.priority;
            }

            // Sync map filters
            if (window.mapState) {
                window.mapState.filters.start_date = gf.start_date;
                window.mapState.filters.end_date = gf.end_date;
                window.mapState.filters.hub = gf.hub;
                window.mapState.filters.priority = gf.priority;
                window.mapState.filters.status = gf.status;
            }

            // Sync BI filters
            if (window.biState) {
                window.biState.filters.start_date = gf.start_date;
                window.biState.filters.end_date = gf.end_date;
                window.biState.filters.hub = gf.hub;
                window.biState.filters.priority = gf.priority;
                window.biState.filters.status = gf.status;
            }

            // Sync Executive Command filters
            if (window.execFilters) {
                window.execFilters.region = gf.region;
            }
        }
    };
    window.FilterBar = FilterBar;
})();
