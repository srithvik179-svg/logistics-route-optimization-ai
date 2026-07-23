/**
 * Executive Reports & Insight Generator Page Controller
 * Handles template fetches, presentation activations, and multi-format exports.
 */
(function() {
    let _activeReport = null;

    async function initExecutiveReportsWorkspace() {
        console.log("[ExecutiveReports] Initializing workspace dashboard...");

        // Render controls cockpit
        window.ReportBuilder.render("reports-builder-container");

        // Spinner loadings for outputs
        ["reports-summary-container", "reports-insights-container", "reports-history-container"].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = `<div style="padding:var(--space-6); text-align:center; color:var(--text-muted);"><i class="fa-solid fa-spinner fa-spin" style="font-size:1.5rem;"></i></div>`;
        });

        try {
            // Compile default report on first load
            await compileReport("Executive Summary", "Executive Leadership");

            // Fetch report log history
            try {
                const history = await apiFetch("/api/reports/history");
                if (history) window.ReportHistory.render("reports-history-container", history);
            } catch (histErr) {
                console.warn("[ExecutiveReports] History unavailable:", histErr);
                const histEl = document.getElementById("reports-history-container");
                if (histEl) histEl.innerHTML = `<div style="padding:1rem;color:var(--text-muted);font-size:11px;text-align:center;">No report history available yet.</div>`;
            }

        } catch (err) {
            console.error("[ExecutiveReports] Error loading default report:", err);
        }
    }

    async function compileReport(reportType, template) {
        console.log(`[ExecutiveReports] Compiling report: ${reportType} (${template})...`);

        try {
            const currentFilters = window.GlobalFilters || {};

            const result = await apiFetch("/api/reports/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    report_type: reportType,
                    template: template,
                    generated_by: "analyst",
                    filters: currentFilters
                })
            });
            _activeReport = result;

            // Render components
            window.ExecutiveSummary.render("reports-summary-container", _activeReport.summary);
            window.InsightCards.render("reports-insights-container", _activeReport.insights);

            // Refresh history view so new log entry appears immediately
            try {
                const history = await apiFetch("/api/reports/history");
                if (history) window.ReportHistory.render("reports-history-container", history);
            } catch (hErr) {
                console.warn("[ExecutiveReports] History refresh error:", hErr);
            }

        } catch (err) {
            console.error("[ExecutiveReports] Compile Error:", err);
            const el = document.getElementById("reports-summary-container");
            if (el) el.innerHTML = `<div class="card glass-panel" style="padding:var(--space-6); text-align:center; color:var(--danger-color);">
                <i class="fa-solid fa-triangle-exclamation"></i> Failed to generate report.
            </div>`;
        }
    }

    async function downloadArchiveReport(id) {
        try {
            await apiFetch("/api/reports/increment-download", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id: id })
            });
            const history = await apiFetch("/api/reports/history");
            if (history) window.ReportHistory.render("reports-history-container", history);
            exportReportCSV();
        } catch (err) {
            console.warn("Archive download count increment error:", err);
            exportReportCSV();
        }
    }

    function enterPresentationMode() {
        if (!_activeReport) {
            alert("Please generate a report first.");
            return;
        }
        window.PresentationMode.open(_activeReport);
    }

    // CSV Export
    function exportReportCSV() {
        if (!_activeReport) return;
        const data = _activeReport.aggregated_data.sla_prediction.shipments || [];
        let csv = "Shipment ID,Origin,Destination,Risk Level,Breach %,Delay h,Impact USD\n";
        data.forEach(s => {
            csv += `${s.transaction_id},${s.origin},${s.destination},${s.risk_level},${s.breach_probability},${s.estimated_delay_hours},${s.business_impact_usd}\n`;
        });
        const blob = new Blob([csv], { type: "text/csv" });
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `executive_report_${_activeReport.report_id}.csv`;
        a.click();
    }

    // PDF Export
    function exportReportPDF() {
        if (!_activeReport) return;
        const summary = _activeReport.summary;
        const w = window.open("", "_blank");
        w.document.write(`
            <html>
            <head>
                <title>Executive Intelligence Report</title>
                <style>
                    body { font-family: sans-serif; padding: 2rem; color: #1f2937; }
                    h2 { color: #1e3a8a; border-bottom: 2px solid #e5e7eb; padding-bottom: 0.5rem; }
                    h3 { color: #374151; margin-top: 1.5rem; }
                    .box { background: #f3f4f6; padding: 1rem; border-radius: 8px; border: 1px solid #e5e7eb; margin: 10px 0; }
                    .kpi { display: inline-block; background: #f0f9ff; border: 1px solid #bae6fd;
                           border-radius: 6px; padding: 8px 16px; margin: 4px; text-align: center; }
                    .kpi-val { font-size: 1.2rem; font-weight: 700; color: #0369a1; display: block; }
                    .kpi-lbl { font-size: 10px; color: #6b7280; }
                </style>
            </head>
            <body>
                <h2>Dell FutureMinds Executive Intelligence Report</h2>
                <p>Generated: ${_activeReport.generation_time} | Report ID: ${_activeReport.report_id}</p>
                <p>Report Type: <strong>${_activeReport.report_type}</strong> | Focus: <strong>${_activeReport.template}</strong></p>
                
                <h3>Corporate Performance Summary</h3>
                <div class="box">
                    <strong>Business Health Score:</strong> ${summary.business_health_score}/100<br><br>
                    ${summary.business_overview}
                </div>

                <h3>Key Focus KPIs</h3>
                <div>
                    <div class="kpi"><span class="kpi-val">$${summary.financial_impact_usd.toLocaleString()}</span><span class="kpi-lbl">Projected Savings</span></div>
                    <div class="kpi"><span class="kpi-val">${summary.critical_risk_count}</span><span class="kpi-lbl">Active Risk Alerts</span></div>
                </div>

                <h3>AI-Derived Insights Summary</h3>
                <ul>
                    ${_activeReport.insights.map(ins => `
                        <li><strong>${ins.category}</strong>: ${ins.title} - ${ins.detail}</li>
                    `).join("")}
                </ul>
                <script>window.onload = function() { window.print(); }</script>
            </body>
            </html>
        `);
        w.document.close();
    }

    // Trigger compiler from dropdowns
    window.compileExecutiveReport = function() {
        const typeSelect = document.getElementById("report-type-select");
        const tempSelect = document.getElementById("report-template-select");
        if (typeSelect && tempSelect) {
            compileReport(typeSelect.value, tempSelect.value);
        }
    };

    window.loadExecutiveReportsWorkspace = initExecutiveReportsWorkspace;
    window.enterPresentationMode = enterPresentationMode;
    window.exportReportCSV = exportReportCSV;
    window.exportReportPDF = exportReportPDF;
    window.downloadArchiveReport = downloadArchiveReport;
})();
