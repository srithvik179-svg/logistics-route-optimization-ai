/**
 * Executive Command Center & Reporting Suite
 * Phase 34 — Dell FutureMinds Hackathon
 *
 * All data is fetched exclusively through the Enterprise API Gateway.
 * No direct repository access. No backend modifications.
 */

// =========================================================
// STATE & CACHE
// =========================================================

/** Active executive filter state */
const execFilters = {
    date_range: "all",
    region: "",
    partner: "",
    algorithm: "astar"
};

/** Response cache to avoid redundant API calls within the same session */
const execDataCache = new Map();

/** Cache TTL in milliseconds (5 minutes) */
const EXEC_CACHE_TTL = 5 * 60 * 1000;

/** Track which tabs have been loaded */
const execTabsLoaded = new Set();

// =========================================================
// ENTRY POINT
// =========================================================

/**
 * Main entry point: load the Executive Command Center.
 * Called by app.js navigation handler when #executive-section is activated.
 */
async function loadExecutiveCommandCenter() {
    console.log("[Observability] Executive Dashboard Loaded");
    execTabsLoaded.clear();
    execDataCache.clear();

    // Load the active tab (overview by default)
    await loadExecOverview();
    execTabsLoaded.add("exec-overview");

    console.log("[Observability] KPIs Refreshed");
}

// =========================================================
// TAB SWITCHING
// =========================================================

/**
 * Switches the active executive tab and lazily loads its data.
 * @param {string} tabId - The tab pane element ID to activate.
 * @param {HTMLElement} btn - The tab button that was clicked.
 */
async function switchExecTab(tabId, btn) {
    // Update tab button states
    document.querySelectorAll(".exec-tab").forEach(t => t.classList.remove("active"));
    btn.classList.add("active");

    // Update tab pane visibility
    document.querySelectorAll(".exec-tab-pane").forEach(p => p.classList.remove("active"));
    const pane = document.getElementById(tabId);
    if (pane) pane.classList.add("active");

    // Lazy-load: only call the loader if not already loaded
    if (!execTabsLoaded.has(tabId)) {
        execTabsLoaded.add(tabId);
        switch (tabId) {
            case "exec-overview":     await loadExecOverview(); break;
            case "exec-business":     await loadExecBusinessPerformance(); break;
            case "exec-financial":    await loadExecFinancial(); break;
            case "exec-operations":   await loadExecOperations(); break;
            case "exec-network":      await loadExecNetworkPerformance(); break;
            case "exec-optimization": await loadExecOptimization(); break;
            case "exec-regional":     await loadExecRegionalInsights(); break;
            case "exec-strategic":    await loadExecStrategicKPIs(); break;
        }
    }
}

// =========================================================
// FILTER MANAGEMENT
// =========================================================

/**
 * Reads filter controls and re-loads the current tab with updated filters.
 */
async function applyExecFilters() {
    execFilters.date_range = document.getElementById("exec-filter-date")?.value || "all";
    execFilters.region     = document.getElementById("exec-filter-region")?.value || "";
    execFilters.partner    = document.getElementById("exec-filter-partner")?.value || "";
    execFilters.algorithm  = document.getElementById("exec-filter-algo")?.value || "astar";

    // Invalidate cache so all panels reload with new filters
    execDataCache.clear();
    execTabsLoaded.clear();

    console.log("[Observability] KPIs Refreshed", execFilters);

    // Re-load the currently visible tab
    const activeBtn = document.querySelector(".exec-tab.active");
    const activeTabId = activeBtn ? activeBtn.getAttribute("data-tab") : "exec-overview";
    execTabsLoaded.add(activeTabId);

    switch (activeTabId) {
        case "exec-overview":     await loadExecOverview(); break;
        case "exec-business":     await loadExecBusinessPerformance(); break;
        case "exec-financial":    await loadExecFinancial(); break;
        case "exec-operations":   await loadExecOperations(); break;
        case "exec-network":      await loadExecNetworkPerformance(); break;
        case "exec-optimization": await loadExecOptimization(); break;
        case "exec-regional":     await loadExecRegionalInsights(); break;
        case "exec-strategic":    await loadExecStrategicKPIs(); break;
    }
}

// =========================================================
// CACHED API FETCH HELPER
// =========================================================

/**
 * Fetches data from a POST endpoint with caching.
 * @param {string} url - API endpoint URL.
 * @param {object} body - Request payload.
 * @returns {Promise<object>} - JSON response (unwrapped by API gateway).
 */
async function execFetchPost(url, body = {}) {
    const cacheKey = url + JSON.stringify(body);
    const cached = execDataCache.get(cacheKey);
    if (cached && (Date.now() - cached.ts < EXEC_CACHE_TTL)) {
        return cached.data;
    }
    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error(`API error ${res.status} from ${url}`);
    const data = await res.json();
    execDataCache.set(cacheKey, { data, ts: Date.now() });
    return data;
}

/**
 * Fetches data from a GET endpoint with caching.
 * @param {string} url - API endpoint URL.
 * @returns {Promise<object>} - JSON response.
 */
async function execFetchGet(url) {
    const cached = execDataCache.get(url);
    if (cached && (Date.now() - cached.ts < EXEC_CACHE_TTL)) {
        return cached.data;
    }
    const res = await fetch(url);
    if (!res.ok) throw new Error(`API error ${res.status} from ${url}`);
    const data = await res.json();
    execDataCache.set(url, { data, ts: Date.now() });
    return data;
}

// =========================================================
// HELPER: Build API filter payload
// =========================================================
function buildExecPayload(extra = {}) {
    const filters = {};
    if (execFilters.region) filters.region = execFilters.region;
    if (execFilters.partner) filters.partner = execFilters.partner;
    return { filters, ...extra };
}

// =========================================================
// TAB 1: EXECUTIVE OVERVIEW
// =========================================================
async function loadExecOverview() {
    try {
        const [dashData, slaData, healthData, scoringData] = await Promise.allSettled([
            execFetchGet("/api/analytics/dashboard"),
            execFetchPost("/api/sla-analytics/payload", buildExecPayload()),
            execFetchGet("/api/v1/monitoring/health"),
            execFetchPost("/api/route-scoring/payload", buildExecPayload())
        ]);

        // --- KPI Command Strip ---
        if (dashData.status === "fulfilled") {
            const d = dashData.value;
            setText("ekpi-shipments-val", fmtNum(d.total_shipments ?? d.kpis?.total_shipments));
            setText("ekpi-transit-val", fmtDays(d.avg_transit_days ?? d.kpis?.avg_transit_days));
            setText("ekpi-cost-val", fmtCurrency(d.total_cost ?? d.kpis?.total_cost));
            setText("ekpi-ontime-val", fmtPct(d.on_time_delivery_rate ?? d.kpis?.on_time_delivery_rate));
        }

        if (slaData.status === "fulfilled") {
            const s = slaData.value;
            const overview = s.overview ?? s;
            setText("ekpi-sla-val", fmtPct(overview.compliance_rate ?? overview.sla_compliance_rate));
            setText("ekpi-violations-val", fmtNum(overview.total_violations ?? overview.violations_count));

            // Executive alert bar
            const violations = overview.total_violations ?? overview.violations_count ?? 0;
            if (violations > 0) {
                showExecAlert(`⚠ ${violations} SLA violation(s) detected. Immediate review recommended.`);
            }

            // SLA delta indicators
            setDelta("ekpi-sla-delta", overview.compliance_rate ?? 0, 90, true);
            setDelta("ekpi-violations-delta", violations, 0, false);
        }

        // --- Platform Health Table ---
        if (healthData.status === "fulfilled") {
            const h = healthData.value;
            const tbody = document.getElementById("exec-health-table");
            if (tbody && h.services) {
                tbody.innerHTML = h.services.map(svc => {
                    const isUp = svc.status === "UP" || svc.status === "HEALTHY";
                    return `<tr>
                        <td><strong>${svc.name}</strong></td>
                        <td><span class="badge ${isUp ? 'success' : 'danger'}">${svc.status}</span></td>
                        <td>${fmtMs(svc.response_time_ms)}</td>
                    </tr>`;
                }).join("");
            }
        }

        // --- Business Summary ---
        if (dashData.status === "fulfilled") {
            const d = dashData.value;
            const summaryEl = document.getElementById("exec-business-summary");
            if (summaryEl) {
                summaryEl.innerHTML = `
                    <div class="exec-stat-row"><span>Total Shipments</span><strong>${fmtNum(d.total_shipments ?? d.kpis?.total_shipments)}</strong></div>
                    <div class="exec-stat-row"><span>Total Logistics Cost</span><strong>${fmtCurrency(d.total_cost ?? d.kpis?.total_cost)}</strong></div>
                    <div class="exec-stat-row"><span>Avg Transit Time</span><strong>${fmtDays(d.avg_transit_days ?? d.kpis?.avg_transit_days)}</strong></div>
                    <div class="exec-stat-row"><span>On-Time Delivery Rate</span><strong>${fmtPct(d.on_time_delivery_rate ?? d.kpis?.on_time_delivery_rate)}</strong></div>
                    <div class="exec-stat-row"><span>Active Hubs</span><strong>${fmtNum(d.active_hubs ?? d.kpis?.active_hubs)}</strong></div>
                    <div class="exec-stat-row"><span>Active Routes</span><strong>${fmtNum(d.active_routes ?? d.kpis?.active_routes)}</strong></div>
                `;
            }
        }

        // --- Top & Bottom Route Rankings ---
        if (scoringData.status === "fulfilled") {
            const s = scoringData.value;
            const rankings = s.rankings ?? s.route_rankings ?? [];
            renderTopBottomRoutes(rankings);
        }

        console.log("[Observability] Business Summary Updated");
    } catch (err) {
        console.error("[ExecDashboard] loadExecOverview error:", err);
    }
}

function renderTopBottomRoutes(rankings) {
    const sorted = [...rankings].sort((a, b) =>
        (b.overall_score ?? b.score ?? 0) - (a.overall_score ?? a.score ?? 0)
    );
    const top = sorted.slice(0, 5);
    const bottom = sorted.slice(-5).reverse();

    const topTbody = document.getElementById("exec-top-routes");
    const botTbody = document.getElementById("exec-bottom-routes");

    if (topTbody) {
        topTbody.innerHTML = top.length === 0
            ? `<tr><td colspan="4" class="text-center text-muted">No data available</td></tr>`
            : top.map((r, i) => `<tr>
                <td><span class="exec-rank-badge">#${i+1}</span> ${r.route ?? r.route_id ?? "—"}</td>
                <td><strong>${fmtScore(r.overall_score ?? r.score)}</strong></td>
                <td>${fmtPct(r.sla_score ?? r.sla_compliance)}</td>
                <td>${fmtCurrency(r.total_cost ?? r.cost)}</td>
            </tr>`).join("");
    }

    if (botTbody) {
        botTbody.innerHTML = bottom.length === 0
            ? `<tr><td colspan="4" class="text-center text-muted">No data available</td></tr>`
            : bottom.map((r, i) => `<tr>
                <td><span class="exec-rank-badge danger">#${sorted.length - i}</span> ${r.route ?? r.route_id ?? "—"}</td>
                <td><strong>${fmtScore(r.overall_score ?? r.score)}</strong></td>
                <td>${fmtDays(r.avg_delay_days ?? r.delay)}</td>
                <td>${fmtCurrency(r.total_cost ?? r.cost)}</td>
            </tr>`).join("");
    }
}

// =========================================================
// TAB 2: BUSINESS PERFORMANCE
// =========================================================
async function loadExecBusinessPerformance() {
    try {
        const [biData, perfData] = await Promise.allSettled([
            execFetchPost("/api/bi/dashboard", buildExecPayload()),
            execFetchPost("/api/performance/payload", buildExecPayload())
        ]);

        // --- Scorecard Grid ---
        const grid = document.getElementById("exec-scorecard-grid");
        if (grid && biData.status === "fulfilled") {
            const d = biData.value;
            const kpis = d.kpis ?? d;
            grid.innerHTML = [
                { label: "Total Shipments", value: fmtNum(kpis.total_shipments), icon: "fa-boxes-stacked", color: "blue" },
                { label: "On-Time Rate", value: fmtPct(kpis.on_time_delivery_rate ?? kpis.on_time_rate), icon: "fa-truck-fast", color: "green" },
                { label: "Avg Transit Time", value: fmtDays(kpis.avg_transit_days), icon: "fa-clock", color: "orange" },
                { label: "SLA Compliance", value: fmtPct(kpis.sla_compliance_rate ?? kpis.sla_rate), icon: "fa-shield-halved", color: "green" },
                { label: "Total Cost", value: fmtCurrency(kpis.total_cost), icon: "fa-coins", color: "orange" },
                { label: "Avg Cost/Shipment", value: fmtCurrency(kpis.avg_cost_per_shipment ?? kpis.avg_cost), icon: "fa-receipt", color: "blue" },
            ].map(s => `
                <div class="exec-scorecard accent-${s.color}">
                    <div class="exec-scorecard-icon"><i class="fa-solid ${s.icon}"></i></div>
                    <div class="exec-scorecard-body">
                        <span class="exec-scorecard-label">${s.label}</span>
                        <span class="exec-scorecard-value">${s.value}</span>
                    </div>
                </div>
            `).join("");
        }

        // --- Hub Performance Table ---
        if (perfData.status === "fulfilled") {
            const d = perfData.value;
            const hubs = d.hub_scorecards ?? d.node_scorecards ?? d.scorecards ?? [];
            const tbody = document.getElementById("exec-hub-perf-table");
            if (tbody) {
                tbody.innerHTML = hubs.length === 0
                    ? `<tr><td colspan="5" class="text-center text-muted">No hub data available</td></tr>`
                    : hubs.slice(0, 10).map(h => `<tr>
                        <td><strong>${h.hub ?? h.node ?? h.name ?? "—"}</strong></td>
                        <td>${fmtNum(h.shipments ?? h.total_shipments)}</td>
                        <td>${fmtPct(h.on_time_rate ?? h.on_time_delivery_rate)}</td>
                        <td>${fmtPct(h.sla_compliance ?? h.sla_rate)}</td>
                        <td>${fmtCurrency(h.avg_cost)}</td>
                    </tr>`).join("");
            }
        }

        // --- Mode Performance Table ---
        if (biData.status === "fulfilled") {
            const d = biData.value;
            const modes = d.transport_breakdown ?? d.mode_breakdown ?? d.distributions?.transport_mode ?? [];
            const tbody = document.getElementById("exec-mode-perf-table");
            if (tbody) {
                const modeArr = Array.isArray(modes) ? modes : Object.entries(modes).map(([k, v]) => ({ mode: k, ...v }));
                tbody.innerHTML = modeArr.length === 0
                    ? `<tr><td colspan="5" class="text-center text-muted">No mode data available</td></tr>`
                    : modeArr.map(m => `<tr>
                        <td><strong>${m.mode ?? m.name ?? "—"}</strong></td>
                        <td>${fmtNum(m.count ?? m.shipments)}</td>
                        <td>${fmtDays(m.avg_transit_days ?? m.avg_transit)}</td>
                        <td>${fmtCurrency(m.total_cost)}</td>
                        <td>${fmtPct(m.sla_compliance ?? m.sla_rate)}</td>
                    </tr>`).join("");
            }
        }

        console.log("[Observability] Reports Generated");
    } catch (err) {
        console.error("[ExecDashboard] loadExecBusinessPerformance error:", err);
    }
}

// =========================================================
// TAB 3: FINANCIAL OVERVIEW
// =========================================================
async function loadExecFinancial() {
    try {
        const data = await execFetchPost("/api/cost-analytics/payload", buildExecPayload());
        const overview = data.overview ?? data;

        // KPI Strip
        setText("fcost-total", fmtCurrency(overview.total_cost));
        setText("fcost-avg", fmtCurrency(overview.avg_cost_per_shipment ?? overview.avg_cost));
        setText("fcost-variance", fmtCurrency(overview.cost_std_dev ?? overview.cost_variance));
        setText("fcost-min-route", overview.min_cost_route ?? overview.cheapest_route ?? "—");

        // Cost Rankings Table
        const rankings = data.rankings ?? data.cost_rankings ?? [];
        const tbody = document.getElementById("exec-cost-rankings");
        if (tbody) {
            tbody.innerHTML = rankings.length === 0
                ? `<tr><td colspan="5" class="text-center text-muted">No ranking data available</td></tr>`
                : rankings.slice(0, 10).map((r, i) => `<tr>
                    <td><span class="exec-rank-badge">#${i+1}</span></td>
                    <td><strong>${r.route ?? r.route_id ?? "—"}</strong></td>
                    <td>${fmtCurrency(r.total_cost)}</td>
                    <td>${fmtCurrency(r.avg_cost)}</td>
                    <td>${fmtNum(r.shipments ?? r.count)}</td>
                </tr>`).join("");
        }

        // Cost Trend Chart
        const trends = data.trends ?? data.cost_trends ?? [];
        if (trends.length > 0 && typeof Plotly !== "undefined") {
            const labels = trends.map(t => t.period ?? t.date ?? t.month ?? "");
            const values = trends.map(t => t.total_cost ?? t.avg_cost ?? t.cost ?? 0);
            Plotly.react("exec-cost-trend-chart", [{
                x: labels, y: values, type: "scatter", mode: "lines+markers",
                line: { color: "#f59e0b", width: 2.5 },
                marker: { color: "#f59e0b", size: 7 },
                fill: "tozeroy", fillcolor: "rgba(245,158,11,0.1)"
            }], {
                paper_bgcolor: "transparent", plot_bgcolor: "transparent",
                font: { color: "#9ca3af", size: 11 },
                margin: { t: 10, r: 10, b: 40, l: 50 },
                xaxis: { gridcolor: "rgba(255,255,255,0.05)" },
                yaxis: { gridcolor: "rgba(255,255,255,0.05)", tickprefix: "₹" }
            }, { responsive: true, displayModeBar: false });
        }

        console.log("[Observability] Reports Generated");
    } catch (err) {
        console.error("[ExecDashboard] loadExecFinancial error:", err);
    }
}

// =========================================================
// TAB 4: OPERATIONS SUMMARY
// =========================================================
async function loadExecOperations() {
    try {
        const [transitData, inventoryData, slaData] = await Promise.allSettled([
            execFetchPost("/api/transit-analytics/payload", buildExecPayload()),
            execFetchPost("/api/inventory-analytics/payload", buildExecPayload()),
            execFetchPost("/api/sla-analytics/payload", buildExecPayload())
        ]);

        // Transit Performance
        if (transitData.status === "fulfilled") {
            const t = transitData.value;
            const ov = t.overview ?? t.transit_overview ?? t;
            setText("ops-transit-avg", fmtDays(ov.avg_transit_days ?? ov.avg_days));
            setText("ops-transit-min", fmtDays(ov.min_transit_days ?? ov.fastest_days));
            setText("ops-transit-max", fmtDays(ov.max_transit_days ?? ov.slowest_days));
            setText("ops-ontime-rate", fmtPct(ov.on_time_rate ?? ov.on_time_delivery_rate));
            setText("ops-total-shipments", fmtNum(ov.total_shipments ?? ov.count));
        }

        // Inventory Health
        if (inventoryData.status === "fulfilled") {
            const inv = inventoryData.value;
            const ov = inv.overview ?? inv.inventory_overview ?? inv;
            setText("ops-inv-skus", fmtNum(ov.total_skus ?? ov.unique_parts));
            setText("ops-inv-stock", fmtNum(ov.avg_stock_level ?? ov.avg_quantity));
            setText("ops-inv-turnover", (ov.turnover_rate ?? ov.inventory_turnover ?? "—").toString());
            setText("ops-inv-fulfillment", fmtPct(ov.fulfillment_rate));
            setText("ops-inv-outliers", fmtNum((inv.outliers ?? []).length));
        }

        // SLA Compliance
        if (slaData.status === "fulfilled") {
            const s = slaData.value;
            const ov = s.overview ?? s;
            setText("ops-sla-rate", fmtPct(ov.compliance_rate ?? ov.sla_compliance_rate));
            setText("ops-sla-total", fmtNum(ov.total_records ?? ov.total_checks));
            setText("ops-sla-violations", fmtNum(ov.total_violations ?? ov.violations_count));
            setText("ops-sla-critical", fmtNum(ov.critical_violations ?? ov.severe_violations));
            setText("ops-sla-best", ov.best_hub ?? ov.best_performing_hub ?? "—");

            // SLA Violations Table
            const violations = s.violations ?? s.sla_violations ?? [];
            const tbody = document.getElementById("exec-sla-violations-table");
            if (tbody) {
                tbody.innerHTML = violations.length === 0
                    ? `<tr><td colspan="5" class="text-center text-muted" style="padding:1rem;">No violations detected ✓</td></tr>`
                    : violations.slice(0, 15).map(v => {
                        const sev = v.severity ?? "MEDIUM";
                        const sevClass = sev === "HIGH" || sev === "CRITICAL" ? "danger" : sev === "LOW" ? "" : "warning";
                        return `<tr>
                            <td><strong>${v.route ?? v.route_id ?? "—"}</strong></td>
                            <td>${fmtDays(v.expected_days ?? v.sla_days)}</td>
                            <td>${fmtDays(v.actual_days ?? v.transit_days)}</td>
                            <td class="text-danger">${fmtDays(v.delay_days ?? v.delay)}</td>
                            <td><span class="badge ${sevClass}">${sev}</span></td>
                        </tr>`;
                    }).join("");
            }
        }

        console.log("[Observability] Business Summary Updated");
    } catch (err) {
        console.error("[ExecDashboard] loadExecOperations error:", err);
    }
}

// =========================================================
// TAB 5: NETWORK PERFORMANCE
// =========================================================
async function loadExecNetworkPerformance() {
    try {
        const [capacityData, scoringData] = await Promise.allSettled([
            execFetchPost("/api/capacity-analytics/payload", buildExecPayload()),
            execFetchPost("/api/route-scoring/payload", buildExecPayload())
        ]);

        // Network KPI Strip
        if (capacityData.status === "fulfilled") {
            const c = capacityData.value;
            const ov = c.overview ?? c;
            setText("net-nodes", fmtNum(ov.total_nodes ?? ov.total_hubs_rcs));
            setText("net-edges", fmtNum(ov.total_routes ?? ov.active_routes));
            setText("net-util", fmtPct(ov.avg_utilization_rate ?? ov.avg_utilization));

            const bottlenecks = c.bottlenecks ?? [];
            setText("net-bottlenecks", fmtNum(bottlenecks.length));

            // Bottleneck Table
            const tbody = document.getElementById("exec-bottleneck-table");
            if (tbody) {
                tbody.innerHTML = bottlenecks.length === 0
                    ? `<tr><td colspan="3" class="text-center text-muted">No critical bottlenecks detected</td></tr>`
                    : bottlenecks.slice(0, 10).map(b => {
                        const util = b.utilization_rate ?? b.utilization ?? 0;
                        const sev = util > 90 ? "danger" : util > 70 ? "warning" : "";
                        return `<tr>
                            <td><strong>${b.hub ?? b.name ?? b.node ?? "—"}</strong></td>
                            <td>
                                <div class="exec-progress-bar-wrap">
                                    <div class="exec-progress-bar ${sev}" style="width:${Math.min(util,100)}%"></div>
                                </div>
                                ${util.toFixed(1)}%
                            </td>
                            <td><span class="badge ${sev}">${sev === "danger" ? "CRITICAL" : sev === "warning" ? "HIGH" : "NORMAL"}</span></td>
                        </tr>`;
                    }).join("");
            }
        }

        // Route Score Rankings
        if (scoringData.status === "fulfilled") {
            const s = scoringData.value;
            const rankings = s.rankings ?? s.route_rankings ?? [];
            const tbody = document.getElementById("exec-route-scores");
            if (tbody) {
                tbody.innerHTML = rankings.length === 0
                    ? `<tr><td colspan="4" class="text-center text-muted">No routing data available</td></tr>`
                    : rankings.slice(0, 10).map((r, i) => {
                        const score = r.overall_score ?? r.score ?? 0;
                        const grade = score >= 80 ? "A" : score >= 65 ? "B" : score >= 50 ? "C" : "D";
                        const gradeClass = grade === "A" ? "success" : grade === "B" ? "" : grade === "C" ? "warning" : "danger";
                        return `<tr>
                            <td><span class="exec-rank-badge">#${i+1}</span></td>
                            <td><strong>${r.route ?? r.route_id ?? "—"}</strong></td>
                            <td>${fmtScore(score)}</td>
                            <td><span class="badge ${gradeClass}">${grade}</span></td>
                        </tr>`;
                    }).join("");
            }
        }

        console.log("[Observability] Reports Generated");
    } catch (err) {
        console.error("[ExecDashboard] loadExecNetworkPerformance error:", err);
    }
}

// =========================================================
// TAB 6: OPTIMIZATION SUMMARY
// =========================================================
async function loadExecOptimization() {
    try {
        const [astarData, metricsData] = await Promise.allSettled([
            execFetchPost("/api/astar-pathfinding/payload", buildExecPayload()),
            execFetchGet("/api/v1/monitoring/metrics")
        ]);

        // Platform Performance Metrics
        if (metricsData.status === "fulfilled") {
            const m = metricsData.value;
            setText("opt-api-latency", fmtMs(m.api_response_time_avg));
            setText("opt-throughput", `${(m.request_throughput ?? 0).toFixed(1)} req/min`);
            setText("opt-error-rate", fmtPct(m.error_rate));
            setText("opt-engine-latency", fmtMs(m.engine_execution_time_avg));
            setText("opt-active-req", fmtNum(m.active_requests));
        }

        // Best Optimized Route Card
        if (astarData.status === "fulfilled") {
            const a = astarData.value;
            const routes = a.optimal_routes ?? a.paths ?? [];
            const bestRouteEl = document.getElementById("exec-best-route-card");
            if (bestRouteEl && routes.length > 0) {
                const best = routes[0];
                const path = best.path ?? best.optimal_path ?? [];
                bestRouteEl.innerHTML = `
                    <div class="exec-stat-row"><span>Route Path</span><strong>${Array.isArray(path) ? path.join(" → ") : path}</strong></div>
                    <div class="exec-stat-row"><span>Total Distance</span><strong>${fmtKm(best.total_distance ?? best.distance)}</strong></div>
                    <div class="exec-stat-row"><span>Total Cost</span><strong>${fmtCurrency(best.total_cost ?? best.cost)}</strong></div>
                    <div class="exec-stat-row"><span>Transit Time</span><strong>${fmtDays(best.transit_days ?? best.total_time)}</strong></div>
                    <div class="exec-stat-row"><span>Nodes Explored</span><strong>${fmtNum(best.nodes_explored ?? a.statistics?.nodes_explored)}</strong></div>
                `;
            } else if (bestRouteEl) {
                bestRouteEl.innerHTML = `<div class="exec-loading text-muted">No optimized route data available</div>`;
            }
        }

        // Algorithm Comparison Table
        const tbody = document.getElementById("exec-algo-comparison");
        if (tbody) {
            const algos = [
                { name: "A* Pathfinding", data: astarData, color: "success" },
                { name: "Genetic Algorithm", data: null, color: "warning" },
                { name: "Ant Colony (ACO)", data: null, color: "warning" }
            ];

            tbody.innerHTML = algos.map(algo => {
                if (algo.data && algo.data.status === "fulfilled") {
                    const d = algo.data.value;
                    const routes = d.optimal_routes ?? d.paths ?? [];
                    const best = routes[0] ?? {};
                    const path = best.path ?? best.optimal_path ?? [];
                    return `<tr>
                        <td><strong><i class="fa-solid fa-star" style="color:#f59e0b; margin-right:4px;"></i>${algo.name}</strong></td>
                        <td style="font-size:11px;">${Array.isArray(path) ? path.slice(0,3).join(" → ") + (path.length > 3 ? "…" : "") : "—"}</td>
                        <td>${fmtCurrency(best.total_cost ?? best.cost)}</td>
                        <td>${fmtDays(best.transit_days ?? best.total_time)}</td>
                        <td>${fmtNum(best.nodes_explored ?? d.statistics?.nodes_explored)}</td>
                        <td><span class="badge ${algo.color}">LOADED</span></td>
                    </tr>`;
                }
                return `<tr>
                    <td><strong>${algo.name}</strong></td>
                    <td colspan="4" class="text-muted" style="font-size:11px;">Run from Route Intelligence section to load results</td>
                    <td><span class="badge">PENDING</span></td>
                </tr>`;
            }).join("");
        }

        console.log("[Observability] Reports Generated");
    } catch (err) {
        console.error("[ExecDashboard] loadExecOptimization error:", err);
    }
}

// =========================================================
// TAB 7: REGIONAL INSIGHTS
// =========================================================
async function loadExecRegionalInsights() {
    try {
        const [geoData, capacityData] = await Promise.allSettled([
            execFetchPost("/api/geospatial-analytics/payload", buildExecPayload()),
            execFetchPost("/api/capacity-analytics/payload", buildExecPayload())
        ]);

        // Hub Performance Table
        if (capacityData.status === "fulfilled") {
            const c = capacityData.value;
            const hubs = c.hubs_analysis ?? c.hub_rankings ?? c.hubs ?? [];
            const tbody = document.getElementById("exec-regional-hub-table");
            if (tbody) {
                tbody.innerHTML = hubs.length === 0
                    ? `<tr><td colspan="6" class="text-center text-muted">No hub data available</td></tr>`
                    : hubs.map(h => {
                        const util = h.utilization_rate ?? h.utilization ?? 0;
                        const status = util > 85 ? "danger" : util > 65 ? "warning" : "success";
                        return `<tr>
                            <td><strong>${h.hub ?? h.name ?? "—"}</strong></td>
                            <td>${h.region ?? "—"}</td>
                            <td>${fmtNum(h.shipments ?? h.total_shipments)}</td>
                            <td>
                                <div class="exec-progress-bar-wrap">
                                    <div class="exec-progress-bar ${status === "danger" ? "danger" : status === "warning" ? "warning" : ""}" style="width:${Math.min(util,100)}%"></div>
                                </div>
                                ${util.toFixed(1)}%
                            </td>
                            <td>${fmtKm(h.avg_distance ?? h.distance)}</td>
                            <td><span class="badge ${status}">${status === "danger" ? "OVERLOADED" : status === "warning" ? "HIGH" : "OPTIMAL"}</span></td>
                        </tr>`;
                    }).join("");
            }

            // Regional Chart (Plotly bar)
            if (typeof Plotly !== "undefined") {
                const labels = hubs.map(h => h.hub ?? h.name ?? "");
                const vals = hubs.map(h => h.utilization_rate ?? h.utilization ?? 0);
                Plotly.react("exec-regional-chart", [{
                    x: labels, y: vals, type: "bar",
                    marker: { color: vals.map(v => v > 85 ? "#ef4444" : v > 65 ? "#f59e0b" : "#10b981") }
                }], {
                    paper_bgcolor: "transparent", plot_bgcolor: "transparent",
                    font: { color: "#9ca3af", size: 11 },
                    margin: { t: 10, r: 10, b: 60, l: 50 },
                    xaxis: { gridcolor: "rgba(255,255,255,0.05)", tickangle: -30 },
                    yaxis: { gridcolor: "rgba(255,255,255,0.05)", ticksuffix: "%" }
                }, { responsive: true, displayModeBar: false });
            }
        }

        // Repair Center Table
        if (geoData.status === "fulfilled") {
            const g = geoData.value;
            const rcs = g.nearest_mapping ?? g.repair_centers ?? g.rc_mapping ?? [];
            const tbody = document.getElementById("exec-regional-rc-table");
            if (tbody) {
                const rcArr = Array.isArray(rcs) ? rcs : Object.entries(rcs).map(([k, v]) => ({ name: k, ...v }));
                tbody.innerHTML = rcArr.length === 0
                    ? `<tr><td colspan="4" class="text-center text-muted">No RC data available</td></tr>`
                    : rcArr.slice(0, 10).map(rc => `<tr>
                        <td><strong>${rc.name ?? rc.rc ?? rc.repair_center ?? "—"}</strong></td>
                        <td>${rc.nearest_hub ?? rc.hub ?? "—"}</td>
                        <td>${fmtKm(rc.distance ?? rc.distance_km)}</td>
                        <td>${rc.coverage_area ?? rc.coverage ?? "—"}</td>
                    </tr>`).join("");
            }
        }

        console.log("[Observability] Reports Generated");
    } catch (err) {
        console.error("[ExecDashboard] loadExecRegionalInsights error:", err);
    }
}

// =========================================================
// TAB 8: STRATEGIC KPI DASHBOARD
// =========================================================
async function loadExecStrategicKPIs() {
    try {
        const [dashData, slaData, costData, transitData, capacityData] = await Promise.allSettled([
            execFetchGet("/api/analytics/dashboard"),
            execFetchPost("/api/sla-analytics/payload", buildExecPayload()),
            execFetchPost("/api/cost-analytics/payload", buildExecPayload()),
            execFetchPost("/api/transit-analytics/payload", buildExecPayload()),
            execFetchPost("/api/capacity-analytics/payload", buildExecPayload())
        ]);

        const now = new Date().toLocaleString();
        const tsEl = document.getElementById("exec-scorecard-timestamp");
        if (tsEl) tsEl.textContent = `As of ${now}`;

        // Build master scorecard rows
        const rows = [];

        if (dashData.status === "fulfilled") {
            const d = dashData.value;
            const kpis = d.kpis ?? d;
            rows.push(
                { cat: "Logistics Operations", metric: "Total Shipments", value: fmtNum(kpis.total_shipments), status: "success", trend: "→" },
                { cat: "Logistics Operations", metric: "On-Time Delivery Rate", value: fmtPct(kpis.on_time_delivery_rate ?? kpis.on_time_rate), status: (kpis.on_time_delivery_rate ?? 0) > 0.85 ? "success" : "warning", trend: "↑" },
                { cat: "Logistics Operations", metric: "Active Routes", value: fmtNum(kpis.active_routes), status: "success", trend: "→" }
            );
        }

        if (slaData.status === "fulfilled") {
            const s = slaData.value;
            const ov = s.overview ?? s;
            const rate = ov.compliance_rate ?? ov.sla_compliance_rate ?? 0;
            rows.push(
                { cat: "SLA Compliance", metric: "Compliance Rate", value: fmtPct(rate), status: rate > 0.9 ? "success" : rate > 0.75 ? "warning" : "danger", trend: rate > 0.9 ? "↑" : "↓" },
                { cat: "SLA Compliance", metric: "Total Violations", value: fmtNum(ov.total_violations ?? ov.violations_count), status: (ov.total_violations ?? 0) === 0 ? "success" : "danger", trend: "→" }
            );
        }

        if (costData.status === "fulfilled") {
            const c = costData.value;
            const ov = c.overview ?? c;
            rows.push(
                { cat: "Financial", metric: "Total Logistics Cost", value: fmtCurrency(ov.total_cost), status: "success", trend: "→" },
                { cat: "Financial", metric: "Avg Cost / Shipment", value: fmtCurrency(ov.avg_cost_per_shipment ?? ov.avg_cost), status: "success", trend: "↓" }
            );
        }

        if (transitData.status === "fulfilled") {
            const t = transitData.value;
            const ov = t.overview ?? t.transit_overview ?? t;
            rows.push(
                { cat: "Transit Performance", metric: "Avg Transit Time", value: fmtDays(ov.avg_transit_days ?? ov.avg_days), status: "success", trend: "→" },
                { cat: "Transit Performance", metric: "Fastest Route", value: fmtDays(ov.min_transit_days ?? ov.fastest_days), status: "success", trend: "↑" }
            );
        }

        if (capacityData.status === "fulfilled") {
            const cap = capacityData.value;
            const ov = cap.overview ?? cap;
            const util = ov.avg_utilization_rate ?? ov.avg_utilization ?? 0;
            rows.push(
                { cat: "Network Capacity", metric: "Avg Utilization", value: fmtPct(util), status: util > 0.85 ? "danger" : util > 0.65 ? "warning" : "success", trend: "→" },
                { cat: "Network Capacity", metric: "Bottlenecks", value: fmtNum((cap.bottlenecks ?? []).length), status: (cap.bottlenecks ?? []).length > 3 ? "danger" : "success", trend: "→" }
            );
        }

        // Render master scorecard table
        const tbody = document.getElementById("exec-master-scorecard");
        if (tbody) {
            tbody.innerHTML = rows.length === 0
                ? `<tr><td colspan="5" class="text-center text-muted" style="padding:1.5rem;">No data available</td></tr>`
                : rows.map(r => `<tr>
                    <td><span style="font-size:11px; color:var(--text-muted);">${r.cat}</span></td>
                    <td><strong>${r.metric}</strong></td>
                    <td><strong>${r.value}</strong></td>
                    <td><span class="badge ${r.status}">${r.status.toUpperCase()}</span></td>
                    <td style="font-size:1.2rem; color:${r.trend === "↑" ? "#10b981" : r.trend === "↓" ? "#ef4444" : "#9ca3af"};">${r.trend}</td>
                </tr>`).join("");
        }

        // Executive Summary Panel
        buildExecStrategicSummary(dashData, slaData, costData);

        console.log("[Observability] Reports Generated");
    } catch (err) {
        console.error("[ExecDashboard] loadExecStrategicKPIs error:", err);
    }
}

function buildExecStrategicSummary(dashData, slaData, costData) {
    const el = document.getElementById("exec-strategic-summary");
    if (!el) return;

    const shipments = dashData.status === "fulfilled"
        ? (dashData.value.kpis ?? dashData.value).total_shipments ?? "N/A" : "N/A";
    const compliance = slaData.status === "fulfilled"
        ? fmtPct((slaData.value.overview ?? slaData.value).compliance_rate) : "N/A";
    const violations = slaData.status === "fulfilled"
        ? fmtNum((slaData.value.overview ?? slaData.value).total_violations ?? 0) : "N/A";
    const totalCost = costData.status === "fulfilled"
        ? fmtCurrency((costData.value.overview ?? costData.value).total_cost) : "N/A";

    el.innerHTML = `
        <div class="exec-summary-panel">
            <div class="exec-summary-section">
                <h4><i class="fa-solid fa-chart-line" style="color:var(--accent); margin-right:8px;"></i>Operational Highlights</h4>
                <p>The Dell Logistics platform has processed <strong>${shipments}</strong> shipments with an overall SLA compliance rate of <strong>${compliance}</strong>.
                ${violations !== "0" ? `<strong style="color:#ef4444;">${violations} SLA violations</strong> require immediate attention.` : "All SLA targets are currently being met."}</p>
            </div>
            <div class="exec-summary-section">
                <h4><i class="fa-solid fa-coins" style="color:#f59e0b; margin-right:8px;"></i>Financial Summary</h4>
                <p>Total logistics cost for the current period is <strong>${totalCost}</strong>. Route optimization algorithms (A*, Genetic, ACO) are active and continuously identifying cost-saving opportunities across the network.</p>
            </div>
            <div class="exec-summary-section">
                <h4><i class="fa-solid fa-forward" style="color:#10b981; margin-right:8px;"></i>Strategic Recommendations</h4>
                <ul style="margin:0; padding-left:1.25rem; color:var(--text-muted);">
                    <li>Review SLA violations and escalate with transport partners where necessary.</li>
                    <li>Evaluate hub utilization to prevent capacity bottlenecks before peak season.</li>
                    <li>Leverage A* optimized routing to reduce logistics costs on high-frequency routes.</li>
                    <li>Enable AI-assisted decision support (Phase 35) for predictive SLA forecasting.</li>
                </ul>
            </div>
        </div>
    `;
}

// =========================================================
// EXPORT FUNCTIONS
// =========================================================

/**
 * Exports transaction data to CSV via the existing /api/bi/export endpoint.
 */
async function exportExecCSV() {
    try {
        console.log("[Observability] Export Completed");
        const res = await fetch("/api/bi/export", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filters: {}, report_type: "transactions" })
        });
        if (!res.ok) throw new Error("Export API failed");
        const blob = await res.blob();
        triggerDownload(blob, "dell_logistics_transactions.csv", "text/csv");
    } catch (err) {
        console.error("[ExecDashboard] exportExecCSV error:", err);
        alert("CSV export failed. Please try again.");
    }
}

/**
 * Downloads a KPI summary as a client-side JSON → CSV blob.
 */
async function downloadKPIReport() {
    try {
        console.log("[Observability] Export Completed");
        const dash = await execFetchGet("/api/analytics/dashboard");
        const kpis = dash.kpis ?? dash;

        const rows = Object.entries(kpis)
            .filter(([, v]) => v !== null && v !== undefined && typeof v !== "object")
            .map(([k, v]) => `"${k}","${v}"`);

        const csv = ["KPI,Value", ...rows].join("\n");
        const blob = new Blob([csv], { type: "text/csv" });
        triggerDownload(blob, "dell_kpi_report.csv", "text/csv");
    } catch (err) {
        console.error("[ExecDashboard] downloadKPIReport error:", err);
        alert("KPI report download failed. Please try again.");
    }
}

/**
 * Triggers browser print dialog for the dashboard.
 */
function printExecDashboard() {
    console.log("[Observability] Export Completed");
    window.print();
}

/**
 * Creates a temporary anchor element to trigger a file download.
 */
function triggerDownload(blob, filename, type) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// =========================================================
// ALERT BAR
// =========================================================
function showExecAlert(message) {
    const bar = document.getElementById("exec-alert-bar");
    const text = document.getElementById("exec-alert-text");
    if (bar && text) {
        text.textContent = message;
        bar.style.display = "flex";
    }
}

// =========================================================
// FORMATTING UTILITIES
// =========================================================

function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val ?? "—";
}

function setDelta(id, value, threshold, higherIsBetter) {
    const el = document.getElementById(id);
    if (!el || value == null) return;
    const isGood = higherIsBetter ? value >= threshold : value <= threshold;
    el.textContent = isGood ? "▲ On Target" : "▼ Below Target";
    el.style.color = isGood ? "#10b981" : "#ef4444";
}

function fmtNum(val) {
    if (val == null) return "—";
    return Number(val).toLocaleString();
}

function fmtCurrency(val) {
    if (val == null) return "—";
    const n = Number(val);
    if (n >= 1e7) return "₹" + (n / 1e7).toFixed(2) + "Cr";
    if (n >= 1e5) return "₹" + (n / 1e5).toFixed(2) + "L";
    return "₹" + n.toFixed(2);
}

function fmtPct(val) {
    if (val == null) return "—";
    const n = Number(val);
    // Handle both 0.95 (fraction) and 95 (percentage) forms
    const pct = n <= 1 ? n * 100 : n;
    return pct.toFixed(1) + "%";
}

function fmtDays(val) {
    if (val == null) return "—";
    return Number(val).toFixed(1) + " days";
}

function fmtMs(val) {
    if (val == null) return "—";
    return Number(val).toFixed(2) + " ms";
}

function fmtKm(val) {
    if (val == null) return "—";
    return Number(val).toFixed(1) + " km";
}

function fmtScore(val) {
    if (val == null) return "—";
    return Number(val).toFixed(1) + " / 100";
}
