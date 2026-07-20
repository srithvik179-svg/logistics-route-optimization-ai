/**
 * AI Insights Workspace & Advanced User Experience
 * Phase 35 — Dell FutureMinds Hackathon
 *
 * Provides: Workspace tabs, insight cards, decision support, operational alerts,
 * analytics workspace, productivity hub, command palette, quick search,
 * keyboard shortcuts, favorites, saved views, and recent activity.
 *
 * All data via Enterprise API Gateway. No LLM. No new backend.
 */

'use strict';

// ============================================================
// MODULE STATE
// ============================================================

/** Workspace tab loaded tracking */
const wsTabsLoaded = new Set();

/** All raw alerts collected from API responses (for filtering) */
let wsAllAlerts = [];

/** Recent activity ring buffer (max 50 entries) */
const WS_ACTIVITY_MAX = 50;
let wsActivityLog = [];

/** Favorites persisted in localStorage */
const WS_FAVORITES_KEY = 'dell_ws_favorites';
const WS_VIEWS_KEY     = 'dell_ws_saved_views';

/** Command palette state */
let cmdPaletteHighlightIdx = -1;

/** Workspace data cache (TTL 5 min) */
const wsCache = new Map();
const WS_CACHE_TTL = 5 * 60 * 1000;

// ============================================================
// REGISTERED COMMANDS
// ============================================================
const WS_COMMANDS = [
    { id: 'nav-overview',    label: 'Navigate: Overview',            icon: 'fa-house-chimney',      group: 'Navigation',   action: () => clickNav('overview-section') },
    { id: 'nav-dashboard',   label: 'Navigate: Executive Dashboard', icon: 'fa-chart-line',         group: 'Navigation',   action: () => clickNav('dashboard-section') },
    { id: 'nav-map',         label: 'Navigate: Network Map',         icon: 'fa-map-location-dot',   group: 'Navigation',   action: () => clickNav('network-map-section') },
    { id: 'nav-routes',      label: 'Navigate: Route Intelligence',  icon: 'fa-route',              group: 'Navigation',   action: () => clickNav('routes-section') },
    { id: 'nav-performance', label: 'Navigate: Logistics Performance',icon: 'fa-square-poll-vertical',group:'Navigation',  action: () => clickNav('performance-section') },
    { id: 'nav-workspace',   label: 'Navigate: AI Insights',         icon: 'fa-brain',              group: 'Navigation',   action: () => clickNav('workspace-section') },
    { id: 'nav-executive',   label: 'Navigate: Executive Center',    icon: 'fa-crown',              group: 'Navigation',   action: () => clickNav('executive-section') },
    { id: 'nav-admin',       label: 'Navigate: Admin Center',        icon: 'fa-screwdriver-wrench', group: 'Navigation',   action: () => clickNav('admin-section') },
    { id: 'nav-dataset',     label: 'Navigate: Dataset Status',      icon: 'fa-database',           group: 'Navigation',   action: () => clickNav('dataset-section') },
    { id: 'nav-explorer',    label: 'Navigate: Dataset Explorer',    icon: 'fa-magnifying-glass-chart', group: 'Navigation', action: () => clickNav('explorer-section') },
    { id: 'export-csv',      label: 'Export: Transaction CSV',       icon: 'fa-file-csv',           group: 'Export',       action: () => { closeCommandPalette(); exportExecCSV(); } },
    { id: 'export-kpi',      label: 'Export: KPI Report',            icon: 'fa-file-arrow-down',    group: 'Export',       action: () => { closeCommandPalette(); downloadKPIReport(); } },
    { id: 'export-print',    label: 'Print: Dashboard',              icon: 'fa-print',              group: 'Export',       action: () => { closeCommandPalette(); printExecDashboard(); } },
    { id: 'ws-save-view',    label: 'Save: Current View',            icon: 'fa-floppy-disk',        group: 'Workspace',    action: () => { closeCommandPalette(); promptSaveView(); } },
    { id: 'ws-shortcuts',    label: 'View: Keyboard Shortcuts',      icon: 'fa-keyboard',           group: 'Workspace',    action: () => { closeCommandPalette(); showShortcutsModal(); } },
    { id: 'ws-refresh',      label: 'Refresh: AI Insights Workspace',icon: 'fa-rotate',             group: 'Workspace',    action: () => { closeCommandPalette(); loadWorkspace(); } },
    { id: 'toggle-sidebar',  label: 'Toggle: Sidebar',               icon: 'fa-bars',               group: 'UI',           action: () => { closeCommandPalette(); document.getElementById('sidebar-toggle')?.click(); } },
];

/** Search index: all searchable items in the platform */
const WS_SEARCH_INDEX = [
    { label: 'Overview', desc: 'Platform overview dashboard', section: 'overview-section', icon: 'fa-house-chimney' },
    { label: 'Executive Analytics Dashboard', desc: 'KPIs and business intelligence', section: 'dashboard-section', icon: 'fa-chart-line' },
    { label: 'Logistics Network Map', desc: 'Geospatial hub & route visualization', section: 'network-map-section', icon: 'fa-map-location-dot' },
    { label: 'Route Intelligence', desc: 'Route network analysis and optimization', section: 'routes-section', icon: 'fa-route' },
    { label: 'Logistics Performance', desc: 'SLA, transit, cost performance monitoring', section: 'performance-section', icon: 'fa-square-poll-vertical' },
    { label: 'AI Insights Workspace', desc: 'Intelligent insights and productivity hub', section: 'workspace-section', icon: 'fa-brain' },
    { label: 'Executive Command Center', desc: 'Senior management reporting suite', section: 'executive-section', icon: 'fa-crown' },
    { label: 'Admin Center', desc: 'System administration and operations', section: 'admin-section', icon: 'fa-screwdriver-wrench' },
    { label: 'Dataset Status', desc: 'Data loading and validation status', section: 'dataset-section', icon: 'fa-database' },
    { label: 'Dataset Explorer', desc: 'Explore raw logistics datasets', section: 'explorer-section', icon: 'fa-magnifying-glass-chart' },
    { label: 'Cost Analytics', desc: 'Logistics cost breakdown and rankings', section: 'workspace-section', icon: 'fa-coins' },
    { label: 'SLA Compliance', desc: 'Service level agreement monitoring', section: 'workspace-section', icon: 'fa-shield-halved' },
    { label: 'Transit Analytics', desc: 'Transit times and on-time delivery rates', section: 'workspace-section', icon: 'fa-truck' },
    { label: 'Inventory Analytics', desc: 'Stock levels, turnover, fulfillment', section: 'workspace-section', icon: 'fa-warehouse' },
    { label: 'Network Capacity', desc: 'Hub utilization and bottleneck analysis', section: 'workspace-section', icon: 'fa-diagram-project' },
    { label: 'Optimization: A*', desc: 'A* pathfinding optimal route results', section: 'workspace-section', icon: 'fa-star' },
    { label: 'Keyboard Shortcuts', desc: 'View all keyboard shortcuts', section: null, icon: 'fa-keyboard', action: () => showShortcutsModal() },
    { label: 'Command Palette', desc: 'Open the command palette', section: null, icon: 'fa-terminal', action: () => openCommandPalette() },
];

// ============================================================
// INITIALISATION (called by DOMContentLoaded in app.js)
// ============================================================

/**
 * Initialises all global UX enhancements. Called once on page load.
 */
function initWorkspaceGlobalUX() {
    initKeyboardShortcuts();
    renderSavedViewsBar();
    renderFavoritesPanel();
    renderActivityFeed();
    console.log('[Observability] Workspace Loaded');
}

// ============================================================
// ENTRY POINT
// ============================================================

/**
 * Main entry point for the workspace section.
 * Called by app.js nav handler when #workspace-section is activated.
 */
async function loadWorkspace() {
    wsTabsLoaded.clear();
    logActivity('navigate', 'Opened AI Insights Workspace', 'fa-brain');
    await loadInsightOverview();
    wsTabsLoaded.add('ws-insights');
    console.log('[Observability] Insights Updated');
}

// ============================================================
// TAB SWITCHING
// ============================================================

async function switchWsTab(tabId, btn) {
    document.querySelectorAll('.ws-tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.ws-tab-pane').forEach(p => p.classList.remove('active'));
    const pane = document.getElementById(tabId);
    if (pane) pane.classList.add('active');

    if (!wsTabsLoaded.has(tabId)) {
        wsTabsLoaded.add(tabId);
        switch (tabId) {
            case 'ws-insights':    await loadInsightOverview(); break;
            case 'ws-decision':    await loadDecisionSupport(); break;
            case 'ws-alerts':      await loadOperationalAlerts(); break;
            case 'ws-analytics':   await loadAnalyticsWorkspace(); break;
            case 'ws-productivity':loadProductivityHub(); break;
        }
    }
    logActivity('tab', `Switched to ${btn.textContent.trim()}`, 'fa-circle-dot');
}

// ============================================================
// API HELPER
// ============================================================

async function wsFetch(url, method = 'GET', body = null) {
    const key = url + (body ? JSON.stringify(body) : '');
    const cached = wsCache.get(key);
    if (cached && Date.now() - cached.ts < WS_CACHE_TTL) return cached.data;
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    if (!res.ok) throw new Error(`${res.status} ${url}`);
    const data = await res.json();
    wsCache.set(key, { data, ts: Date.now() });
    return data;
}

const wsPost = (url, body = {}) => wsFetch(url, 'POST', body);
const wsGet  = (url)           => wsFetch(url, 'GET');

// ============================================================
// TAB 1: INSIGHT OVERVIEW
// ============================================================

// ============================================================
// DATASET STATUS HELPERS & ERROR HANDLING
// ============================================================

async function checkDatasetStatus() {
    try {
        const res = await fetch("/api/dataset/status");
        if (!res.ok) return false;
        const data = await res.json();
        return !!(data.validation_report && data.validation_report.is_valid);
    } catch (e) {
        return false;
    }
}

function showEmptyDatasetState(containerIds) {
    containerIds.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        el.innerHTML = `
            <div class="card glass-panel text-center" style="padding: 2rem; border: 1px dashed rgba(239, 68, 68, 0.4); border-radius: 8px; margin: 10px 0;">
                <i class="fa-solid fa-database text-danger" style="font-size: 2rem; margin-bottom: 1rem; opacity: 0.8;"></i>
                <h4 style="color:#fff; margin-bottom: 0.5rem;">No Dataset Loaded</h4>
                <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 1rem;">Please upload or import the Dell FutureMinds dataset to populate analytics dashboard widgets.</p>
                <button class="btn btn-primary btn-sm" onclick="navigateToDataset()">Go to Import Screen</button>
            </div>
        `;
    });
}

function showErrorState(containerIds, retryFnName) {
    containerIds.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        el.innerHTML = `
            <div class="card glass-panel text-center" style="padding: 1.5rem; border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 8px; margin: 10px 0;">
                <i class="fa-solid fa-triangle-exclamation text-danger" style="font-size: 1.5rem; margin-bottom: 0.5rem;"></i>
                <h5 style="color:#fff; margin-bottom: 0.25rem;">Failed to load widgets</h5>
                <p style="font-size: 11px; color: var(--text-muted); margin-bottom: 0.75rem;">Service connectivity issue detected.</p>
                <button class="btn btn-secondary btn-sm" onclick="${retryFnName}()" style="padding: 2px 8px; font-size: 10px;">
                    <i class="fa-solid fa-rotate-right"></i> Retry
                </button>
            </div>
        `;
    });
}

async function loadInsightOverview() {
    const containers = ['ws-highlight-strip', 'ws-opp-cards', 'ws-risk-cards', 'ws-trend-cards'];
    
    // Renders loading skeletons initially
    containers.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.innerHTML = `
                <div style="display:flex; flex-direction:column; gap:10px; padding:10px; width:100%;">
                    <div style="height:15px; width:40%; background:rgba(255,255,255,0.05); border-radius:4px;" class="skeleton-pulse"></div>
                    <div style="height:25px; width:80%; background:rgba(255,255,255,0.05); border-radius:4px;" class="skeleton-pulse"></div>
                </div>
            `;
        }
    });

    if (!document.getElementById("skeleton-animation-styles")) {
        const style = document.createElement("style");
        style.id = "skeleton-animation-styles";
        style.textContent = `
            @keyframes pulse {
                0% { opacity: 0.6; }
                50% { opacity: 0.3; }
                100% { opacity: 0.6; }
            }
            .skeleton-pulse {
                animation: pulse 1.5s infinite ease-in-out;
            }
        `;
        document.head.appendChild(style);
    }

    const isValid = await checkDatasetStatus();
    if (!isValid) {
        showEmptyDatasetState(containers);
        return;
    }

    try {
        const [dashRes, scoringRes, slaRes, biRes] = await Promise.allSettled([
            wsGet('/api/analytics/dashboard'),
            wsPost('/api/route-scoring/payload', { filters: {} }),
            wsPost('/api/sla-analytics/payload', { filters: {} }),
            wsPost('/api/bi/dashboard', { filters: {} }),
        ]);

        let success = false;

        // --- Executive Highlights ---
        if (dashRes.status === 'fulfilled' && dashRes.value) {
            renderExecutiveHighlights(dashRes.value);
            success = true;
        } else {
            showErrorState(['ws-highlight-strip'], 'loadInsightOverview');
        }

        // --- Opportunities (from route scoring: high-score routes) ---
        if (scoringRes.status === 'fulfilled' && scoringRes.value) {
            renderOpportunityCards(scoringRes.value);
            success = true;
        } else {
            showErrorState(['ws-opp-cards'], 'loadInsightOverview');
        }

        // --- Risks (from SLA violations + bottlenecks) ---
        if (slaRes.status === 'fulfilled' && slaRes.value) {
            renderRiskCards(slaRes.value);
            success = true;
        } else {
            showErrorState(['ws-risk-cards'], 'loadInsightOverview');
        }

        // --- Business Trends ---
        if (biRes.status === 'fulfilled' && biRes.value) {
            renderBusinessTrends(biRes.value, dashRes.status === 'fulfilled' ? dashRes.value : null);
            success = true;
        } else {
            showErrorState(['ws-trend-cards'], 'loadInsightOverview');
        }

        if (success) {
            initCollapsibles();
            console.log('[Observability] Insights Updated');
        }
    } catch (err) {
        console.error('[Workspace] loadInsightOverview:', err);
        showErrorState(containers, 'loadInsightOverview');
    }
}

function renderExecutiveHighlights(d) {
    const el = document.getElementById('ws-highlight-strip');
    if (!el) return;
    const kpis = d.kpis ?? d;
    const items = [
        { label: 'Total Shipments',  value: wsNum(kpis.total_shipments),    icon: 'fa-boxes-stacked', color: '#3b82f6' },
        { label: 'SLA Compliance',   value: wsPct(kpis.sla_compliance_rate ?? kpis.sla_rate), icon: 'fa-shield-halved', color: '#10b981' },
        { label: 'On-Time Rate',     value: wsPct(kpis.on_time_delivery_rate ?? kpis.on_time_rate), icon: 'fa-truck-fast', color: '#10b981' },
        { label: 'Avg Transit',      value: wsDays(kpis.avg_transit_days),  icon: 'fa-clock', color: '#f59e0b' },
        { label: 'Total Cost',       value: wsCurr(kpis.total_cost),        icon: 'fa-coins', color: '#f59e0b' },
        { label: 'Avg Cost/Ship',    value: wsCurr(kpis.avg_cost_per_shipment ?? kpis.avg_cost), icon: 'fa-receipt', color: '#8b5cf6' },
        { label: 'Active Routes',    value: wsNum(kpis.active_routes),      icon: 'fa-route', color: '#3b82f6' },
        { label: 'Active Hubs',      value: wsNum(kpis.active_hubs),        icon: 'fa-location-dot', color: '#8b5cf6' },
    ];
    el.innerHTML = items.map(it => `
        <div class="ws-highlight-tile">
            <i class="fa-solid ${it.icon}" style="color:${it.color}; font-size:1.1rem;"></i>
            <div class="ws-highlight-body">
                <span class="ws-highlight-label">${it.label}</span>
                <span class="ws-highlight-value">${it.value}</span>
            </div>
        </div>
    `).join('');
}

function renderOpportunityCards(d) {
    const el = document.getElementById('ws-opp-cards');
    if (!el) return;
    const rankings = (d.rankings ?? d.route_rankings ?? [])
        .sort((a, b) => (b.overall_score ?? b.score ?? 0) - (a.overall_score ?? a.score ?? 0))
        .slice(0, 4);

    if (rankings.length === 0) {
        el.innerHTML = '<div class="exec-loading">No opportunity data available.</div>';
        return;
    }
    el.innerHTML = rankings.map((r, i) => {
        const score = r.overall_score ?? r.score ?? 0;
        const saving = ((100 - score) * 0.4).toFixed(1);
        return `
        <div class="insight-card opportunity" onclick="logActivity('insight', 'Viewed opportunity: ${r.route ?? r.route_id}', 'fa-arrow-trend-up')">
            <div class="insight-card-header">
                <span class="insight-tag opportunity"><i class="fa-solid fa-arrow-trend-up"></i> Opportunity</span>
                <button class="ws-fav-star" onclick="event.stopPropagation(); addFavorite('route', '${r.route ?? r.route_id}', 'fa-route')" title="Add to Favorites">
                    <i class="fa-regular fa-star"></i>
                </button>
            </div>
            <div class="insight-card-title">Cost Optimization — ${r.route ?? r.route_id ?? 'Route #' + (i+1)}</div>
            <div class="insight-card-body">
                <div class="insight-metric"><span>Route Score</span><strong>${score.toFixed(1)}/100</strong></div>
                <div class="insight-metric"><span>Est. Saving Potential</span><strong style="color:#10b981;">~${saving}%</strong></div>
                <div class="insight-metric"><span>SLA Score</span><strong>${wsPct(r.sla_score ?? r.sla_compliance)}</strong></div>
                <div class="insight-metric"><span>Total Cost</span><strong>${wsCurr(r.total_cost ?? r.cost)}</strong></div>
            </div>
            <div class="insight-card-action">
                <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); clickNav('routes-section')">
                    <i class="fa-solid fa-route"></i> Explore Route
                </button>
            </div>
        </div>`;
    }).join('');
}

function renderRiskCards(d) {
    const el = document.getElementById('ws-risk-cards');
    if (!el) return;
    const ov = d.overview ?? d;
    const violations = d.violations ?? d.sla_violations ?? [];
    const critical = violations.filter(v => v.severity === 'HIGH' || v.severity === 'CRITICAL');
    const topRisks = critical.length > 0 ? critical.slice(0, 4) : violations.slice(0, 4);

    // If no violations, show SLA compliance as low-risk card
    if (topRisks.length === 0) {
        const rate = ov.compliance_rate ?? ov.sla_compliance_rate ?? 1;
        el.innerHTML = `
        <div class="insight-card risk" style="border-left-color:#10b981;">
            <div class="insight-card-header">
                <span class="insight-tag success"><i class="fa-solid fa-circle-check"></i> All Clear</span>
            </div>
            <div class="insight-card-title">No Critical SLA Violations Detected</div>
            <div class="insight-card-body">
                <div class="insight-metric"><span>Compliance Rate</span><strong style="color:#10b981;">${wsPct(rate)}</strong></div>
            </div>
        </div>`;
        return;
    }

    el.innerHTML = topRisks.map(v => {
        const sev = v.severity ?? 'MEDIUM';
        const sevColor = sev === 'CRITICAL' ? '#ef4444' : sev === 'HIGH' ? '#f59e0b' : '#6b7280';
        return `
        <div class="insight-card risk" onclick="logActivity('insight', 'Reviewed risk: ${v.route ?? v.route_id}', 'fa-triangle-exclamation')">
            <div class="insight-card-header">
                <span class="insight-tag risk" style="border-color:${sevColor}; color:${sevColor};">
                    <i class="fa-solid fa-triangle-exclamation"></i> ${sev}
                </span>
                <button class="ws-fav-star" onclick="event.stopPropagation(); addFavorite('alert', '${v.route ?? v.route_id}', 'fa-triangle-exclamation')" title="Add to Favorites">
                    <i class="fa-regular fa-star"></i>
                </button>
            </div>
            <div class="insight-card-title">SLA Breach — ${v.route ?? v.route_id ?? '—'}</div>
            <div class="insight-card-body">
                <div class="insight-metric"><span>Expected</span><strong>${wsDays(v.expected_days ?? v.sla_days)}</strong></div>
                <div class="insight-metric"><span>Actual</span><strong>${wsDays(v.actual_days ?? v.transit_days)}</strong></div>
                <div class="insight-metric"><span>Delay</span><strong style="color:#ef4444;">+${wsDays(v.delay_days ?? v.delay)}</strong></div>
            </div>
            <div class="insight-card-action">
                <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); clickNav('performance-section')">
                    <i class="fa-solid fa-eye"></i> View Details
                </button>
            </div>
        </div>`;
    }).join('');
}

function renderBusinessTrends(bi, dash) {
    const el = document.getElementById('ws-trend-cards');
    if (!el) return;
    const kpis = bi?.kpis ?? bi ?? {};
    const dkpis = dash?.kpis ?? dash ?? {};
    const modes = bi?.transport_breakdown ?? bi?.distributions?.transport_mode ?? {};
    const modeArr = Array.isArray(modes)
        ? modes
        : Object.entries(modes).map(([k, v]) => ({ mode: k, ...v }));
    const topMode = modeArr.sort((a, b) => (b.count ?? b.shipments ?? 0) - (a.count ?? a.shipments ?? 0))[0];

    const onTime = parseFloat(kpis.on_time_delivery_rate ?? dkpis.on_time_delivery_rate ?? 0);
    const sla    = parseFloat(kpis.sla_compliance_rate ?? dkpis.sla_compliance_rate ?? kpis.sla_rate ?? 0);
    const cost   = parseFloat(kpis.avg_cost_per_shipment ?? dkpis.avg_cost ?? 0);

    const trends = [
        {
            label: 'On-Time Delivery Trend',
            value: wsPct(onTime),
            trend: onTime > 0.85 ? 'up' : 'down',
            icon: 'fa-truck-fast',
            color: onTime > 0.85 ? '#10b981' : '#ef4444',
            detail: onTime > 0.85 ? 'Above 85% target' : 'Below 85% target — review routes',
        },
        {
            label: 'SLA Compliance Trend',
            value: wsPct(sla),
            trend: sla > 0.90 ? 'up' : 'down',
            icon: 'fa-shield-halved',
            color: sla > 0.90 ? '#10b981' : '#ef4444',
            detail: sla > 0.90 ? 'Within SLA targets' : 'SLA rate below 90% — escalation needed',
        },
        {
            label: 'Cost Efficiency',
            value: wsCurr(cost),
            trend: cost > 0 ? 'stable' : 'up',
            icon: 'fa-coins',
            color: '#f59e0b',
            detail: 'Average cost per shipment across all active routes',
        },
        {
            label: 'Dominant Transport Mode',
            value: topMode?.mode ?? '—',
            trend: 'stable',
            icon: 'fa-boxes-packing',
            color: '#3b82f6',
            detail: `${wsNum(topMode?.count ?? topMode?.shipments)} shipments via this mode`,
        },
    ];

    el.innerHTML = trends.map(t => `
        <div class="ws-trend-card">
            <div class="ws-trend-icon" style="color:${t.color};"><i class="fa-solid ${t.icon}"></i></div>
            <div class="ws-trend-body">
                <span class="ws-trend-label">${t.label}</span>
                <span class="ws-trend-value" style="color:${t.color};">${t.value}</span>
                <span class="ws-trend-detail">${t.detail}</span>
            </div>
            <div class="ws-trend-arrow">
                ${t.trend === 'up' ? '<i class="fa-solid fa-arrow-trend-up" style="color:#10b981;"></i>'
                  : t.trend === 'down' ? '<i class="fa-solid fa-arrow-trend-down" style="color:#ef4444;"></i>'
                  : '<i class="fa-solid fa-minus" style="color:#6b7280;"></i>'}
            </div>
        </div>
    `).join('');
}

// ============================================================
// TAB 2: DECISION SUPPORT
// ============================================================

async function loadDecisionSupport() {
    const containers = ['ws-top-performers', 'ws-bottom-performers', 'ws-opt-comparison', 'ws-sla-trend-chart'];

    // Skeletons
    document.querySelectorAll('#ws-top-performers, #ws-bottom-performers, #ws-opt-comparison').forEach(el => {
        el.innerHTML = `<tr><td colspan="5" class="text-center text-muted" style="padding:1.5rem;"><i class="fa-solid fa-spinner fa-spin"></i> Loading rankings...</td></tr>`;
    });
    const trendEl = document.getElementById("ws-sla-trend-chart");
    if (trendEl) {
        trendEl.innerHTML = `<div style="display:flex; align-items:center; justify-content:center; height:100%; color:var(--text-muted);"><i class="fa-solid fa-spinner fa-spin" style="font-size:1.5rem;"></i></div>`;
    }

    const isValid = await checkDatasetStatus();
    if (!isValid) {
        showEmptyDatasetState(containers);
        return;
    }

    try {
        const [scoringRes, slaRes, astarRes, costRes] = await Promise.allSettled([
            wsPost('/api/route-scoring/payload', { filters: {} }),
            wsPost('/api/sla-analytics/payload', { filters: {} }),
            wsPost('/api/astar-pathfinding/payload', { filters: {}, heuristic_type: 'great-circle' }),
            wsPost('/api/cost-analytics/payload', { filters: {} }),
        ]);

        let success = false;

        // Top & Bottom Performers
        if (scoringRes.status === 'fulfilled' && scoringRes.value) {
            renderPerformanceTables(scoringRes.value, slaRes.status === 'fulfilled' ? slaRes.value : null);
            success = true;
        } else {
            showErrorState(['ws-top-performers', 'ws-bottom-performers'], 'loadDecisionSupport');
        }

        // Optimization Comparison
        if (astarRes.status === 'fulfilled' && astarRes.value) {
            renderOptimizationComparison(astarRes.value);
            success = true;
        } else {
            showErrorState(['ws-opt-comparison'], 'loadDecisionSupport');
        }

        // SLA Trend Chart
        if (slaRes.status === 'fulfilled' && slaRes.value) {
            renderSLATrendChart(slaRes.value);
            success = true;
        } else {
            showErrorState(['ws-sla-trend-chart'], 'loadDecisionSupport');
        }

        if (success) {
            console.log('[Observability] Insights Updated');
        }
    } catch (err) {
        console.error('[Workspace] loadDecisionSupport:', err);
        showErrorState(containers, 'loadDecisionSupport');
    }
}

function renderPerformanceTables(scoring, slaData) {
    const rankings = (scoring.rankings ?? scoring.route_rankings ?? [])
        .sort((a, b) => (b.overall_score ?? b.score ?? 0) - (a.overall_score ?? a.score ?? 0));
    const top = rankings.slice(0, 8);
    const bottom = [...rankings].reverse().slice(0, 8);
    const violations = slaData ? (slaData.violations ?? slaData.sla_violations ?? []) : [];

    const violMap = {};
    violations.forEach(v => { violMap[v.route ?? v.route_id] = (violMap[v.route ?? v.route_id] || 0) + 1; });

    const topTbody = document.getElementById('ws-top-performers');
    const botTbody = document.getElementById('ws-bottom-performers');

    if (topTbody) {
        topTbody.innerHTML = top.length === 0
            ? '<tr><td colspan="5" class="text-center text-muted" style="padding:1rem;">No data</td></tr>'
            : top.map((r, i) => {
                const score = r.overall_score ?? r.score ?? 0;
                const route = r.route ?? r.route_id ?? '—';
                return `<tr>
                    <td><span class="exec-rank-badge">#${i+1}</span> ${route}</td>
                    <td><strong>${score.toFixed(1)}</strong></td>
                    <td>${wsPct(r.sla_score ?? r.sla_compliance)}</td>
                    <td>${wsCurr(r.total_cost ?? r.cost)}</td>
                    <td>
                        <button class="btn btn-secondary btn-sm" style="padding:2px 8px;"
                            onclick="addFavorite('route','${route}','fa-route'); logActivity('favorite','Starred route: ${route}','fa-star')">
                            <i class="fa-regular fa-star"></i>
                        </button>
                    </td>
                </tr>`;
            }).join('');
    }

    if (botTbody) {
        botTbody.innerHTML = bottom.length === 0
            ? '<tr><td colspan="5" class="text-center text-muted" style="padding:1rem;">No data</td></tr>'
            : bottom.map((r, i) => {
                const score = r.overall_score ?? r.score ?? 0;
                const route = r.route ?? r.route_id ?? '—';
                const viols = violMap[route] ?? 0;
                return `<tr>
                    <td><span class="exec-rank-badge danger">#${rankings.length - i}</span> ${route}</td>
                    <td><strong style="color:#ef4444;">${score.toFixed(1)}</strong></td>
                    <td>${viols > 0 ? `<span class="badge danger">${viols}</span>` : '0'}</td>
                    <td>${wsCurr(r.total_cost ?? r.cost)}</td>
                    <td>
                        <button class="btn btn-secondary btn-sm" style="padding:2px 8px;"
                            onclick="clickNav('performance-section'); logActivity('navigate','Reviewed underperformer: ${route}','fa-arrow-trend-down')">
                            <i class="fa-solid fa-eye"></i>
                        </button>
                    </td>
                </tr>`;
            }).join('');
    }
}

function renderOptimizationComparison(astar) {
    const tbody = document.getElementById('ws-opt-comparison');
    if (!tbody) return;

    const astarRoutes = astar?.optimal_routes ?? astar?.paths ?? [];
    const best = astarRoutes[0] ?? {};
    const path = best.path ?? best.optimal_path ?? [];
    const pathStr = Array.isArray(path) ? path.slice(0, 3).join(' → ') + (path.length > 3 ? '…' : '') : '—';

    const rows = [
        { metric: 'Best Route Path', astar: pathStr, ga: 'Run GA Engine', aco: 'Run ACO Engine' },
        { metric: 'Total Cost', astar: wsCurr(best.total_cost ?? best.cost), ga: '—', aco: '—' },
        { metric: 'Transit Time', astar: wsDays(best.transit_days ?? best.total_time), ga: '—', aco: '—' },
        { metric: 'Nodes Explored', astar: wsNum(best.nodes_explored ?? astar?.statistics?.nodes_explored), ga: '—', aco: '—' },
        { metric: 'Algorithm Status', astar: '<span class="badge success">ACTIVE</span>', ga: '<span class="badge">AVAILABLE</span>', aco: '<span class="badge">AVAILABLE</span>' },
    ];

    tbody.innerHTML = rows.map(row => `<tr>
        <td><strong>${row.metric}</strong></td>
        <td style="color:#fef08a;">${row.astar}</td>
        <td style="color:#93c5fd;">${row.ga}</td>
        <td style="color:#c4b5fd;">${row.aco}</td>
        <td>${row.metric === 'Total Cost' || row.metric === 'Transit Time'
            ? '<span class="badge success">A*</span>'
            : row.metric === 'Algorithm Status' ? '—'
            : '—'}</td>
    </tr>`).join('');
}

function renderSLATrendChart(slaData) {
    if (typeof Plotly === 'undefined') return;
    const dist = slaData.distribution ?? slaData.sla_distribution ?? {};
    const labels = Object.keys(dist);
    const vals   = Object.values(dist).map(v => typeof v === 'number' ? v : v.count ?? 0);
    if (labels.length === 0) return;

    Plotly.react('ws-sla-trend-chart', [{
        x: labels, y: vals, type: 'bar',
        marker: { color: vals.map((v, i) => i === 0 ? '#10b981' : '#ef4444') },
    }], {
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        font: { color: '#9ca3af', size: 11 },
        margin: { t: 10, r: 10, b: 40, l: 50 },
        xaxis: { gridcolor: 'rgba(255,255,255,0.05)' },
        yaxis: { gridcolor: 'rgba(255,255,255,0.05)' },
    }, { responsive: true, displayModeBar: false });
}

// ============================================================
// TAB 3: OPERATIONAL ALERTS
// ============================================================

async function loadOperationalAlerts() {
    const feed = document.getElementById('ws-alert-feed');
    if (feed) feed.innerHTML = '<div class="exec-loading"><i class="fa-solid fa-spinner fa-spin"></i> Scanning for alerts...</div>';

    const isValid = await checkDatasetStatus();
    if (!isValid) {
        showEmptyDatasetState(['ws-alert-feed']);
        return;
    }

    try {
        const [slaRes, capacityRes] = await Promise.allSettled([
            wsPost('/api/sla-analytics/payload', { filters: {} }),
            wsPost('/api/capacity-analytics/payload', { filters: {} }),
        ]);

        wsAllAlerts = [];

        if (slaRes.status === 'fulfilled' && slaRes.value) {
            const violations = slaRes.value.violations ?? slaRes.value.sla_violations ?? [];
            violations.forEach(v => {
                wsAllAlerts.push({
                    id: `sla-${v.route ?? v.route_id ?? Math.random()}`,
                    type: 'SLA Violation',
                    severity: v.severity ?? 'MEDIUM',
                    title: `SLA Breach — ${v.route ?? v.route_id ?? '—'}`,
                    detail: `Delay: +${wsDays(v.delay_days ?? v.delay)} (Expected: ${wsDays(v.expected_days)}, Actual: ${wsDays(v.actual_days)})`,
                    icon: 'fa-shield-halved',
                    timestamp: new Date().toLocaleTimeString(),
                    action: () => clickNav('performance-section'),
                });
            });

            // Overall SLA health alert
            const ov = slaRes.value.overview ?? slaRes.value;
            const rate = ov.compliance_rate ?? ov.sla_compliance_rate ?? 1;
            if (rate < 0.80) {
                wsAllAlerts.unshift({
                    id: 'sla-global',
                    type: 'SLA Health',
                    severity: 'CRITICAL',
                    title: `Critical SLA Compliance: ${wsPct(rate)}`,
                    detail: `Global SLA compliance is below 80% threshold. Immediate intervention required.`,
                    icon: 'fa-circle-exclamation',
                    timestamp: new Date().toLocaleTimeString(),
                });
            }
        }

        if (capacityRes.status === 'fulfilled' && capacityRes.value) {
            const bottlenecks = capacityRes.value.bottlenecks ?? [];
            bottlenecks.forEach(b => {
                const util = b.utilization_rate ?? b.utilization ?? 0;
                const sev = util > 90 ? 'CRITICAL' : util > 75 ? 'HIGH' : 'MEDIUM';
                wsAllAlerts.push({
                    id: `cap-${b.hub ?? b.name ?? Math.random()}`,
                    type: 'Capacity',
                    severity: sev,
                    title: `Capacity Risk — ${b.hub ?? b.name ?? '—'}`,
                    detail: `Utilization at ${util.toFixed(1)}% — ${sev === 'CRITICAL' ? 'immediate rerouting recommended' : 'monitor closely'}`,
                    icon: 'fa-gauge',
                    timestamp: new Date().toLocaleTimeString(),
                    action: () => clickNav('routes-section'),
                });
            });
        }

        // Add INFO alerts for healthy status
        if (wsAllAlerts.length === 0) {
            wsAllAlerts.push({
                id: 'all-clear',
                type: 'System',
                severity: 'INFO',
                title: 'All Systems Operational',
                detail: 'No critical alerts detected. SLA compliance and network capacity are within normal parameters.',
                icon: 'fa-circle-check',
                timestamp: new Date().toLocaleTimeString(),
            });
        }

        // Sort: CRITICAL > HIGH > MEDIUM > LOW > INFO
        const sevOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3, INFO: 4 };
        wsAllAlerts.sort((a, b) => (sevOrder[a.severity] ?? 5) - (sevOrder[b.severity] ?? 5));

        // Update badge count
        const critCount = wsAllAlerts.filter(a => a.severity === 'CRITICAL' || a.severity === 'HIGH').length;
        const badge = document.getElementById('ws-alert-badge');
        if (badge) {
            badge.textContent = critCount;
            badge.style.display = critCount > 0 ? 'inline-flex' : 'none';
        }

        // Update summary counts
        ['CRITICAL','HIGH','MEDIUM','LOW','INFO'].forEach(sev => {
            const cnt = wsAllAlerts.filter(a => a.severity === sev).length;
            const el = document.getElementById(`ws-cnt-${sev.toLowerCase()}`);
            if (el) el.textContent = cnt;
        });

        filterAlerts('all');
        logActivity('alert', `Scanned ${wsAllAlerts.length} alerts`, 'fa-bell');
        console.log('[Observability] Insights Updated');
    } catch (err) {
        console.error('[Workspace] loadOperationalAlerts:', err);
        showErrorState(['ws-alert-feed'], 'loadOperationalAlerts');
    }
}

function filterAlerts(severity) {
    const feed = document.getElementById('ws-alert-feed');
    if (!feed) return;
    const filtered = severity === 'all' ? wsAllAlerts : wsAllAlerts.filter(a => a.severity === severity);

    if (filtered.length === 0) {
        feed.innerHTML = '<div class="exec-loading">No alerts matching this filter.</div>';
        return;
    }

    const sevColors = { CRITICAL: '#ef4444', HIGH: '#f59e0b', MEDIUM: '#6b7280', LOW: '#3b82f6', INFO: '#10b981' };
    feed.innerHTML = filtered.map(alert => `
        <div class="alert-item" data-severity="${alert.severity}">
            <div class="alert-item-icon" style="color:${sevColors[alert.severity] ?? '#6b7280'};">
                <i class="fa-solid ${alert.icon}"></i>
            </div>
            <div class="alert-item-body">
                <div class="alert-item-header">
                    <span class="alert-item-title">${alert.title}</span>
                    <span class="alert-item-sev" style="color:${sevColors[alert.severity] ?? '#6b7280'};">${alert.severity}</span>
                </div>
                <div class="alert-item-detail">${alert.detail}</div>
                <div class="alert-item-meta">
                    <span class="alert-item-type">${alert.type}</span>
                    <span class="alert-item-time">${alert.timestamp}</span>
                </div>
            </div>
            ${alert.action ? `<button class="btn btn-secondary btn-sm alert-item-action" onclick="(${alert.action.toString()})(); logActivity('navigate','Investigated alert: ${alert.type}','fa-arrow-right')">
                <i class="fa-solid fa-arrow-right"></i>
            </button>` : ''}
        </div>
    `).join('');
}

// ============================================================
// TAB 4: ANALYTICS WORKSPACE
// ============================================================

async function loadAnalyticsWorkspace() {
    const containers = ['ws-kpi-strip', 'ws-cost-panel-content', 'ws-transit-panel-content', 'ws-inventory-panel-content', 'ws-network-panel-content'];

    // Skeletons
    containers.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = `<div style="padding:1rem; color:var(--text-muted);"><i class="fa-solid fa-spinner fa-spin"></i> Loading...</div>`;
    });

    const isValid = await checkDatasetStatus();
    if (!isValid) {
        showEmptyDatasetState(containers);
        return;
    }

    try {
        const [dashRes, costRes, transitRes, inventoryRes, capacityRes] = await Promise.allSettled([
            wsGet('/api/analytics/dashboard'),
            wsPost('/api/cost-analytics/payload', { filters: {} }),
            wsPost('/api/transit-analytics/payload', { filters: {} }),
            wsPost('/api/inventory-analytics/payload', { filters: {} }),
            wsPost('/api/capacity-analytics/payload', { filters: {} }),
        ]);

        let success = false;

        // KPI strip
        if (dashRes.status === 'fulfilled' && dashRes.value) {
            renderWsKpiStrip(dashRes.value);
            success = true;
        } else {
            showErrorState(['ws-kpi-strip'], 'loadAnalyticsWorkspace');
        }

        if (costRes.status === 'fulfilled' && costRes.value) {
            renderCostPanel(costRes.value);
            success = true;
        } else {
            showErrorState(['ws-cost-panel-content'], 'loadAnalyticsWorkspace');
        }

        if (transitRes.status === 'fulfilled' && transitRes.value) {
            renderTransitPanel(transitRes.value);
            success = true;
        } else {
            showErrorState(['ws-transit-panel-content'], 'loadAnalyticsWorkspace');
        }

        if (inventoryRes.status === 'fulfilled' && inventoryRes.value) {
            renderInventoryPanel(inventoryRes.value);
            success = true;
        } else {
            showErrorState(['ws-inventory-panel-content'], 'loadAnalyticsWorkspace');
        }

        if (capacityRes.status === 'fulfilled' && capacityRes.value) {
            renderNetworkPanel(capacityRes.value);
            success = true;
        } else {
            showErrorState(['ws-network-panel-content'], 'loadAnalyticsWorkspace');
        }

        if (success) {
            initCollapsibles();
            console.log('[Observability] Insights Updated');
        }
    } catch (err) {
        console.error('[Workspace] loadAnalyticsWorkspace:', err);
        showErrorState(containers, 'loadAnalyticsWorkspace');
    }
}

function renderWsKpiStrip(d) {
    const el = document.getElementById('ws-kpi-strip');
    if (!el) return;
    const kpis = d.kpis ?? d;
    const items = [
        { label: 'Shipments', value: wsNum(kpis.total_shipments), icon: 'fa-boxes-stacked', color: '#3b82f6' },
        { label: 'SLA %', value: wsPct(kpis.sla_compliance_rate ?? kpis.sla_rate), icon: 'fa-shield-halved', color: '#10b981' },
        { label: 'On-Time %', value: wsPct(kpis.on_time_delivery_rate), icon: 'fa-truck-fast', color: '#10b981' },
        { label: 'Avg Transit', value: wsDays(kpis.avg_transit_days), icon: 'fa-clock', color: '#f59e0b' },
        { label: 'Total Cost', value: wsCurr(kpis.total_cost), icon: 'fa-coins', color: '#f59e0b' },
        { label: 'Routes', value: wsNum(kpis.active_routes), icon: 'fa-route', color: '#8b5cf6' },
    ];
    el.innerHTML = items.map(it => `
        <div class="ws-kpi-chip">
            <i class="fa-solid ${it.icon}" style="color:${it.color};"></i>
            <span class="ws-kpi-chip-label">${it.label}</span>
            <strong class="ws-kpi-chip-value">${it.value}</strong>
        </div>
    `).join('');
}

function renderCostPanel(d) {
    const el = document.getElementById('ws-cost-panel-content');
    if (!el) return;
    const ov = d.overview ?? d;
    const rankings = (d.rankings ?? d.cost_rankings ?? []).slice(0, 5);
    el.innerHTML = `
        <div class="ws-panel-kpi-row">
            ${wsMiniKpi('Total Cost', wsCurr(ov.total_cost), 'fa-dollar-sign', '#f59e0b')}
            ${wsMiniKpi('Avg/Shipment', wsCurr(ov.avg_cost_per_shipment ?? ov.avg_cost), 'fa-receipt', '#3b82f6')}
            ${wsMiniKpi('Variance', wsCurr(ov.cost_std_dev ?? ov.cost_variance), 'fa-arrow-trend-down', '#10b981')}
            ${wsMiniKpi('Min Route', ov.min_cost_route ?? ov.cheapest_route ?? '—', 'fa-piggy-bank', '#8b5cf6')}
        </div>
        ${rankings.length > 0 ? `
        <table class="data-table" style="margin-top:0.75rem;">
            <thead><tr><th>#</th><th>Route</th><th>Total Cost</th><th>Avg Cost</th></tr></thead>
            <tbody>${rankings.map((r, i) => `<tr>
                <td>#${i+1}</td>
                <td>${r.route ?? r.route_id ?? '—'}</td>
                <td>${wsCurr(r.total_cost)}</td>
                <td>${wsCurr(r.avg_cost)}</td>
            </tr>`).join('')}</tbody>
        </table>` : ''}
    `;
}

function renderTransitPanel(d) {
    const el = document.getElementById('ws-transit-panel-content');
    if (!el) return;
    const ov = d.overview ?? d.transit_overview ?? d;
    el.innerHTML = `
        <div class="ws-panel-kpi-row">
            ${wsMiniKpi('Avg Transit', wsDays(ov.avg_transit_days ?? ov.avg_days), 'fa-clock', '#3b82f6')}
            ${wsMiniKpi('Fastest', wsDays(ov.min_transit_days ?? ov.fastest_days), 'fa-bolt', '#10b981')}
            ${wsMiniKpi('Slowest', wsDays(ov.max_transit_days ?? ov.slowest_days), 'fa-hourglass', '#ef4444')}
            ${wsMiniKpi('On-Time %', wsPct(ov.on_time_rate ?? ov.on_time_delivery_rate), 'fa-truck-fast', '#10b981')}
        </div>
    `;
}

function renderInventoryPanel(d) {
    const el = document.getElementById('ws-inventory-panel-content');
    if (!el) return;
    const ov = d.overview ?? d.inventory_overview ?? d;
    el.innerHTML = `
        <div class="ws-panel-kpi-row">
            ${wsMiniKpi('Total SKUs', wsNum(ov.total_skus ?? ov.unique_parts), 'fa-boxes-stacked', '#8b5cf6')}
            ${wsMiniKpi('Avg Stock', wsNum(ov.avg_stock_level ?? ov.avg_quantity), 'fa-warehouse', '#3b82f6')}
            ${wsMiniKpi('Fulfillment', wsPct(ov.fulfillment_rate), 'fa-circle-check', '#10b981')}
            ${wsMiniKpi('Turnover', String(ov.turnover_rate ?? ov.inventory_turnover ?? '—'), 'fa-rotate', '#f59e0b')}
        </div>
    `;
}

function renderNetworkPanel(d) {
    const el = document.getElementById('ws-network-panel-content');
    if (!el) return;
    const ov = d.overview ?? d;
    const bottlenecks = d.bottlenecks ?? [];
    el.innerHTML = `
        <div class="ws-panel-kpi-row">
            ${wsMiniKpi('Nodes', wsNum(ov.total_nodes ?? ov.total_hubs_rcs), 'fa-diagram-project', '#10b981')}
            ${wsMiniKpi('Routes', wsNum(ov.total_routes ?? ov.active_routes), 'fa-route', '#3b82f6')}
            ${wsMiniKpi('Avg Util %', wsPct(ov.avg_utilization_rate ?? ov.avg_utilization), 'fa-gauge', '#f59e0b')}
            ${wsMiniKpi('Bottlenecks', wsNum(bottlenecks.length), 'fa-circle-exclamation', bottlenecks.length > 3 ? '#ef4444' : '#10b981')}
        </div>
    `;
}

function wsMiniKpi(label, value, icon, color) {
    return `
        <div class="ws-mini-kpi">
            <i class="fa-solid ${icon}" style="color:${color}; font-size:1.1rem;"></i>
            <span class="ws-mini-kpi-value">${value}</span>
            <span class="ws-mini-kpi-label">${label}</span>
        </div>
    `;
}

// ============================================================
// TAB 5: PRODUCTIVITY HUB
// ============================================================

function loadProductivityHub() {
    renderQuickActions();
    renderFavoritesPanel();
    renderActivityFeed();
    renderSavedViewsManager();
    console.log('[Observability] Insights Updated');
}

function renderQuickActions() {
    const el = document.getElementById('ws-quick-actions');
    if (!el) return;
    const actions = [
        { label: 'Open Command Palette', icon: 'fa-terminal', color: '#3b82f6', action: 'openCommandPalette()' },
        { label: 'Quick Search', icon: 'fa-magnifying-glass', color: '#8b5cf6', action: 'openQuickSearch()' },
        { label: 'Export KPI Report', icon: 'fa-file-arrow-down', color: '#10b981', action: 'downloadKPIReport()' },
        { label: 'Export CSV', icon: 'fa-file-csv', color: '#f59e0b', action: 'exportExecCSV()' },
        { label: 'Print Dashboard', icon: 'fa-print', color: '#6b7280', action: 'printExecDashboard()' },
        { label: 'Refresh Insights', icon: 'fa-rotate', color: '#3b82f6', action: 'loadWorkspace()' },
        { label: 'View Shortcuts', icon: 'fa-keyboard', color: '#8b5cf6', action: 'showShortcutsModal()' },
        { label: 'Save Current View', icon: 'fa-floppy-disk', color: '#10b981', action: 'promptSaveView()' },
        { label: 'Go to Network Map', icon: 'fa-map-location-dot', color: '#f59e0b', action: "clickNav('network-map-section')" },
        { label: 'Go to Routes', icon: 'fa-route', color: '#3b82f6', action: "clickNav('routes-section')" },
        { label: 'Go to Admin Center', icon: 'fa-screwdriver-wrench', color: '#6b7280', action: "clickNav('admin-section')" },
        { label: 'Go to Executive Center', icon: 'fa-crown', color: '#f59e0b', action: "clickNav('executive-section')" },
    ];
    el.innerHTML = actions.map(a => `
        <button class="quick-action-btn" onclick="${a.action}; logActivity('action','${a.label}','${a.icon}')">
            <i class="fa-solid ${a.icon}" style="color:${a.color};"></i>
            <span>${a.label}</span>
        </button>
    `).join('');
}

// ============================================================
// FAVORITES MANAGER
// ============================================================

function getFavorites() {
    try { return JSON.parse(localStorage.getItem(WS_FAVORITES_KEY) || '[]'); }
    catch { return []; }
}

function saveFavorites(favs) {
    localStorage.setItem(WS_FAVORITES_KEY, JSON.stringify(favs));
}

function addFavorite(type, name, icon) {
    const favs = getFavorites();
    const id = `${type}-${name}`;
    if (favs.find(f => f.id === id)) return; // already exists
    favs.unshift({ id, type, name, icon, addedAt: new Date().toLocaleTimeString() });
    saveFavorites(favs);
    renderFavoritesPanel();
    renderSavedViewsBar();
    logActivity('favorite', `Starred: ${name}`, 'fa-star');
    console.log('[Observability] Favorites Updated');
}

function removeFavorite(id) {
    saveFavorites(getFavorites().filter(f => f.id !== id));
    renderFavoritesPanel();
    renderSavedViewsBar();
    console.log('[Observability] Favorites Updated');
}

function clearAllFavorites() {
    saveFavorites([]);
    renderFavoritesPanel();
    renderSavedViewsBar();
    console.log('[Observability] Favorites Updated');
}

function renderFavoritesPanel() {
    const el = document.getElementById('ws-favorites-panel');
    if (!el) return;
    const favs = getFavorites();
    if (favs.length === 0) {
        el.innerHTML = '<div class="exec-loading">No favorites yet. Star items to add them here.</div>';
        return;
    }
    el.innerHTML = favs.map(f => `
        <div class="fav-item">
            <div class="fav-item-icon"><i class="fa-solid ${f.icon}" style="color:#f59e0b;"></i></div>
            <div class="fav-item-body">
                <span class="fav-item-name">${f.name}</span>
                <span class="fav-item-type">${f.type} · ${f.addedAt}</span>
            </div>
            <button class="ws-panel-action-btn danger" onclick="removeFavorite('${f.id}')" title="Remove">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>
    `).join('');
}

// ============================================================
// SAVED VIEWS
// ============================================================

function getSavedViews() {
    try { return JSON.parse(localStorage.getItem(WS_VIEWS_KEY) || '[]'); }
    catch { return []; }
}

function saveSavedViews(views) {
    localStorage.setItem(WS_VIEWS_KEY, JSON.stringify(views));
}

function promptSaveView() {
    const name = prompt('Enter a name for this view:');
    if (!name || !name.trim()) return;
    const views = getSavedViews();
    const activeSection = document.querySelector('.viewport-section.active')?.id ?? 'unknown';
    const activeWsTab   = document.querySelector('.ws-tab.active')?.getAttribute('data-tab') ?? null;
    views.unshift({
        id: Date.now(),
        name: name.trim(),
        section: activeSection,
        wsTab: activeWsTab,
        savedAt: new Date().toLocaleString(),
    });
    saveSavedViews(views.slice(0, 10)); // max 10 views
    renderSavedViewsBar();
    renderSavedViewsManager();
    logActivity('view', `Saved view: ${name.trim()}`, 'fa-floppy-disk');
    console.log('[Observability] Dashboard Saved');
}

function loadView(id) {
    const views = getSavedViews();
    const view = views.find(v => v.id === id);
    if (!view) return;
    clickNav(view.section);
    if (view.wsTab) {
        setTimeout(() => {
            const btn = document.querySelector(`.ws-tab[data-tab="${view.wsTab}"]`);
            if (btn) switchWsTab(view.wsTab, btn);
        }, 300);
    }
    logActivity('view', `Loaded view: ${view.name}`, 'fa-bookmark');
}

function deleteView(id) {
    saveSavedViews(getSavedViews().filter(v => v.id !== id));
    renderSavedViewsBar();
    renderSavedViewsManager();
}

function renderSavedViewsBar() {
    const el = document.getElementById('ws-saved-views-list');
    if (!el) return;
    const views = getSavedViews();
    el.innerHTML = views.slice(0, 4).map(v => `
        <button class="saved-view-chip" onclick="loadView(${v.id})" title="Load: ${v.name} (${v.savedAt})">
            <i class="fa-solid fa-bookmark"></i> ${v.name}
        </button>
    `).join('') || '<span class="saved-views-empty">No saved views</span>';
}

function renderSavedViewsManager() {
    const el = document.getElementById('ws-views-manager');
    if (!el) return;
    const views = getSavedViews();
    if (views.length === 0) {
        el.innerHTML = '<div class="exec-loading">No saved views yet. Use "Save View" to create one.</div>';
        return;
    }
    el.innerHTML = views.map(v => `
        <div class="fav-item">
            <div class="fav-item-icon"><i class="fa-solid fa-bookmark" style="color:#10b981;"></i></div>
            <div class="fav-item-body">
                <span class="fav-item-name">${v.name}</span>
                <span class="fav-item-type">${v.section} · ${v.savedAt}</span>
            </div>
            <button class="btn btn-secondary btn-sm" onclick="loadView(${v.id})">Load</button>
            <button class="ws-panel-action-btn danger" onclick="deleteView(${v.id})" title="Delete"><i class="fa-solid fa-xmark"></i></button>
        </div>
    `).join('');
}

// ============================================================
// RECENT ACTIVITY
// ============================================================

function logActivity(type, message, icon = 'fa-circle-dot') {
    wsActivityLog.unshift({
        type, message, icon,
        time: new Date().toLocaleTimeString(),
    });
    if (wsActivityLog.length > WS_ACTIVITY_MAX) wsActivityLog.pop();
    renderActivityFeed();
}

function renderActivityFeed() {
    const el = document.getElementById('ws-activity-feed');
    if (!el) return;
    if (wsActivityLog.length === 0) {
        el.innerHTML = '<div class="exec-loading">No activity yet.</div>';
        return;
    }
    el.innerHTML = wsActivityLog.map(entry => `
        <div class="activity-item">
            <div class="activity-icon"><i class="fa-solid ${entry.icon}" style="color:#6b7280;"></i></div>
            <div class="activity-body">
                <span class="activity-message">${entry.message}</span>
                <span class="activity-time">${entry.time}</span>
            </div>
        </div>
    `).join('');
}

function clearActivity() {
    wsActivityLog = [];
    renderActivityFeed();
}

// ============================================================
// COLLAPSIBLE SECTIONS
// ============================================================

function initCollapsibles() {
    document.querySelectorAll('.ws-collapsible-header').forEach(header => {
        // Avoid double-registering
        if (header.dataset.collapsibleInit) return;
        header.dataset.collapsibleInit = '1';
        header.addEventListener('click', function () {
            const targetId = this.getAttribute('data-target');
            const body = document.getElementById(targetId);
            const chevron = this.querySelector('.ws-chevron');
            if (!body) return;
            const isOpen = body.style.maxHeight !== '0px' && body.style.maxHeight !== '';
            if (isOpen) {
                body.style.maxHeight = '0px';
                body.style.opacity = '0';
                if (chevron) chevron.style.transform = 'rotate(-90deg)';
            } else {
                body.style.maxHeight = body.scrollHeight + 'px';
                body.style.opacity = '1';
                if (chevron) chevron.style.transform = 'rotate(0deg)';
            }
        });
        // Start open
        const targetId = header.getAttribute('data-target');
        const body = document.getElementById(targetId);
        if (body) {
            body.style.maxHeight = body.scrollHeight + 5000 + 'px';
            body.style.opacity = '1';
        }
    });
}

// ============================================================
// COMMAND PALETTE
// ============================================================

function openCommandPalette() {
    const overlay = document.getElementById('cmd-palette-overlay');
    const input   = document.getElementById('cmd-palette-input');
    if (!overlay) return;
    overlay.style.display = 'flex';
    if (input) { input.value = ''; input.focus(); }
    renderCommandResults('');
    logActivity('command', 'Opened Command Palette', 'fa-terminal');
    console.log('[Observability] Command Executed');
}

function closeCommandPalette() {
    const overlay = document.getElementById('cmd-palette-overlay');
    if (overlay) overlay.style.display = 'none';
    cmdPaletteHighlightIdx = -1;
}

function closeCmdPaletteIfBg(event) {
    if (event.target === document.getElementById('cmd-palette-overlay')) closeCommandPalette();
}

function filterCommands(query) {
    renderCommandResults(query);
    cmdPaletteHighlightIdx = -1;
}

function renderCommandResults(query) {
    const el = document.getElementById('cmd-palette-results');
    if (!el) return;
    const q = query.toLowerCase().trim();
    const filtered = q === '' ? WS_COMMANDS : WS_COMMANDS.filter(c =>
        c.label.toLowerCase().includes(q) || c.group.toLowerCase().includes(q)
    );
    if (filtered.length === 0) {
        el.innerHTML = '<div class="cmd-no-results"><i class="fa-solid fa-circle-xmark"></i> No matching commands</div>';
        return;
    }
    // Group by category
    const groups = {};
    filtered.forEach(c => {
        if (!groups[c.group]) groups[c.group] = [];
        groups[c.group].push(c);
    });
    el.innerHTML = Object.entries(groups).map(([grp, cmds]) => `
        <div class="cmd-group-label">${grp}</div>
        ${cmds.map(c => `
        <div class="cmd-result-item" data-cmd-id="${c.id}" onclick="executeCommand('${c.id}')">
            <i class="fa-solid ${c.icon}"></i>
            <span>${highlightMatch(c.label, q)}</span>
        </div>`).join('')}
    `).join('');
}

function highlightMatch(text, query) {
    if (!query) return text;
    const idx = text.toLowerCase().indexOf(query.toLowerCase());
    if (idx < 0) return text;
    return text.slice(0, idx) + `<mark class="cmd-highlight">${text.slice(idx, idx + query.length)}</mark>` + text.slice(idx + query.length);
}

function executeCommand(id) {
    const cmd = WS_COMMANDS.find(c => c.id === id);
    if (!cmd) return;
    logActivity('command', `Executed: ${cmd.label}`, 'fa-terminal');
    console.log('[Observability] Command Executed');
    closeCommandPalette();
    cmd.action();
}

function cmdPaletteKeyNav(event) {
    const items = document.querySelectorAll('.cmd-result-item');
    if (event.key === 'ArrowDown') {
        event.preventDefault();
        cmdPaletteHighlightIdx = Math.min(cmdPaletteHighlightIdx + 1, items.length - 1);
    } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        cmdPaletteHighlightIdx = Math.max(cmdPaletteHighlightIdx - 1, 0);
    } else if (event.key === 'Enter') {
        event.preventDefault();
        const highlighted = items[cmdPaletteHighlightIdx];
        if (highlighted) {
            const id = highlighted.getAttribute('data-cmd-id');
            if (id) executeCommand(id);
        }
        return;
    } else if (event.key === 'Escape') {
        closeCommandPalette();
        return;
    }
    items.forEach((item, i) => item.classList.toggle('highlighted', i === cmdPaletteHighlightIdx));
    items[cmdPaletteHighlightIdx]?.scrollIntoView({ block: 'nearest' });
}

// ============================================================
// QUICK SEARCH
// ============================================================

function openQuickSearch() {
    const overlay = document.getElementById('search-overlay');
    const input   = document.getElementById('search-input');
    if (!overlay) return;
    overlay.style.display = 'flex';
    if (input) { input.value = ''; input.focus(); }
    document.getElementById('search-results').innerHTML = '<div class="search-hint">Type to search across the platform…</div>';
    logActivity('search', 'Opened Quick Search', 'fa-magnifying-glass');
}

function closeQuickSearch() {
    const overlay = document.getElementById('search-overlay');
    if (overlay) overlay.style.display = 'none';
}

function closeSearchIfBg(event) {
    if (event.target === document.getElementById('search-overlay')) closeQuickSearch();
}

function performSearch(query) {
    const el = document.getElementById('search-results');
    if (!el) return;
    const q = query.toLowerCase().trim();
    if (q.length < 2) {
        el.innerHTML = '<div class="search-hint">Type to search across the platform…</div>';
        return;
    }
    const results = WS_SEARCH_INDEX.filter(item =>
        item.label.toLowerCase().includes(q) || item.desc.toLowerCase().includes(q)
    );
    if (results.length === 0) {
        el.innerHTML = '<div class="search-hint">No results found.</div>';
        return;
    }
    el.innerHTML = results.map(r => `
        <div class="search-result-item" onclick="${r.action ? `(${r.action.toString()})()` : `clickNav('${r.section}')`}; closeQuickSearch(); logActivity('search','Navigated to: ${r.label}','fa-magnifying-glass')">
            <i class="fa-solid ${r.icon}" style="color:var(--accent-blue);"></i>
            <div class="search-result-body">
                <span class="search-result-label">${highlightMatch(r.label, q)}</span>
                <span class="search-result-desc">${r.desc}</span>
            </div>
            <i class="fa-solid fa-arrow-right" style="color:var(--text-muted); font-size:11px;"></i>
        </div>
    `).join('');
}

// ============================================================
// KEYBOARD SHORTCUTS MODAL
// ============================================================

function showShortcutsModal() {
    const overlay = document.getElementById('shortcuts-overlay');
    if (overlay) overlay.style.display = 'flex';
    logActivity('shortcut', 'Viewed keyboard shortcuts', 'fa-keyboard');
}

function closeShortcutsModal() {
    const overlay = document.getElementById('shortcuts-overlay');
    if (overlay) overlay.style.display = 'none';
}

function closeShortcutsIfBg(event) {
    if (event.target === document.getElementById('shortcuts-overlay')) closeShortcutsModal();
}

// ============================================================
// GLOBAL KEYBOARD SHORTCUTS
// ============================================================

const NAV_SHORTCUT_MAP = {
    '1': 'overview-section',
    '2': 'dashboard-section',
    '3': 'network-map-section',
    '4': 'routes-section',
    '5': 'workspace-section',
    '6': 'executive-section',
    '7': 'admin-section',
    '8': 'dataset-section',
};

function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ignore if typing in an input/textarea
        const tag = document.activeElement?.tagName;
        const isInput = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';

        // Ctrl+K — Command Palette
        if (e.ctrlKey && e.key === 'k') {
            e.preventDefault();
            const overlay = document.getElementById('cmd-palette-overlay');
            if (overlay?.style.display === 'flex') closeCommandPalette();
            else openCommandPalette();
            return;
        }

        // Ctrl+/ — Quick Search
        if (e.ctrlKey && e.key === '/') {
            e.preventDefault();
            const overlay = document.getElementById('search-overlay');
            if (overlay?.style.display === 'flex') closeQuickSearch();
            else openQuickSearch();
            return;
        }

        // Ctrl+S — Save View
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            promptSaveView();
            return;
        }

        // Escape — Close any open overlay
        if (e.key === 'Escape') {
            closeCommandPalette();
            closeQuickSearch();
            closeShortcutsModal();
            return;
        }

        if (isInput) return;

        // Shift+? — Shortcuts modal
        if (e.shiftKey && e.key === '?') {
            showShortcutsModal();
            return;
        }

        // Alt+1-8 — Section navigation
        if (e.altKey && NAV_SHORTCUT_MAP[e.key]) {
            e.preventDefault();
            clickNav(NAV_SHORTCUT_MAP[e.key]);
            logActivity('shortcut', `Alt+${e.key} → ${NAV_SHORTCUT_MAP[e.key]}`, 'fa-keyboard');
            return;
        }

        // Alt+R — Refresh current section
        if (e.altKey && e.key === 'r') {
            e.preventDefault();
            const active = document.querySelector('.viewport-section.active')?.id;
            if (active === 'workspace-section') loadWorkspace();
            else if (active === 'executive-section') loadExecutiveCommandCenter();
            return;
        }

        // Alt+B — Toggle Sidebar
        if (e.altKey && e.key === 'b') {
            e.preventDefault();
            document.getElementById('sidebar-toggle')?.click();
            return;
        }
    });
}

// ============================================================
// UTILITY: Click nav link programmatically
// ============================================================

function clickNav(sectionId) {
    const link = document.querySelector(`.nav-link[data-target="${sectionId}"]`);
    if (link) {
        link.click();
        logActivity('navigate', `Navigated to ${sectionId.replace('-section', '').replace(/-/g, ' ')}`, 'fa-arrow-right');
    }
}

// ============================================================
// FORMATTERS
// ============================================================

const wsNum  = v => window.Formatters.safeNumber(v);
const wsDays = v => window.Formatters.safeDuration(v);
const wsCurr = v => window.Formatters.safeCurrency(v);
const wsPct  = v => window.Formatters.safePercentage(v);
