/**
 * AlertCenter Component
 * Renders categorized operational alerts with dismiss, acknowledge, and assign actions.
 */
(function() {
    let _alerts = [];

    const AlertCenter = {
        render(containerId, alerts) {
            const el = document.getElementById(containerId);
            if (!el) return;
            _alerts = alerts || [];
            this._draw(el, _alerts);
        },

        _draw(el, list) {
            const rows = list.map(alt => {
                const assigned = alt.assigned_to 
                    ? `<span style="font-size:10px; color:#10b981;"><i class="fa-solid fa-user-check"></i> ${alt.assigned_to}</span>`
                    : `
                        <select class="form-control" style="font-size:9px; height:22px; padding:2px 4px; width:100px;"
                                onchange="AlertCenter.assignAlert('${alt.id}', this.value)">
                            <option value="">-- Assign --</option>
                            <option value="Manager-A">Manager-A</option>
                            <option value="Manager-B">Manager-B</option>
                            <option value="Analyst-A">Analyst-A</option>
                        </select>
                      `;

                const actionBtns = alt.status === "Dismissed" 
                    ? '<span style="font-size:10px; color:var(--text-muted);">Archived</span>'
                    : `
                        <button class="btn btn-secondary btn-sm" style="font-size:9px; padding:2px 6px;" onclick="AlertCenter.ackAlert('${alt.id}')">Ack</button>
                        <button class="btn btn-danger btn-sm" style="font-size:9px; padding:2px 6px;" onclick="AlertCenter.dismissAlert('${alt.id}')">Dismiss</button>
                      `;

                return `
                    <tr id="alert-row-${alt.id}" style="opacity:${alt.status === 'Dismissed' ? 0.5 : 1};">
                        <td><span class="badge" style="background:${alt.color}22; color:${alt.color}; border:1px solid ${alt.color}44; font-size:9px;">${alt.severity}</span></td>
                        <td style="font-size:11px; font-weight:600; color:#fff;">${alt.type}</td>
                        <td style="font-size:11px; color:var(--text-secondary);">${alt.message}</td>
                        <td><span class="badge badge-info" style="font-size:9px;">${alt.status}</span></td>
                        <td>${assigned}</td>
                        <td style="text-align:right;">${actionBtns}</td>
                    </tr>
                `;
            }).join("");

            el.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="border: 1px solid rgba(63, 63, 70, 0.4);">
                    <div class="card-header" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:var(--space-2);">
                        <h3><i class="fa-solid fa-triangle-exclamation text-danger"></i> System Alert Command Center</h3>
                        <div style="display:flex; gap:var(--space-2); align-items:center;">
                            <input type="text" placeholder="Search alerts..." class="form-control" style="width:160px; font-size:11px;"
                                   oninput="AlertCenter.filter(this.value)">
                            <select class="form-control" style="width:120px; font-size:11px;" onchange="AlertCenter.filterSeverity(this.value)">
                                <option value="">All Severities</option>
                                <option>Critical</option>
                                <option>High</option>
                                <option>Moderate</option>
                                <option>Low</option>
                            </select>
                        </div>
                    </div>
                    <div class="card-body" style="padding:0; overflow-y:auto; max-height:260px;">
                        <div class="table-container">
                            <table class="data-table" id="command-center-alerts-table">
                                <thead>
                                    <tr>
                                        <th>Severity</th>
                                        <th>Type</th>
                                        <th>Description</th>
                                        <th>Status</th>
                                        <th>Assignment</th>
                                        <th class="text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>${rows}</tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        },

        ackAlert(id) {
            const alt = _alerts.find(a => a.id === id);
            if (alt) {
                alt.status = "Acknowledged";
                console.log(`[AlertCenter] Acknowledged alert: ${id}`);
                // Refresh table body
                this._refresh();
            }
        },

        dismissAlert(id) {
            const alt = _alerts.find(a => a.id === id);
            if (alt) {
                alt.status = "Dismissed";
                console.log(`[AlertCenter] Dismissed alert: ${id}`);
                this._refresh();
            }
        },

        assignAlert(id, val) {
            if (!val) return;
            const alt = _alerts.find(a => a.id === id);
            if (alt) {
                alt.assigned_to = val;
                alt.status = "Assigned";
                console.log(`[AlertCenter] Assigned alert ${id} to ${val}`);
                this._refresh();
            }
        },

        filter(q) {
            const filtered = _alerts.filter(a => (a.type + a.message).toLowerCase().includes(q.toLowerCase()));
            this._renderRows(filtered);
        },

        filterSeverity(sev) {
            const filtered = sev ? _alerts.filter(a => a.severity === sev) : _alerts;
            this._renderRows(filtered);
        },

        _refresh() {
            this._renderRows(_alerts);
        },

        _renderRows(list) {
            const tbody = document.querySelector("#command-center-alerts-table tbody");
            if (!tbody) return;

            tbody.innerHTML = list.map(alt => {
                const assigned = alt.assigned_to 
                    ? `<span style="font-size:10px; color:#10b981;"><i class="fa-solid fa-user-check"></i> ${alt.assigned_to}</span>`
                    : `
                        <select class="form-control" style="font-size:9px; height:22px; padding:2px 4px; width:100px;">
                            <option value="">-- Assign --</option>
                            <option value="Manager-A">Manager-A</option>
                            <option value="Manager-B">Manager-B</option>
                            <option value="Analyst-A">Analyst-A</option>
                        </select>
                      `;

                const actionBtns = alt.status === "Dismissed" 
                    ? '<span style="font-size:10px; color:var(--text-muted);">Archived</span>'
                    : `
                        <button class="btn btn-secondary btn-sm" style="font-size:9px; padding:2px 6px;">Ack</button>
                        <button class="btn btn-danger btn-sm" style="font-size:9px; padding:2px 6px;">Dismiss</button>
                      `;

                return `
                    <tr style="opacity:${alt.status === 'Dismissed' ? 0.5 : 1};">
                        <td><span class="badge" style="background:${alt.color}22; color:${alt.color}; border:1px solid ${alt.color}44; font-size:9px;">${alt.severity}</span></td>
                        <td style="font-size:11px; font-weight:600; color:#fff;">${alt.type}</td>
                        <td style="font-size:11px; color:var(--text-secondary);">${alt.message}</td>
                        <td><span class="badge badge-info" style="font-size:9px;">${alt.status}</span></td>
                        <td>${assigned}</td>
                        <td style="text-align:right;">${actionBtns}</td>
                    </tr>
                `;
            }).join("");
        }
    };
    window.AlertCenter = AlertCenter;
})();
