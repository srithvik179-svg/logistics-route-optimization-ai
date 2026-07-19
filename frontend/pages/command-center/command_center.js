/**
 * Logistics Command Center Main Page Controller
 * Orchestrates payload fetches, searches, quick actions, and alerts ack workflows.
 */
(function() {
    let _data = null;

    async function initCommandCenterWorkspace() {
        console.log("[CommandCenter] Initializing unified command workspace dashboard...");

        // Render QuickActions & GlobalSearch immediately
        window.QuickActions.render("command-center-actions-container");
        window.GlobalSearch.render("command-center-search-container");

        // Set up spinner loaders for other containers
        ["command-center-control-container", "command-center-alerts-container", 
         "command-center-health-container", "command-center-feed-container"].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = `<div style="padding:var(--space-6); text-align:center; color:var(--text-muted);"><i class="fa-solid fa-spinner fa-spin" style="font-size:1.5rem;"></i></div>`;
        });

        try {
            const res = await fetch("/api/command-center/payload");
            if (!res.ok) throw new Error("Failed to fetch command center dashboard data");
            _data = await res.json();

            const { kpis, alerts, activity_feed, network_health } = _data;

            // 1. MissionControl KPIs
            window.MissionControl.render("command-center-control-container", kpis);

            // 2. AlertCenter table list
            window.AlertCenter.render("command-center-alerts-container", alerts);

            // 3. NetworkHealth combined score matrix
            window.NetworkHealth.render("command-center-health-container", network_health);

            // 4. Live Activity timeline list
            window.ActivityFeed.render("command-center-feed-container", activity_feed);

        } catch (err) {
            console.error("[CommandCenter] Initialization Error:", err);
            const el = document.getElementById("command-center-control-container");
            if (el) el.innerHTML = `<div class="card glass-panel" style="padding:var(--space-6); text-align:center; color:var(--danger-color);">
                <i class="fa-solid fa-triangle-exclamation"></i> Failed to load Logistics Command Center dashboard.
            </div>`;
        }
    }

    window.loadCommandCenterWorkspace = initCommandCenterWorkspace;
})();
