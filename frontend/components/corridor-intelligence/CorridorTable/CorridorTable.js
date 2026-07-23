/**
 * CorridorTable Component
 * Displays a sortable, searchable data grid of corridor efficiency metrics.
 */
(function() {
    const CorridorTable = {
        data: [],
        filteredData: [],
        sortField: "efficiency_score",
        sortAsc: false,
        searchQuery: "",
        onExportCSVCallback: null,
        onExportPDFCallback: null,

        init(containerId, onExportCSV, onExportPDF) {
            this.container = document.getElementById(containerId);
            this.onExportCSVCallback = onExportCSV;
            this.onExportPDFCallback = onExportPDF;
        },

        render(corridorsData) {
            if (!this.container) return;

            if (corridorsData) {
                this.data = corridorsData;
                this.applyFilterAndSort();
            }

            let rowsHtml = "";
            if (this.filteredData.length === 0) {
                rowsHtml = `<tr><td colspan="10" class="text-center text-muted">No corridors match active filter criteria.</td></tr>`;
            } else {
                // Store corridor data in global lookup map so onclick only passes a safe numeric index
                window._corridorMap = window._corridorMap || {};
                this.filteredData.forEach((c, idx) => {
                    // Score coloring classes
                    const getScoreClass = (score) => {
                        return score >= 75.0 ? 'text-success' : (score >= 50.0 ? 'text-warning' : 'text-danger');
                    };

                    // Store in global map for safe lookup
                    const mapKey = `corridor_${idx}`;
                    window._corridorMap[mapKey] = c;

                    rowsHtml += `
                        <tr>
                            <td><strong>${c.origin}</strong></td>
                            <td><strong>${c.destination}</strong></td>
                            <td class="text-right">${(c.distance || 0).toFixed(1)} km</td>
                            <td class="text-right">${(c.transit_time || 0).toFixed(1)} days</td>
                            <td class="text-right">${c.shipment_count || 0}</td>
                            <td class="text-right ${(c.delay_rate || 0) > 30 ? 'text-danger' : ''}">${(c.delay_rate || 0).toFixed(1)}%</td>
                            <td class="text-right">${window.Formatters.safeCurrency(c.avg_cost)}</td>
                            <td class="text-right">${((c.distance || 0) * 0.15).toFixed(1)} gal</td>
                            <td class="text-right ${(c.reliability_score || 0) < 70 ? 'text-danger' : 'text-success'}">${(c.reliability_score || 0).toFixed(1)}%</td>
                            <td class="text-right ${getScoreClass(c.efficiency_score || 0)}"><strong>${(c.efficiency_score || 0).toFixed(0)}%</strong></td>
                            <td style="white-space:nowrap;">
                                <button class="btn btn-secondary btn-sm" style="font-size:10px; padding:3px 8px; margin-right:4px;"
                                    onclick="window.openCorridorDrillDown('${mapKey}')">
                                    <i class="fa-solid fa-magnifying-glass-chart"></i> Details
                                </button>
                                <button class="btn btn-primary btn-sm" style="font-size:10px; padding:3px 8px;"
                                    onclick="window.triggerCorridorOptimization('${mapKey}')">
                                    <i class="fa-solid fa-bolt"></i> Optimize
                                </button>
                            </td>
                        </tr>
                    `;
                });

            }

            this.container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up">
                    <div class="card-header" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: var(--space-3);">
                        <h3><i class="fa-solid fa-table text-primary"></i> Corridor Performance Registry</h3>
                        
                        <div style="display: flex; gap: var(--space-3); align-items: center; flex-wrap: wrap;">
                            <input type="text" id="corridor-search-box" class="form-control" style="width: 220px; font-size: var(--font-size-xs);" placeholder="Search corridor hubs..." value="${this.searchQuery}">
                            
                            <button class="btn btn-secondary btn-sm" id="btn-export-corridors-csv"><i class="fa-solid fa-file-csv"></i> CSV</button>
                            <button class="btn btn-secondary btn-sm" id="btn-export-corridors-pdf"><i class="fa-solid fa-file-pdf"></i> Report</button>
                        </div>
                    </div>
                    <div class="card-body" style="padding: 0;">
                        <div class="table-container">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th class="sortable" data-field="origin">Source</th>
                                        <th class="sortable" data-field="destination">Dest</th>
                                        <th class="sortable text-right" data-field="distance">Distance</th>
                                        <th class="sortable text-right" data-field="transit_time">Transit Time</th>
                                        <th class="sortable text-right" data-field="shipment_count">Shipments</th>
                                        <th class="sortable text-right" data-field="delay_rate">Delay Rate</th>
                                        <th class="sortable text-right" data-field="avg_cost">Transit Cost</th>
                                        <th class="sortable text-right" data-field="distance">Fuel Est</th>
                                        <th class="sortable text-right" data-field="reliability_score">SLA Met</th>
                                        <th class="sortable text-right" data-field="efficiency_score">Efficiency</th>
                                        <th style="text-align:center;">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${rowsHtml}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;

            // Bind sorting headers
            this.container.querySelectorAll("th.sortable").forEach(th => {
                const field = th.getAttribute("data-field");
                
                // Add indicator icons
                if (field === this.sortField) {
                    th.innerHTML += this.sortAsc ? ' <i class="fa-solid fa-sort-up"></i>' : ' <i class="fa-solid fa-sort-down"></i>';
                    th.classList.add("active-sort");
                } else {
                    th.innerHTML += ' <i class="fa-solid fa-sort text-muted" style="font-size:9px;"></i>';
                }

                th.addEventListener("click", () => {
                    if (this.sortField === field) {
                        this.sortAsc = !this.sortAsc;
                    } else {
                        this.sortField = field;
                        this.sortAsc = true;
                    }
                    this.applyFilterAndSort();
                    this.render();
                });
            });

            // Bind Search input
            const search = document.getElementById("corridor-search-box");
            if (search) {
                search.addEventListener("input", (e) => {
                    this.searchQuery = e.target.value.trim().toLowerCase();
                    this.applyFilterAndSort();
                    this.render();
                    
                    // Restore focus
                    const box = document.getElementById("corridor-search-box");
                    if (box) {
                        box.focus();
                        box.setSelectionRange(box.value.length, box.value.length);
                    }
                });
            }

            // Bind Export triggers
            const csvBtn = document.getElementById("btn-export-corridors-csv");
            if (csvBtn) {
                csvBtn.addEventListener("click", () => {
                    if (this.onExportCSVCallback) this.onExportCSVCallback(this.filteredData);
                });
            }

            const pdfBtn = document.getElementById("btn-export-corridors-pdf");
            if (pdfBtn) {
                pdfBtn.addEventListener("click", () => {
                    if (this.onExportPDFCallback) this.onExportPDFCallback(this.filteredData);
                });
            }
        },

        applyFilterAndSort() {
            // Apply Search Query filter
            if (this.searchQuery === "") {
                this.filteredData = [...this.data];
            } else {
                this.filteredData = this.data.filter(c => {
                    return c.origin.toLowerCase().includes(this.searchQuery) ||
                           c.destination.toLowerCase().includes(this.searchQuery);
                });
            }

            // Apply Sort
            this.filteredData.sort((a, b) => {
                let valA = a[this.sortField];
                let valB = b[this.sortField];

                if (typeof valA === "string") {
                    valA = valA.toLowerCase();
                    valB = valB.toLowerCase();
                }

                if (valA < valB) return this.sortAsc ? -1 : 1;
                if (valA > valB) return this.sortAsc ? 1 : -1;
                return 0;
            });
        }
    };
    window.CorridorTable = CorridorTable;
})();
