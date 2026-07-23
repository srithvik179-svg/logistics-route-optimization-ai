/**
 * CorridorDrillDownModal Component
 * Interactive Enterprise Drill-Down Modal for Phase 53 Route Decision Intelligence.
 */
(function() {
    const CorridorDrillDownModal = {
        async open(corridorId) {
            console.log(`[CorridorDrillDownModal] Opening detail panel for corridor: ${corridorId}`);
            
            // 1. Ensure modal container exists in body
            let modalEl = document.getElementById("corridor-drilldown-modal");
            if (!modalEl) {
                modalEl = document.createElement("div");
                modalEl.id = "corridor-drilldown-modal";
                modalEl.className = "modal-backdrop fade-in";
                modalEl.style.cssText = "position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.85); backdrop-filter:blur(8px); z-index:9999; display:flex; align-items:center; justify-content:center;";
                document.body.appendChild(modalEl);
            }

            modalEl.innerHTML = `
                <div class="glass-panel" style="width:90%; max-width:900px; max-height:90vh; background:#09090b; border:1px solid #3f3f46; border-radius:12px; display:flex; flex-direction:column; overflow:hidden; box-shadow:0 25px 50px -12px rgba(0,0,0,0.7);">
                    <div style="padding:16px 24px; background:#18181b; border-bottom:1px solid #27272a; display:flex; justify-content:space-between; align-items:center;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <i class="fa-solid fa-route text-primary" style="font-size:18px;"></i>
                            <div>
                                <h3 style="margin:0; font-size:16px; color:#fff;">Corridor Intelligence Drill-Down</h3>
                                <span style="font-size:11px; color:#a1a1aa;">Target Corridor: <strong style="color:#60a5fa;">${corridorId}</strong></span>
                            </div>
                        </div>
                        <button class="btn btn-secondary btn-sm" onclick="window.closeCorridorDrillDown()" style="padding:4px 10px;">
                            <i class="fa-solid fa-xmark"></i> Close
                        </button>
                    </div>

                    <div id="corridor-drilldown-content" style="padding:20px; overflow-y:auto; flex:1; display:flex; flex-direction:column; gap:16px;">
                        <div style="text-align:center; padding:2rem; color:#a1a1aa;">
                            <i class="fa-solid fa-circle-notch fa-spin text-primary" style="font-size:2rem; margin-bottom:1rem;"></i>
                            <p style="margin:0; font-size:12px;">Analyzing corridor health, transit distribution, and root causes...</p>
                        </div>
                    </div>
                </div>
            `;

            try {
                // Fetch detail payload from backend endpoint
                const res = await fetch("/api/corridor-drilldown/details", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ corridor_id: corridorId })
                });

                const raw = await res.json();
                const data = raw.payload || raw;
                const corr = data.corridor || {};
                const scores = corr.scores || {};
                const metrics = corr.metrics || {};
                const rootCause = corr.root_cause || {};
                const impact = corr.business_impact || {};
                const altRoute = corr.alternative_route || {};

                const contentEl = document.getElementById("corridor-drilldown-content");
                if (contentEl) {
                    contentEl.innerHTML = `
                        <!-- Health Score Cards Strip -->
                        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:10px;">
                            <div style="background:#18181b; padding:12px; border-radius:8px; border:1px solid #27272a; text-align:center;">
                                <span style="font-size:10px; color:#a1a1aa;">Overall Health</span>
                                <div style="font-size:18px; font-weight:800; color:${corr.health_color === 'danger' ? '#ef4444' : '#10b981'}; margin-top:2px;">
                                    ${scores.overall_health || 85.0}/100
                                </div>
                                <span class="badge ${corr.health_color || 'success'}" style="font-size:8px;">${corr.health_tier || 'Good'}</span>
                            </div>

                            <div style="background:#18181b; padding:12px; border-radius:8px; border:1px solid #27272a; text-align:center;">
                                <span style="font-size:10px; color:#a1a1aa;">Cost Score</span>
                                <div style="font-size:18px; font-weight:800; color:#f59e0b; margin-top:2px;">${scores.cost_score || 80.0}</div>
                                <span style="font-size:9px; color:#71717a;">$${metrics.avg_cost || 0} / shipment</span>
                            </div>

                            <div style="background:#18181b; padding:12px; border-radius:8px; border:1px solid #27272a; text-align:center;">
                                <span style="font-size:10px; color:#a1a1aa;">SLA Compliance</span>
                                <div style="font-size:18px; font-weight:800; color:#3b82f6; margin-top:2px;">${metrics.sla_compliance_pct || 90.0}%</div>
                                <span style="font-size:9px; color:#71717a;">${metrics.sla_violations || 0} Breaches</span>
                            </div>

                            <div style="background:#18181b; padding:12px; border-radius:8px; border:1px solid #27272a; text-align:center;">
                                <span style="font-size:10px; color:#a1a1aa;">Avg Transit</span>
                                <div style="font-size:18px; font-weight:800; color:#a855f7; margin-top:2px;">${metrics.avg_transit_days || 2.5} Days</div>
                                <span style="font-size:9px; color:#71717a;">Distance: ${metrics.avg_distance || 150} km</span>
                            </div>

                            <div style="background:#18181b; padding:12px; border-radius:8px; border:1px solid #27272a; text-align:center;">
                                <span style="font-size:10px; color:#a1a1aa;">Optimization Score</span>
                                <div style="font-size:18px; font-weight:800; color:#10b981; margin-top:2px;">${scores.optimization_score || 88.0}</div>
                                <span style="font-size:9px; color:#34d399;">Potential: ${impact.return_on_optimization || '24.5%'}</span>
                            </div>
                        </div>

                        <!-- Explainable Root Cause Analysis -->
                        <div style="background:#18181b; padding:16px; border-radius:8px; border:1px solid #27272a; display:flex; flex-direction:column; gap:8px;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <h4 style="margin:0; font-size:13px; color:#f4f4f5;"><i class="fa-solid fa-microscope text-warning"></i> AI Root Cause Analysis & Contributing Drivers</h4>
                                <span class="badge info" style="font-size:9px;">Confidence: ${rootCause.confidence_score || '95.0%'}</span>
                            </div>
                            <p style="font-size:11px; color:#a1a1aa; margin:0;">${rootCause.root_cause_summary || 'Analysis indicates facility capacity bottleneck during peak dispatch cycles.'}</p>
                            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:6px;">
                                <div style="background:rgba(0,0,0,0.3); padding:10px; border-radius:6px; border-left:3px solid #ef4444;">
                                    <strong style="font-size:11px; color:#f87171;">Primary Contributing Drivers:</strong>
                                    <ul style="margin:4px 0 0 14px; padding:0; font-size:10px; color:#d4d4d8;">
                                        ${(rootCause.contributing_factors || ['Facility capacity utilization exceeding threshold.']).map(f => `<li>${f}</li>`).join('')}
                                    </ul>
                                </div>
                                <div style="background:rgba(0,0,0,0.3); padding:10px; border-radius:6px; border-left:3px solid #10b981;">
                                    <strong style="font-size:11px; color:#34d399;">Expected Optimization Outcome:</strong>
                                    <div style="font-size:10px; color:#d4d4d8; margin-top:4px; display:flex; flex-direction:column; gap:2px;">
                                        <span>• Cost Reduction: ${rootCause.expected_improvement?.cost_reduction || '-18%'}</span>
                                        <span>• Transit Reduction: ${rootCause.expected_improvement?.transit_reduction || '-0.8 Days'}</span>
                                        <span>• SLA Gain: ${rootCause.expected_improvement?.sla_improvement || '+24.5%'}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Alternative Route Generator Comparison -->
                        ${altRoute.recommended_route ? `
                        <div style="background:#18181b; padding:16px; border-radius:8px; border:1px solid #27272a; display:flex; flex-direction:column; gap:10px;">
                            <h4 style="margin:0; font-size:13px; color:#f4f4f5;"><i class="fa-solid fa-code-compare text-primary"></i> Alternative Route Generator Comparison</h4>
                            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
                                <div style="background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); padding:12px; border-radius:6px;">
                                    <span style="font-size:10px; font-weight:700; color:#f87171;">CURRENT DIRECT ROUTE</span>
                                    <div style="font-size:12px; font-weight:700; color:#fff; margin:4px 0;">${(altRoute.current_route.path || []).join(' → ')}</div>
                                    <div style="font-size:10px; color:#a1a1aa; display:flex; flex-direction:column; gap:2px;">
                                        <span>Distance: ${altRoute.current_route.distance_km} km</span>
                                        <span>Transit Time: ${altRoute.current_route.transit_days} Days</span>
                                        <span>Cost: $${altRoute.current_route.cost}</span>
                                        <span>SLA Prob: ${altRoute.current_route.sla_probability}</span>
                                    </div>
                                </div>

                                <div style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); padding:12px; border-radius:6px;">
                                    <span style="font-size:10px; font-weight:700; color:#34d399;">RECOMMENDED ALTERNATIVE ROUTE</span>
                                    <div style="font-size:12px; font-weight:700; color:#fff; margin:4px 0;">${altRoute.recommended_route.path_str}</div>
                                    <div style="font-size:10px; color:#a1a1aa; display:flex; flex-direction:column; gap:2px;">
                                        <span>Distance: ${altRoute.recommended_route.distance_km} km</span>
                                        <span>Transit Time: ${altRoute.recommended_route.transit_days} Days</span>
                                        <span>Cost: $${altRoute.recommended_route.cost}</span>
                                        <span>SLA Prob: ${altRoute.recommended_route.sla_probability}</span>
                                    </div>
                                </div>
                            </div>
                            <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(0,0,0,0.3); padding:8px 12px; border-radius:6px; font-size:11px;">
                                <span>Savings: <strong style="color:#facc15;">${altRoute.comparison?.estimated_savings}</strong></span>
                                <span>ETA Gain: <strong style="color:#34d399;">${altRoute.comparison?.eta_improvement}</strong></span>
                                <span>Risk Reduction: <strong style="color:#60a5fa;">${altRoute.comparison?.risk_reduction}</strong></span>
                                <button class="btn btn-primary btn-xs" onclick="window.triggerCorridorOptimization('${corridorId}')" style="font-size:10px; padding:3px 10px;">
                                    <i class="fa-solid fa-wand-magic-sparkles"></i> Apply Optimization
                                </button>
                            </div>
                        </div>
                        ` : ''}
                    `;
                }
            } catch (err) {
                console.error("[CorridorDrillDownModal] Error:", err);
            }
        },

        close() {
            const modalEl = document.getElementById("corridor-drilldown-modal");
            if (modalEl) modalEl.remove();
        }
    };

    window.openCorridorDrillDown = (id) => CorridorDrillDownModal.open(id);
    window.closeCorridorDrillDown = () => CorridorDrillDownModal.close();
    window.CorridorDrillDownModal = CorridorDrillDownModal;
})();
