/**
 * RichResponse Component
 * Renders structured AI responses containing Summary, Metric cards, Data Tables,
 * Business Impact, Next Actions, Confidence Score, Data Sources, and Deep-links.
 */
(function() {
    const RichResponse = {
        renderHtml(payload) {
            const {
                summary = "",
                metrics = {},
                explanation = "",
                table = null,
                business_impact = "",
                next_actions = [],
                confidence = null,
                data_sources = [],
                related_modules = []
            } = payload;

            // 1. Confidence Badge
            let confidenceHtml = "";
            if (confidence) {
                confidenceHtml = `
                    <span style="float:right; font-size:9px; background:rgba(16, 185, 129, 0.12); color:#10b981; padding:2px 7px; border-radius:4px; border:1px solid rgba(16, 185, 129, 0.3); font-weight:600;">
                        <i class="fa-solid fa-shield-halved"></i> Confidence: ${confidence}
                    </span>
                `;
            }

            // 2. Metrics Badges
            let metricsHtml = "";
            const metricsKeys = Object.keys(metrics);
            if (metricsKeys.length > 0) {
                metricsHtml = `
                    <div style="margin-top:var(--space-2); display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:8px;">
                        ${metricsKeys.map(key => `
                            <div style="background:rgba(18, 18, 22, 0.6); border:1px solid rgba(63, 63, 70, 0.3); padding:8px 10px; border-radius:6px; text-align:center;">
                                <div style="font-size:9px; color:var(--text-muted); text-transform:uppercase; margin-bottom:2px; font-weight:600;">${key}</div>
                                <div style="font-size:12px; font-weight:bold; color:var(--primary-color);">${metrics[key]}</div>
                            </div>
                        `).join('')}
                    </div>
                `;
            }

            // 3. Structured Data Table
            let tableHtml = "";
            if (table && table.headers && table.rows && table.rows.length > 0) {
                tableHtml = `
                    <div style="margin-top:var(--space-3); overflow-x:auto; border:1px solid rgba(63, 63, 70, 0.4); border-radius:6px;">
                        <table style="width:100%; border-collapse:collapse; font-size:10px; text-align:left;">
                            <thead>
                                <tr style="background:rgba(30, 30, 36, 0.8); border-bottom:1px solid rgba(63, 63, 70, 0.4);">
                                    ${table.headers.map(h => `<th style="padding:6px 10px; color:var(--text-muted); font-weight:600; text-transform:uppercase;">${h}</th>`).join('')}
                                </tr>
                            </thead>
                            <tbody>
                                ${table.rows.map((row, idx) => `
                                    <tr style="border-bottom:1px solid rgba(63, 63, 70, 0.15); background:${idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)'};">
                                        ${row.map(cell => `<td style="padding:6px 10px; color:#fff;">${cell}</td>`).join('')}
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
            }

            // 4. Next Actions
            let actionsHtml = "";
            if (next_actions.length > 0) {
                actionsHtml = `
                    <div style="margin-top:var(--space-2);">
                        <div style="font-size:10px; font-weight:bold; color:var(--text-secondary); text-transform:uppercase; margin-bottom:4px;">Suggested Actions</div>
                        <ul style="margin:0; padding-left:14px; font-size:11px; color:#fff; display:flex; flex-direction:column; gap:4px;">
                            ${next_actions.map(act => `<li>${act}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }

            // 5. Data Sources Footer
            let dataSourcesHtml = "";
            if (data_sources.length > 0) {
                dataSourcesHtml = `
                    <div style="font-size:9px; color:var(--text-muted); margin-top:4px;">
                        <i class="fa-solid fa-database" style="margin-right:3px;"></i> <strong>Data Sources:</strong> ${data_sources.join(" · ")}
                    </div>
                `;
            }

            // 6. Related deep-link buttons
            let linksHtml = "";
            if (related_modules.length > 0) {
                linksHtml = `
                    <div style="margin-top:var(--space-3); border-top:1px solid rgba(63, 63, 70, 0.25); padding-top:var(--space-2); display:flex; flex-wrap:wrap; gap:8px; align-items:center;">
                        <span style="font-size:9px; color:var(--text-muted); text-transform:uppercase;">View Modules:</span>
                        ${related_modules.map(mod => {
                            let label = mod.replace("-section", "").replace("command-3d", "3D Command").replace("-", " ");
                            label = label.charAt(0).toUpperCase() + label.slice(1);
                            return `
                                <button class="btn btn-secondary btn-sm" onclick="RichResponse.navigateToModule('${mod}')" style="font-size:9px; padding:3px 8px;">
                                    <i class="fa-solid fa-arrow-up-right-from-square"></i> Open ${label}
                                </button>
                            `;
                        }).join('')}
                    </div>
                `;
            }

            return `
                <div class="rich-response-container" style="display:flex; flex-direction:column; gap:var(--space-2); font-family:sans-serif; color:var(--text-secondary);">
                    <div>
                        ${confidenceHtml}
                        <div style="font-size:12px; color:#fff; line-height:1.5; font-weight:500;">
                            ${summary}
                        </div>
                    </div>

                    ${metricsHtml}
                    ${tableHtml}

                    ${explanation ? `
                        <div style="font-size:11px; line-height:1.4; margin-top:4px;">
                            <span style="color:var(--text-muted); font-weight:bold;">Analysis:</span> ${explanation}
                        </div>
                    ` : ''}

                    ${business_impact ? `
                        <div style="background:rgba(59, 130, 246, 0.08); border:1px solid rgba(59, 130, 246, 0.25); padding:8px 10px; border-radius:6px; font-size:11px; margin-top:4px;">
                            <span style="color:var(--primary-color); font-weight:bold;"><i class="fa-solid fa-chart-line"></i> Business Impact:</span> ${business_impact}
                        </div>
                    ` : ''}

                    ${actionsHtml}
                    ${dataSourcesHtml}
                    ${linksHtml}
                </div>
            `;
        },

        navigateToModule(sectionId) {
            console.log(`[CopilotLink] Navigating viewport to section: ${sectionId}`);
            const link = document.querySelector(`.nav-link[data-target="${sectionId}"]`);
            if (link) {
                link.click();
            }
        }
    };

    window.RichResponse = RichResponse;
})();
