/**
 * AnalyticsWorkspace Component
 * Coordinates the analytics dashboard cards, widget configurations, and filter updates.
 */
(function() {
    const AnalyticsWorkspace = {
        init(gridContainerId, preferenceSelectId = null) {
            console.log("[AnalyticsWorkspace] Initializing Grid System...");
            window.DashboardGrid.init(gridContainerId, preferenceSelectId);
        }
    };
    window.AnalyticsWorkspace = AnalyticsWorkspace;
})();
