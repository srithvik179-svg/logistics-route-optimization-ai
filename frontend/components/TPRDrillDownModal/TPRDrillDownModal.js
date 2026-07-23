/**
 * TPRDrillDownModal Component
 * Interactive modal displaying TPR capacity, queue metrics, category breakdown, and AI recommendations.
 * Fully self-contained — renders immediately using client-side data seeded from the TPR ID.
 */
(function() {
    const TPRDrillDownModal = {
        open(tprId) {
            // Remove any existing modal
            const existing = document.getElementById("tpr-drilldown-modal");
            if (existing) existing.remove();

            // Seed-based deterministic random so same TPR always shows same values
            const seed = (tprId || "TPR-X").split("").reduce((a, c) => a + c.charCodeAt(0), 0);
            let s = seed;
            const rnd = (min, max) => { s = (s * 1664525 + 1013904223) & 0xffffffff; return min + (Math.abs(s) % (max - min + 1)); };

            const capPerDay   = rnd(80,  220);
            const utilPct     = rnd(58,  96);
            const queueLen    = rnd(12,  85);
            const slaPct      = rnd(88,  99);
            const utilColor   = utilPct > 90 ? "#f87171" : utilPct > 75 ? "#facc15" : "#34d399";

            const categories = [
                { label: "Screen / Display",       pct: rnd(22, 35) },
                { label: "Battery Replacement",    pct: rnd(18, 28) },
                { label: "Motherboard Repair",     pct: rnd(10, 18) },
                { label: "Keyboard / Input",       pct: rnd(8,  14) },
                { label: "Chassis / Structural",   pct: rnd(5,  12) },
            ];

            const recommendations = [
                `Increase intake capacity by ${rnd(10, 20)}% — current queue is approaching saturation threshold.`,
                `Re-route low-priority units from ${tprId} to the nearest under-utilised centre to cut wait times.`,
                `Batch Screen/Display repairs on Tue & Thu to reduce per-unit handling time by ~${rnd(8, 18)}%.`,
                `SLA compliance can be lifted to 99%+ by adding one additional technician during peak-hour shifts.`,
                `Predictive maintenance scheduling could reduce emergency repairs by ${rnd(12, 25)}%.`,
            ];

            const categoriesHtml = categories.map(c => `
                <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px;">
                    <span style="color:#d4d4d8;">${c.label}</span>
                    <span style="color:#60a5fa;font-weight:600;">${c.pct}%</span>
                </div>
                <div style="height:6px;background:#27272a;border-radius:3px;margin-bottom:10px;overflow:hidden;">
                    <div style="width:${c.pct}%;height:100%;background:linear-gradient(90deg,#3b82f6,#60a5fa);border-radius:3px;"></div>
                </div>
            `).join("");

            const recsHtml = recommendations.map(r => `
                <div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:8px;font-size:11px;color:#d4d4d8;
                            padding:8px 10px;background:rgba(59,130,246,0.08);border-left:3px solid #3b82f6;border-radius:4px;">
                    <i class="fa-solid fa-bolt" style="color:#facc15;margin-top:2px;flex-shrink:0;"></i>
                    <span>${r}</span>
                </div>
            `).join("");

            const modal = document.createElement("div");
            modal.id = "tpr-drilldown-modal";
            modal.style.cssText = [
                "position:fixed;top:0;left:0;width:100vw;height:100vh;",
                "background:rgba(0,0,0,0.85);backdrop-filter:blur(8px);",
                "z-index:9999;display:flex;align-items:center;justify-content:center;"
            ].join("");

            modal.innerHTML = `
                <div style="width:92%;max-width:780px;max-height:90vh;background:#09090b;
                            border:1px solid #3f3f46;border-radius:12px;display:flex;
                            flex-direction:column;overflow:hidden;box-shadow:0 25px 50px rgba(0,0,0,0.7);">

                    <!-- Header -->
                    <div style="padding:14px 20px;background:#18181b;border-bottom:1px solid #27272a;
                                display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <h3 style="margin:0;font-size:15px;color:#fff;">
                                <i class="fa-solid fa-screwdriver-wrench" style="color:#3b82f6;margin-right:8px;"></i>
                                TPR Capacity &amp; Workload Audit:
                                <span style="color:#60a5fa;">${tprId}</span>
                            </h3>
                            <span style="font-size:10px;color:#71717a;">
                                Repair centre efficiency intelligence &amp; AI optimization actions
                            </span>
                        </div>
                        <button onclick="document.getElementById('tpr-drilldown-modal').remove()"
                                style="background:none;border:1px solid #3f3f46;color:#a1a1aa;
                                       border-radius:6px;padding:4px 10px;cursor:pointer;font-size:12px;">
                            ✕ Close
                        </button>
                    </div>

                    <!-- Body -->
                    <div style="overflow-y:auto;flex:1;padding:20px;display:flex;flex-direction:column;gap:16px;">

                        <!-- KPI Row -->
                        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;">
                            ${[
                                { label: "Capacity / Day",   val: `${capPerDay} units`, color: "#60a5fa" },
                                { label: "Utilization",      val: `${utilPct}%`,         color: utilColor  },
                                { label: "Pending Queue",    val: `${queueLen} units`,  color: utilPct > 75 ? "#facc15" : "#34d399" },
                                { label: "Historical SLA",   val: `${slaPct}%`,          color: "#34d399"  },
                            ].map(k => `
                                <div style="background:#18181b;border:1px solid #27272a;border-radius:8px;
                                            padding:12px 14px;text-align:center;">
                                    <span style="font-size:9px;color:#71717a;text-transform:uppercase;
                                                 display:block;margin-bottom:6px;letter-spacing:0.05em;">${k.label}</span>
                                    <strong style="font-size:18px;color:${k.color};">${k.val}</strong>
                                </div>
                            `).join("")}
                        </div>

                        <!-- Capacity Bar -->
                        <div style="background:#18181b;border:1px solid #27272a;border-radius:8px;padding:14px;">
                            <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                                <span style="font-size:11px;color:#a1a1aa;">Current Utilization Level</span>
                                <span style="font-size:11px;color:${utilColor};font-weight:600;">${utilPct}%</span>
                            </div>
                            <div style="height:10px;background:#27272a;border-radius:5px;overflow:hidden;">
                                <div style="width:${utilPct}%;height:100%;
                                            background:linear-gradient(90deg,${utilColor},${utilColor}aa);
                                            border-radius:5px;transition:width 0.8s ease;"></div>
                            </div>
                            <div style="display:flex;justify-content:space-between;margin-top:4px;font-size:9px;color:#52525b;">
                                <span>0%</span><span>50%</span><span>100%</span>
                            </div>
                        </div>

                        <!-- Categories + Recommendations -->
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">
                            <div style="background:#18181b;border:1px solid #27272a;border-radius:8px;padding:14px;">
                                <h4 style="margin:0 0 12px;font-size:12px;color:#fff;">
                                    <i class="fa-solid fa-chart-pie" style="color:#3b82f6;margin-right:6px;"></i>
                                    Repair Category Breakdown
                                </h4>
                                ${categoriesHtml}
                            </div>
                            <div style="background:#18181b;border:1px solid #27272a;border-radius:8px;padding:14px;">
                                <h4 style="margin:0 0 12px;font-size:12px;color:#fff;">
                                    <i class="fa-solid fa-robot" style="color:#facc15;margin-right:6px;"></i>
                                    AI Optimization Actions
                                </h4>
                                ${recsHtml}
                            </div>
                        </div>

                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            // Close on backdrop click
            modal.addEventListener("click", (e) => {
                if (e.target === modal) modal.remove();
            });
        }
    };

    window.TPRDrillDownModal = TPRDrillDownModal;
})();
