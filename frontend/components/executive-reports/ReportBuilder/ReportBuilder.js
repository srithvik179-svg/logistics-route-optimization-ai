/**
 * ReportBuilder Component
 * Formulates interactive selector cockpit for reports and templates parameters.
 */
(function() {
    const ReportBuilder = {
        render(containerId) {
            const el = document.getElementById(containerId);
            if (!el) return;

            el.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="border: 1px solid rgba(59, 130, 246, 0.4); background: rgba(59, 130, 246, 0.05); padding: var(--space-4);">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:var(--space-3);">
                        <div>
                            <h2 style="margin:0 0 4px 0; color:#fff; font-size:1.4rem;"><i class="fa-solid fa-file-invoice-dollar text-primary"></i> Executive Reporting Cockpit</h2>
                            <p style="margin:0; font-size:11px; color:var(--text-secondary); line-height:1.4;">Select a report template focus group and format category to compile structured executive insights.</p>
                        </div>
                        <div style="display:flex; gap:var(--space-2); align-items:center; flex-wrap:wrap;">
                            <select id="report-type-select" class="form-control" style="width:200px; font-size:11px;">
                                <option>Executive Summary</option>
                                <option>Network Performance Report</option>
                                <option>Route Optimization Report</option>
                                <option>Corridor Efficiency Report</option>
                                <option>Cost Optimization Report</option>
                                <option>Reverse Logistics Report</option>
                                <option>SLA Compliance Report</option>
                                <option>Operational Risk Report</option>
                                <option>Weekly Operations Report</option>
                                <option>Monthly Operations Report</option>
                            </select>
                            <select id="report-template-select" class="form-control" style="width:160px; font-size:11px;">
                                <option>Executive Leadership</option>
                                <option>Operations Manager</option>
                                <option>Regional Manager</option>
                                <option>Supply Chain Head</option>
                                <option>Business Analyst</option>
                            </select>
                            <button class="btn btn-primary" onclick="window.compileExecutiveReport()">
                                <i class="fa-solid fa-gears"></i> Generate Report
                            </button>
                            <button class="btn btn-secondary" onclick="window.enterPresentationMode()">
                                <i class="fa-solid fa-expand"></i> Present Slide Mode
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }
    };
    window.ReportBuilder = ReportBuilder;
})();
