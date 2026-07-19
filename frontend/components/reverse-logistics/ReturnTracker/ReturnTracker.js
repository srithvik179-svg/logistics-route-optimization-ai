/**
 * ReturnTracker Component
 * Searchable/sortable return shipment grid with workflow action selectors.
 */
(function() {
    let _allReturns = [];

    const STATUS_BADGE = {
        "Pending":    "badge-warning",
        "In Transit": "badge-info",
        "Processing": "badge-primary",
        "Refurbished":"badge-success",
        "Recycled":   "badge-cyan",
        "Cancelled":  "badge-danger"
    };

    const ReturnTracker = {
        render(containerId, returns) {
            const container = document.getElementById(containerId);
            if (!container) return;

            _allReturns = returns || [];
            this._draw(container, _allReturns);
        },

        _draw(container, list) {
            if (!list.length) {
                container.innerHTML = `
                    <div class="card glass-panel" style="padding:var(--space-6); text-align:center; color:var(--text-muted);">
                        No return shipments found.
                    </div>`;
                return;
            }

            const rows = list.map(r => {
                const badge = STATUS_BADGE[r.status] || "badge-primary";
                return `
                    <tr>
                        <td><code style="font-size:10px; color:var(--text-secondary);">${r.return_id}</code></td>
                        <td><code style="font-size:10px; color:var(--text-muted);">${r.shipment_id}</code></td>
                        <td>${r.origin}</td>
                        <td>${r.destination}</td>
                        <td><span class="badge ${badge}" style="font-size:9px;">${r.status}</span></td>
                        <td style="font-size:11px;">${r.reason}</td>
                        <td style="font-size:11px;">${r.current_hub}</td>
                        <td style="font-size:11px; text-align:right;">${r.days_in_transit}d</td>
                        <td style="font-size:11px; text-align:right;">${r.estimated_completion}</td>
                        <td>
                            <select class="form-control" style="font-size:9px; padding:2px 4px; height:24px;"
                                    onchange="ReturnTracker.assignCenter('${r.return_id}', this.value)">
                                <option value="">-- Assign --</option>
                                <option value="Austin Refurb">Austin Refurb</option>
                                <option value="Houston Recycling">Houston Recycling</option>
                                <option value="Dallas TPR">Dallas TPR</option>
                            </select>
                        </td>
                    </tr>
                `;
            }).join("");

            container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up">
                    <div class="card-header" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:var(--space-2);">
                        <h3><i class="fa-solid fa-rotate-left text-primary"></i> Return Shipment Tracker</h3>
                        <div style="display:flex; gap:var(--space-2); align-items:center;">
                            <input type="text" id="return-search" placeholder="Search returns..."
                                   class="form-control" style="width:180px; font-size:11px;"
                                   oninput="ReturnTracker.filter(this.value)">
                            <select id="return-status-filter" class="form-control" style="width:130px; font-size:11px;"
                                    onchange="ReturnTracker.filterStatus(this.value)">
                                <option value="">All Statuses</option>
                                <option value="Pending">Pending</option>
                                <option value="In Transit">In Transit</option>
                                <option value="Processing">Processing</option>
                                <option value="Refurbished">Refurbished</option>
                                <option value="Recycled">Recycled</option>
                            </select>
                            <button class="btn btn-secondary btn-sm" onclick="window.exportReturnsCSV()"><i class="fa-solid fa-file-csv"></i> CSV</button>
                            <button class="btn btn-secondary btn-sm" onclick="window.exportReturnsPDF()"><i class="fa-solid fa-file-pdf"></i> PDF</button>
                        </div>
                    </div>
                    <div class="card-body" style="padding:0; overflow:auto;">
                        <div class="table-container">
                            <table class="data-table" id="returns-table">
                                <thead>
                                    <tr>
                                        <th>Return ID</th>
                                        <th>Shipment ID</th>
                                        <th>Origin</th>
                                        <th>Destination</th>
                                        <th>Status</th>
                                        <th>Reason</th>
                                        <th>Current Hub</th>
                                        <th class="text-right">Days</th>
                                        <th class="text-right">Est. Completion</th>
                                        <th>Assign Center</th>
                                    </tr>
                                </thead>
                                <tbody>${rows}</tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        },

        filter(query) {
            const q = (query || "").toLowerCase();
            const filtered = _allReturns.filter(r =>
                r.return_id.toLowerCase().includes(q) ||
                r.origin.toLowerCase().includes(q) ||
                r.destination.toLowerCase().includes(q) ||
                r.reason.toLowerCase().includes(q)
            );
            const tbody = document.querySelector("#returns-table tbody");
            if (!tbody) return;
            tbody.innerHTML = filtered.map(r => {
                const badge = STATUS_BADGE[r.status] || "badge-primary";
                return `<tr>
                    <td><code style="font-size:10px;">${r.return_id}</code></td>
                    <td><code style="font-size:10px; color:var(--text-muted);">${r.shipment_id}</code></td>
                    <td>${r.origin}</td><td>${r.destination}</td>
                    <td><span class="badge ${badge}" style="font-size:9px;">${r.status}</span></td>
                    <td style="font-size:11px;">${r.reason}</td>
                    <td style="font-size:11px;">${r.current_hub}</td>
                    <td style="font-size:11px; text-align:right;">${r.days_in_transit}d</td>
                    <td style="font-size:11px; text-align:right;">${r.estimated_completion}</td>
                    <td><select class="form-control" style="font-size:9px; padding:2px 4px; height:24px;">
                        <option value="">-- Assign --</option>
                        <option value="Austin Refurb">Austin Refurb</option>
                        <option value="Houston Recycling">Houston Recycling</option>
                        <option value="Dallas TPR">Dallas TPR</option>
                    </select></td>
                </tr>`;
            }).join("");
        },

        filterStatus(status) {
            const filtered = status ? _allReturns.filter(r => r.status === status) : _allReturns;
            const tbody = document.querySelector("#returns-table tbody");
            if (!tbody) return;
            const badge = STATUS_BADGE[status] || "badge-primary";
            tbody.innerHTML = filtered.map(r => {
                const b = STATUS_BADGE[r.status] || "badge-primary";
                return `<tr>
                    <td><code style="font-size:10px;">${r.return_id}</code></td>
                    <td><code style="font-size:10px; color:var(--text-muted);">${r.shipment_id}</code></td>
                    <td>${r.origin}</td><td>${r.destination}</td>
                    <td><span class="badge ${b}" style="font-size:9px;">${r.status}</span></td>
                    <td style="font-size:11px;">${r.reason}</td>
                    <td style="font-size:11px;">${r.current_hub}</td>
                    <td style="font-size:11px; text-align:right;">${r.days_in_transit}d</td>
                    <td style="font-size:11px; text-align:right;">${r.estimated_completion}</td>
                    <td><select class="form-control" style="font-size:9px; padding:2px 4px; height:24px;">
                        <option>-- Assign --</option>
                        <option>Austin Refurb</option>
                        <option>Houston Recycling</option>
                        <option>Dallas TPR</option>
                    </select></td>
                </tr>`;
            }).join("");
        },

        assignCenter(returnId, center) {
            if (!center) return;
            console.log(`[ReturnTracker] Assigned ${returnId} → ${center}`);
            // Show a small toast notification
            const toast = document.createElement("div");
            toast.style.cssText = `position:fixed; bottom:20px; right:20px; background:rgba(16,185,129,0.9); color:#fff;
                                   padding:10px 16px; border-radius:8px; font-size:12px; z-index:9999;
                                   animation: fadeIn 0.3s ease;`;
            toast.textContent = `✓ ${returnId} assigned to ${center}`;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }
    };

    window.ReturnTracker = ReturnTracker;
})();
