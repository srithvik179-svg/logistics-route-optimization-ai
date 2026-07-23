/**
 * AlertCenter Component
 * Renders categorized operational alerts with dismiss, acknowledge, and assign actions.
 * Fixed: status fallback, _renderRows onclick handlers, filter state preservation, color fallbacks.
 */
(function() {
    let _alerts    = [];
    let _sevFilter = "";
    let _txtFilter = "";

    // Severity → color mapping used when API data has no color field
    const SEV_COLORS = {
        "Critical": "#f87171",
        "High":     "#fb923c",
        "Moderate": "#facc15",
        "Medium":   "#facc15",
        "Low":      "#34d399",
        "Info":     "#60a5fa"
    };

    function _makeRows(list) {
        return list.map(alt => {
            const status  = alt.status   || "Active";
            const color   = alt.color    || SEV_COLORS[alt.severity] || "#a1a1aa";
            const severity = alt.severity || "—";
            const isDismissed = status === "Dismissed";

            const assigned = alt.assigned_to
                ? `<span style="font-size:10px;color:#10b981;"><i class="fa-solid fa-user-check"></i> ${alt.assigned_to}</span>`
                : `<select class="form-control"
                           style="font-size:9px;height:22px;padding:2px 4px;width:100px;"
                           onchange="AlertCenter.assignAlert('${alt.id}',this.value)">
                       <option value="">-- Assign --</option>
                       <option value="Manager-A">Manager-A</option>
                       <option value="Manager-B">Manager-B</option>
                       <option value="Analyst-A">Analyst-A</option>
                   </select>`;

            const statusBadgeColor = {
                "Acknowledged": "#34d399",
                "Dismissed":    "#71717a",
                "Assigned":     "#60a5fa",
                "Active":       "#facc15"
            }[status] || "#a1a1aa";

            const actionBtns = isDismissed
                ? `<span style="font-size:10px;color:var(--text-muted);">Archived</span>`
                : `<button class="btn btn-secondary btn-sm"
                           style="font-size:9px;padding:2px 6px;"
                           onclick="AlertCenter.ackAlert('${alt.id}')">Ack</button>
                   <button class="btn btn-danger btn-sm"
                           style="font-size:9px;padding:2px 6px;"
                           onclick="AlertCenter.dismissAlert('${alt.id}')">Dismiss</button>`;

            return `
                <tr style="opacity:${isDismissed ? 0.5 : 1};">
                    <td><span class="badge"
                              style="background:${color}22;color:${color};border:1px solid ${color}55;font-size:9px;white-space:nowrap;">
                        ${severity}
                    </span></td>
                    <td style="font-size:11px;font-weight:600;color:#fff;">${alt.type || '—'}</td>
                    <td style="font-size:11px;color:var(--text-secondary);">${alt.message || '—'}</td>
                    <td><span class="badge"
                              style="background:${statusBadgeColor}22;color:${statusBadgeColor};
                                     border:1px solid ${statusBadgeColor}44;font-size:9px;">
                        ${status}
                    </span></td>
                    <td>${assigned}</td>
                    <td style="text-align:right;">${actionBtns}</td>
                </tr>`;
        }).join("");
    }

    function _applyFilters() {
        let list = _alerts;
        if (_sevFilter) list = list.filter(a => (a.severity || "") === _sevFilter);
        if (_txtFilter) list = list.filter(a => ((a.type || "") + (a.message || "")).toLowerCase().includes(_txtFilter));
        return list;
    }

    function _refreshTable() {
        const tbody = document.querySelector("#command-center-alerts-table tbody");
        if (tbody) tbody.innerHTML = _makeRows(_applyFilters());
    }

    const AlertCenter = {
        render(containerId, alerts) {
            const el = document.getElementById(containerId);
            if (!el) return;
            // Normalise status so badge never shows "undefined"
            _alerts = (alerts || []).map(a => ({ ...a, status: a.status || "Active" }));
            _sevFilter = "";
            _txtFilter = "";
            this._draw(el);
        },

        _draw(el) {
            el.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="border:1px solid rgba(63,63,70,0.4);">
                    <div class="card-header"
                         style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:var(--space-2);">
                        <h3><i class="fa-solid fa-triangle-exclamation text-danger"></i> System Alert Command Center
                            <span style="font-size:10px;color:#71717a;font-weight:400;margin-left:8px;">
                                ${_alerts.length} alerts
                            </span>
                        </h3>
                        <div style="display:flex;gap:var(--space-2);align-items:center;flex-wrap:wrap;">
                            <input type="text" placeholder="Search alerts…" class="form-control"
                                   style="width:150px;font-size:11px;"
                                   oninput="AlertCenter.filter(this.value)">
                            <select class="form-control" style="width:130px;font-size:11px;"
                                    onchange="AlertCenter.filterSeverity(this.value)">
                                <option value="">All Severities</option>
                                <option>Critical</option>
                                <option>High</option>
                                <option>Moderate</option>
                                <option>Low</option>
                            </select>
                            <button class="btn btn-secondary btn-sm"
                                    style="font-size:10px;padding:2px 8px;"
                                    onclick="AlertCenter.resetFilters()">
                                <i class="fa-solid fa-filter-circle-xmark"></i> Reset
                            </button>
                        </div>
                    </div>
                    <div class="card-body" style="padding:0;overflow-y:auto;max-height:380px;">
                        <div class="table-container" style="overflow-x:auto;">
                            <table class="data-table" id="command-center-alerts-table" style="min-width:700px;">
                                <thead>
                                    <tr>
                                        <th style="width:85px;">Severity</th>
                                        <th style="width:130px;">Type</th>
                                        <th>Description</th>
                                        <th style="width:100px;">Status</th>
                                        <th style="width:110px;">Assignment</th>
                                        <th class="text-right" style="width:120px;">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>${_makeRows(_applyFilters())}</tbody>
                            </table>
                        </div>
                    </div>
                </div>`;
        },

        ackAlert(id) {
            const alt = _alerts.find(a => String(a.id) === String(id));
            if (alt) {
                alt.status = "Acknowledged";
                _refreshTable();
            }
        },

        dismissAlert(id) {
            const alt = _alerts.find(a => String(a.id) === String(id));
            if (alt) {
                alt.status = "Dismissed";
                _refreshTable();
            }
        },

        assignAlert(id, val) {
            if (!val) return;
            const alt = _alerts.find(a => String(a.id) === String(id));
            if (alt) {
                alt.assigned_to = val;
                alt.status = "Assigned";
                _refreshTable();
            }
        },

        filter(q) {
            _txtFilter = q.toLowerCase().trim();
            _refreshTable();
        },

        filterSeverity(sev) {
            _sevFilter = sev;
            _refreshTable();
        },

        resetFilters() {
            _sevFilter = "";
            _txtFilter = "";
            // Reset UI controls
            const sel = document.querySelector("#command-center-alerts-table")
                ?.closest(".card")?.querySelector("select");
            if (sel) sel.value = "";
            const inp = document.querySelector("#command-center-alerts-table")
                ?.closest(".card")?.querySelector("input");
            if (inp) inp.value = "";
            _refreshTable();
        }
    };

    window.AlertCenter = AlertCenter;
})();
