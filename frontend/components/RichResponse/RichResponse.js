/**
 * RichResponse Component
 * Renders structured AI responses containing Summary, Metric tables, Business Impact cards, Next Actions, and deep-links.
 */
(function() {
    const RichResponse = {
        renderHtml(payload) {
            const { summary, metrics = {}, explanation, business_impact, next_actions = [], related_modules = [] } = payload;

            // Generate metrics badges/table if present
            let metricsHtml = "";
            const metricsKeys = Object.keys(metrics);
            if (metricsKeys.length > 0) {
                metricsHtml = `
                    <div style="margin-top:var(--space-2); display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:8px;">
                        ${metricsKeys.map(key => `
                            <div style="background:rgba(9, 9, 11, 0.4); border:1px solid rgba(63, 63, 70, 0.2); padding:8px; border-radius:6px; text-align:center;">
                                <div style="font-size:9px; color:var(--text-muted); text-transform:uppercase; margin-bottom:2px;">${key}</div>
                                <div style="font-size:12px; font-weight:bold; color:var(--primary-color);">${metrics[key]}</div>
                            </div>
                        `).join('')}
                    </div>
                `;
            }

            // Next Actions
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

            // Related deep-link buttons
            let linksHtml = "";
            if (related_modules.length > 0) {
                linksHtml = `
                    <div style="margin-top:var(--space-3); border-top:1px solid rgba(63, 63, 70, 0.2); padding-top:var(--space-2); display:flex; flex-wrap:wrap; gap:8px; align-items:center;">
                        <span style="font-size:9px; color:var(--text-muted); text-transform:uppercase;">View Modules:</span>
                        ${related_modules.map(mod => {
                            let label = mod.replace("-section", "").replace("-", " ");
                            // Capitalize label
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
                    <div style="font-size:12px; color:#fff; line-height:1.5; font-weight:500;">
                        ${summary}
                    </div>

                    ${metricsHtml}

                    <div style="font-size:11px; line-height:1.4; margin-top:4px;">
                        <span style="color:var(--text-muted); font-weight:bold;">Analysis:</span> ${explanation}
                    </div>

                    <div style="background:rgba(59, 130, 246, 0.05); border:1px solid rgba(59, 130, 246, 0.2); padding:8px; border-radius:6px; font-size:11px; margin-top:4px;">
                        <span style="color:var(--primary-color); font-weight:bold;"><i class="fa-solid fa-chart-line"></i> Business Impact:</span> ${business_impact}
                    </div>

                    ${actionsHtml}
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
