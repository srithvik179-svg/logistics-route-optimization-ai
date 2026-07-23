/**
 * ShipmentRiskTable Component
 * Sortable/filterable table of all risk-scored shipments with inline risk indicators.
 */
(function() {
    let _all = [];

    const ShipmentRiskTable = {
        render(containerId, shipments) {
            const el = document.getElementById(containerId);
            if (!el) return;
            _all = shipments || [];
            this._draw(el, _all);
        },

        _draw(el, list) {
            const rows = list.map(s => `
                <tr>
                    <td><code style="font-size:10px;">${s.transaction_id}</code></td>
                    <td>${s.origin}</td>
                    <td>${s.destination}</td>
                    <td>
                        <div style="display:flex;align-items:center;gap:6px;">
                            <div style="width:${Math.round(s.risk_score)}%;max-width:60px;height:5px;background:${s.risk_color};border-radius:3px;"></div>
                            <span style="font-size:10px;font-weight:600;color:${s.risk_color};">${s.risk_score}</span>
                        </div>
                    </td>
                    <td><span class="badge" style="background:${s.risk_color}22;color:${s.risk_color};border:1px solid ${s.risk_color}44;font-size:9px;padding:2px 7px;border-radius:999px;">${s.risk_level}</span></td>
                    <td style="text-align:right;font-size:11px;color:${s.breach_probability>60?'#ef4444':'#a1a1aa'};">${s.breach_probability}%</td>
                    <td style="text-align:right;font-size:11px;">${s.estimated_delay_hours}h</td>
                    <td style="text-align:right;font-size:11px;">${s.confidence_score}%</td>
                    <td style="font-size:10px;color:var(--text-secondary);">${s.likely_causes.join(", ")}</td>
                    <td style="text-align:right;font-size:11px;">${window.Formatters.safeCurrency(s.business_impact_usd)}</td>
                </tr>`).join("");

            el.innerHTML = `
                <div class="card glass-panel fade-in-slide-up">
                    <div class="card-header" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:var(--space-2);">
                        <h3><i class="fa-solid fa-triangle-exclamation text-danger"></i> Shipment Risk Register</h3>
                        <div style="display:flex;gap:var(--space-2);align-items:center;">
                            <input type="text" placeholder="Search shipments..." class="form-control" style="width:170px;font-size:11px;"
                                   oninput="ShipmentRiskTable.filter(this.value)">
                            <select class="form-control" style="width:130px;font-size:11px;" onchange="ShipmentRiskTable.filterLevel(this.value)">
                                <option value="">All Levels</option>
                                <option>Very Low</option><option>Low</option>
                                <option>Moderate</option><option>High</option><option>Critical</option>
                            </select>
                            <button class="btn btn-secondary btn-sm" onclick="window.exportRiskCSV()"><i class="fa-solid fa-file-csv"></i> CSV</button>
                            <button class="btn btn-secondary btn-sm" onclick="window.exportRiskPDF()"><i class="fa-solid fa-file-pdf"></i> PDF</button>
                        </div>
                    </div>
                    <div class="card-body" style="padding:0;overflow:auto;">
                        <div class="table-container">
                            <table class="data-table" id="risk-table">
                                <thead>
                                    <tr>
                                        <th>Shipment ID</th><th>Origin</th><th>Destination</th>
                                        <th>Risk Score</th><th>Risk Level</th>
                                        <th class="text-right">Breach %</th>
                                        <th class="text-right">Delay (h)</th>
                                        <th class="text-right">Confidence</th>
                                        <th>Likely Causes</th>
                                        <th class="text-right">Impact</th>
                                    </tr>
                                </thead>
                                <tbody>${rows}</tbody>
                            </table>
                        </div>
                    </div>
                </div>`;
        },

        _redraw(list) {
            const tbody = document.querySelector("#risk-table tbody");
            if (!tbody) return;
            tbody.innerHTML = list.map(s => `
                <tr>
                    <td><code style="font-size:10px;">${s.transaction_id}</code></td>
                    <td>${s.origin}</td><td>${s.destination}</td>
                    <td><div style="display:flex;align-items:center;gap:6px;">
                        <div style="width:${Math.round(s.risk_score)}%;max-width:60px;height:5px;background:${s.risk_color};border-radius:3px;"></div>
                        <span style="font-size:10px;font-weight:600;color:${s.risk_color};">${s.risk_score}</span></div></td>
                    <td><span class="badge" style="background:${s.risk_color}22;color:${s.risk_color};border:1px solid ${s.risk_color}44;font-size:9px;padding:2px 7px;border-radius:999px;">${s.risk_level}</span></td>
                    <td style="text-align:right;font-size:11px;color:${s.breach_probability>60?'#ef4444':'#a1a1aa'};">${s.breach_probability}%</td>
                    <td style="text-align:right;font-size:11px;">${s.estimated_delay_hours}h</td>
                    <td style="text-align:right;font-size:11px;">${s.confidence_score}%</td>
                    <td style="font-size:10px;color:var(--text-secondary);">${s.likely_causes.join(", ")}</td>
                    <td style="text-align:right;font-size:11px;">${window.Formatters.safeCurrency(s.business_impact_usd)}</td>
                </tr>`).join("");
        },

        filter(q) { this._redraw(_all.filter(s => (s.transaction_id+s.origin+s.destination).toLowerCase().includes(q.toLowerCase()))); },
        filterLevel(l) { this._redraw(l ? _all.filter(s => s.risk_level === l) : _all); }
    };

    window.exportRiskCSV = function() {
        let csv = "Shipment ID,Origin,Destination,Risk Score,Risk Level,Breach %,Delay (h),Confidence,Likely Causes,Impact\n";
        const rows = document.querySelectorAll("#risk-table tbody tr");
        rows.forEach(tr => {
            const cols = Array.from(tr.querySelectorAll("td")).map(td => `"${td.textContent.trim().replace(/"/g, '""')}"`);
            if (cols.length >= 10) csv += cols.join(",") + "\n";
        });
        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `dell_shipment_risks_${new Date().toISOString().slice(0,10)}.csv`;
        a.click();
        if (window.Toast) window.Toast.success("Shipment Risks CSV report exported.");
    };

    window.exportRiskPDF = function() {
        const printWindow = window.open("", "_blank");
        if (!printWindow) return alert("Please allow popups to export PDF.");
        printWindow.document.write(`
            <html><head><title>Dell SLA Risk Register Report</title>
            <style>body{font-family:sans-serif;padding:20px;} table{width:100%;border-collapse:collapse;} th,td{border:1px solid #ccc;padding:8px;font-size:12px;}</style>
            </head><body>
            <h2>Dell SLA Risk Register & Delay Predictions</h2>
            <p>Generated: ${new Date().toLocaleString()}</p>
            ${document.getElementById("risk-table") ? document.getElementById("risk-table").outerHTML : ""}
            <script>window.onload = function() { window.print(); }</script>
            </body></html>
        `);
        printWindow.document.close();
    };

    window.ShipmentRiskTable = ShipmentRiskTable;
})();
