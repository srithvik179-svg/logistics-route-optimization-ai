/**
 * RouteTimeline Component
 * Interactive stage-by-stage timeline visualizer for Intelligent Routing.
 */
(function() {
    const RouteTimeline = {
        render(containerId, timelineData) {
            const container = document.getElementById(containerId);
            if (!container) return;

            if (!Array.isArray(timelineData) || timelineData.length === 0) {
                container.innerHTML = `
                    <div style="font-size:11px; color:#71717a; text-align:center; padding:12px;">
                        No timeline stages available.
                    </div>
                `;
                return;
            }

            let stagesHtml = "";
            timelineData.forEach((item, idx) => {
                const isLast = idx === timelineData.length - 1;
                // Support both API shape {stage, duration, location} and fallback shape {step, eta, location}
                const stageLabel  = item.stage    || item.step     || `Stage ${idx + 1}`;
                const etaLabel    = item.duration  || item.eta      || "—";
                const locationLabel = item.location || item.hub     || "—";
                stagesHtml += `
                    <div style="display:flex; align-items:flex-start; gap:12px; position:relative; flex:1;">
                        <div style="display:flex; flex-direction:column; align-items:center;">
                            <div style="width:28px; height:28px; border-radius:50%; background:#18181b; border:2px solid #3b82f6; display:flex; align-items:center; justify-content:center; color:#60a5fa; font-size:11px; font-weight:bold; z-index:2;">
                                ${idx + 1}
                            </div>
                            ${!isLast ? `<div style="width:2px; height:100%; min-height:24px; background:linear-gradient(to bottom, #3b82f6, #27272a); margin-top:2px;"></div>` : ''}
                        </div>
                        <div style="display:flex; flex-direction:column; gap:2px; background:rgba(24,24,27,0.6); padding:8px 12px; border-radius:6px; border:1px solid rgba(63,63,70,0.3); flex:1;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <strong style="font-size:12px; color:#f4f4f5;">${stageLabel}</strong>
                                <span class="badge info" style="font-size:9px;">${etaLabel}</span>
                            </div>
                            <span style="font-size:10px; color:#a1a1aa;"><i class="fa-solid fa-location-dot text-primary"></i> ${locationLabel}</span>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = `
                <div class="card glass-panel" style="padding:12px; border-radius:8px;">
                    <h4 style="margin:0 0 10px 0; font-size:12px; color:#f4f4f5;"><i class="fa-solid fa-clock-rotate-left text-primary"></i> Stage-by-Stage Shipment Timeline</h4>
                    <div style="display:flex; flex-direction:column; gap:8px;">
                        ${stagesHtml}
                    </div>
                </div>
            `;
        }
    };

    window.RouteTimeline = RouteTimeline;
})();
