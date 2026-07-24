/**
 * Timeline Component
 * Represents a timeline slider at the bottom of the map allowing planners to filter active routes by days.
 */
(function() {
    const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

    const Timeline = {
        render(containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;

            container.innerHTML = `
                <div class="card glass-panel" style="padding:var(--space-3); border:1px solid rgba(63,63,70,0.4); display:flex; flex-direction:column; gap:6px;">
                    <div style="font-size:11px; font-weight:bold; color:#fff; text-transform:uppercase; display:flex; justify-content:space-between; align-items:center;">
                        <span><i class="fa-solid fa-clock text-primary"></i> Operations Timeline Slider</span>
                        <span id="timeline-day-label" style="color:var(--primary-color); font-weight:bold;">All Days</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:var(--space-3); margin-top:2px;">
                        <span style="font-size:10px; color:var(--text-muted);">Mon</span>
                        <input type="range" id="timeline-day-slider" min="-1" max="6" value="-1" oninput="Timeline.updateDay(this.value)" style="flex:1; accent-color:var(--primary-color);">
                        <span style="font-size:10px; color:var(--text-muted);">Sun</span>
                    </div>
                </div>
            `;
        },

        updateDay(val) {
            const index = parseInt(val);
            const label = document.getElementById("timeline-day-label");

            // Build active filters object combining global map filters
            const activeFilters = Object.assign({}, window.GlobalFilters || {});

            if (index === -1) {
                if (label) label.textContent = "All Days";
                delete activeFilters.day_of_week;
            } else {
                const day = DAYS[index];
                if (label) label.textContent = day;
                activeFilters.day_of_week = day;
            }

            // Sync with global filter state if available
            if (window.GlobalFilters) {
                if (index === -1) {
                    delete window.GlobalFilters.day_of_week;
                } else {
                    window.GlobalFilters.day_of_week = DAYS[index];
                }
            }

            if (window.NetworkExplorer && typeof window.NetworkExplorer.loadNetwork === "function") {
                window.NetworkExplorer.loadNetwork(activeFilters);
            }
        }
    };

    window.Timeline = Timeline;
})();
