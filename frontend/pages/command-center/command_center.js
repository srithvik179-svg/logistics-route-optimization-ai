/**
 * Logistics Command Center Main Page Controller
 * Orchestrates payload fetches, searches, quick actions, and alerts ack workflows.
 */
(function() {
    let _data = null;

    const DEFAULT_DATA = {
        kpis: {
            shipments_in_transit: 1800,
            delayed_shipments: 63,
            critical_alerts: 2,
            cost_today_usd: 2828333.75,
            avg_sla_percentage: 96.4,
            hub_utilization_pct: 74.5,
            vehicle_utilization_pct: 81.2,
            ai_recommendation_status: "Synchronized"
        },
        alerts: [
            { id: "ALT-101", severity: "Critical", title: "Capacity Bottleneck at HUB-SIN", message: "Singapore Hub utilization reached 96.4% capacity threshold.", timestamp: "10 mins ago", status: "Active", assigned_to: "" },
            { id: "ALT-102", severity: "High", title: "Corridor Delay Risk: HUB-BLR → TPR-DEL-01", message: "Monsoon weather impact increasing transit lead time by +2.4 days.", timestamp: "25 mins ago", status: "Active", assigned_to: "" },
            { id: "ALT-103", severity: "Moderate", title: "Part Inventory Shortage: Motherboard X5", message: "TPR Bangalore stock falling below 15 units safety buffer.", timestamp: "1 hour ago", status: "Acknowledged", assigned_to: "Manager-A" }
        ],
        network_health: {
            overall_health_score: 94.8,
            active_hubs: 12,
            active_routes: 108,
            on_time_performance: 96.4,
            system_status: "HEALTHY"
        },
        activity_feed: [
            { title: "Dijkstra Route Optimization Applied", description: "Cleared capacity bottlenecks across BLR-MUM corridors.", timestamp: "Just now", icon: "fa-bolt", type: "success" },
            { title: "SLA Risk Model Evaluated", description: "Random Forest model predicted 96.8% accuracy on 1,800 shipments.", timestamp: "5 mins ago", icon: "fa-brain", type: "info" }
        ]
    };

    function renderAll(data) {
        const payload = data || DEFAULT_DATA;

        if (window.QuickActions) window.QuickActions.render("command-center-actions-container");
        if (window.GlobalSearch) window.GlobalSearch.render("command-center-search-container");
        if (window.MissionControl) window.MissionControl.render("command-center-control-container", payload.kpis || DEFAULT_DATA.kpis);
        if (window.AlertCenter) window.AlertCenter.render("command-center-alerts-container", payload.alerts || DEFAULT_DATA.alerts);
        if (window.NetworkHealth) window.NetworkHealth.render("command-center-health-container", payload.network_health || DEFAULT_DATA.network_health);
        if (window.ActivityFeed) window.ActivityFeed.render("command-center-feed-container", payload.activity_feed || DEFAULT_DATA.activity_feed);
    }

    async function initCommandCenterWorkspace() {
        console.log("[CommandCenter] Initializing unified command workspace dashboard...");

        // Render immediately so screen is never blank
        renderAll(DEFAULT_DATA);

        try {
            const res = await fetch("/api/command-center/payload");
            if (res.ok) {
                const envelope = await res.json();
                _data = (envelope && envelope.payload) ? envelope.payload : envelope;
                if (_data && (_data.kpis || _data.alerts)) {
                    renderAll(_data);
                }
            }
        } catch (err) {
            console.warn("[CommandCenter] Live API fetch fallback warning:", err);
        }
    }

    window.loadCommandCenterWorkspace = initCommandCenterWorkspace;

    // Auto-init on page load if command center is visible
    document.addEventListener("DOMContentLoaded", () => {
        setTimeout(initCommandCenterWorkspace, 100);
    });
})();
