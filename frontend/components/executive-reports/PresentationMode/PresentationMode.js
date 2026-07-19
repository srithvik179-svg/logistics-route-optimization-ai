/**
 * PresentationMode Component
 * Interactive full-screen dark-theme presentation overlay for slide-deck navigations.
 */
(function() {
    let _report = null;
    let _activeSlide = 0;

    const PresentationMode = {
        open(report) {
            _report = report;
            _activeSlide = 0;

            const modal = document.createElement("div");
            modal.id = "presentation-overlay";
            modal.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background: #09090b; z-index: 99999; display: flex; flex-direction: column;
                justify-content: space-between; padding: 2rem; color: #fff;
                animation: fadeIn 0.3s ease; font-family: sans-serif;
            `;

            document.body.appendChild(modal);
            this._drawSlide();
        },

        close() {
            const el = document.getElementById("presentation-overlay");
            if (el) el.remove();
        },

        next() {
            if (_activeSlide < 4) {
                _activeSlide++;
                this._drawSlide();
            }
        },

        prev() {
            if (_activeSlide > 0) {
                _activeSlide--;
                this._drawSlide();
            }
        },

        _drawSlide() {
            const overlay = document.getElementById("presentation-overlay");
            if (!overlay || !_report) return;

            const summary = _report.summary;
            const focus = _report.focus_areas.join(", ");

            const slides = [
                // Slide 1: Welcome & assessment
                `
                <div>
                    <span style="font-size:12px; color:#3b82f6; text-transform:uppercase; font-weight:700;">Slide 1 / 5 — Overview</span>
                    <h1 style="font-size:2.4rem; margin:1rem 0; color:#fff;">Corporate Logistics Operations Overview</h1>
                    <div style="font-size:1.6rem; line-height:1.6; color:#a1a1aa; background:#18181b; padding:1.5rem; border-radius:12px; border:1px solid #27272a; margin-top:2rem;">
                        ${summary.business_overview}
                    </div>
                </div>
                `,
                // Slide 2: KPI metrics
                `
                <div>
                    <span style="font-size:12px; color:#3b82f6; text-transform:uppercase; font-weight:700;">Slide 2 / 5 — KPIs</span>
                    <h1 style="font-size:2.4rem; margin:1rem 0; color:#fff;">Operational Health & Focus Areas</h1>
                    <p style="color:#a1a1aa; font-size:1.1rem; margin-bottom:2rem;">Focus Template: <strong>${_report.template}</strong> (Target Sections: ${focus})</p>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-top:2rem;">
                        <div style="padding:1.5rem; background:#18181b; border:1px solid #27272a; border-radius:12px; text-align:center;">
                            <span style="font-size:12px; color:#a1a1aa;">FINANCIAL IMPACT</span>
                            <div style="font-size:3rem; font-weight:800; color:#10b981; margin-top:10px;">$${summary.financial_impact_usd.toLocaleString()}</div>
                        </div>
                        <div style="padding:1.5rem; background:#18181b; border:1px solid #27272a; border-radius:12px; text-align:center;">
                            <span style="font-size:12px; color:#a1a1aa;">BUSINESS HEALTH SCORE</span>
                            <div style="font-size:3rem; font-weight:800; color:#ef4444; margin-top:10px;">${summary.business_health_score}/100</div>
                        </div>
                    </div>
                </div>
                `,
                // Slide 3: Executive Insights
                `
                <div>
                    <span style="font-size:12px; color:#3b82f6; text-transform:uppercase; font-weight:700;">Slide 3 / 5 — Key Insights</span>
                    <h1 style="font-size:2.4rem; margin:1rem 0; color:#fff;">AI-Generated Network Insights</h1>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:2rem;">
                        ${_report.insights.map(ins => `
                            <div style="padding:12px; background:#18181b; border-left:4px solid ${ins.color}; border-radius:6px;">
                                <strong style="color:${ins.color}; font-size:12px; text-transform:uppercase;">${ins.category}</strong>
                                <h4 style="margin:4px 0; color:#fff;">${ins.title}</h4>
                                <p style="margin:0; font-size:11px; color:#a1a1aa; line-height:1.4;">${ins.detail}</p>
                            </div>
                        `).join("")}
                    </div>
                </div>
                `,
                // Slide 4: Route recommendations
                `
                <div>
                    <span style="font-size:12px; color:#3b82f6; text-transform:uppercase; font-weight:700;">Slide 4 / 5 — Routing Actions</span>
                    <h1 style="font-size:2.4rem; margin:1rem 0; color:#fff;">Recommended Routing Interventions</h1>
                    <div style="font-size:1.2rem; line-height:1.6; color:#a1a1aa; background:#18181b; padding:1.5rem; border-radius:12px; border:1px solid #27272a; margin-top:2rem;">
                        <ul>
                            <li style="margin-bottom:10px;">Execute express path bypasses on recommended route: <strong>${_report.aggregated_data.sla_prediction.decision ? _report.aggregated_data.sla_prediction.decision.best_route : 'HUB-A → HUB-B'}</strong></li>
                            <li style="margin-bottom:10px;">Re-distribute returns logistics inbound stream to avoid Dallas capacity locks.</li>
                            <li>Commit Simulated driver shifts to secure What-If savings target.</li>
                        </ul>
                    </div>
                </div>
                `,
                // Slide 5: Appendix & stats
                `
                <div>
                    <span style="font-size:12px; color:#3b82f6; text-transform:uppercase; font-weight:700;">Slide 5 / 5 — End of Deck</span>
                    <h1 style="font-size:2.4rem; margin:1rem 0; color:#fff;">Interactive Reporting Analytics Summary</h1>
                    <p style="color:#a1a1aa; font-size:1.1rem; margin-bottom:2rem;">Dell FutureMinds Logistics Intelligence Platform — Phase 47 Complete.</p>
                    <div style="font-size:1.1rem; color:#a1a1aa; background:#18181b; padding:1.5rem; border-radius:12px; border:1px solid #27272a; text-align:center;">
                        Generated: ${_report.generation_time} | Report ID: ${_report.report_id}<br>
                        Export to PDF, PowerPoint, or Excel is ready.
                    </div>
                </div>
                `
            ];

            overlay.innerHTML = `
                <!-- Top Exit Header -->
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #27272a; padding-bottom:1rem;">
                    <div style="font-size:1.1rem; font-weight:700; color:#fff;">
                        <i class="fa-solid fa-crown text-warning"></i> Dell FutureMinds presentation Mode
                    </div>
                    <button onclick="PresentationMode.close()" 
                            style="background:#ef4444; border:none; color:#fff; padding:6px 12px; border-radius:6px; font-weight:600; cursor:pointer;">
                        Exit Slide Mode
                    </button>
                </div>

                <!-- Slide Content Container -->
                <div style="flex:1; display:flex; flex-direction:column; justify-content:center; padding:2rem 0;">
                    ${slides[_activeSlide]}
                </div>

                <!-- Bottom Controls Nav -->
                <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid #27272a; padding-top:1rem;">
                    <div>
                        <button onclick="PresentationMode.prev()" ${_activeSlide === 0 ? "disabled" : ""}
                                style="background:#27272a; border:none; color:#fff; padding:8px 16px; border-radius:6px; cursor:pointer; margin-right:10px; opacity:${_activeSlide === 0 ? 0.4 : 1};">
                            ← Previous Slide
                        </button>
                        <button onclick="PresentationMode.next()" ${_activeSlide === 4 ? "disabled" : ""}
                                style="background:#3b82f6; border:none; color:#fff; padding:8px 16px; border-radius:6px; cursor:pointer; opacity:${_activeSlide === 4 ? 0.4 : 1};">
                            Next Slide →
                        </button>
                    </div>
                    <div style="font-size:11px; color:#a1a1aa;">
                        Press Esc or click top right to exit presentation.
                    </div>
                </div>
            `;
        }
    };

    window.PresentationMode = PresentationMode;
})();
