/**
 * ActivityFeed Component
 * Renders continuously updating operational timeline feed of logistics events.
 */
(function() {
    const ActivityFeed = {
        render(containerId, events) {
            const el = document.getElementById(containerId);
            if (!el) return;

            const items = (events || []).map(ev => `
                <div style="display:flex; gap:var(--space-3); padding:var(--space-2) var(--space-3); background:rgba(9, 9, 11, 0.4); border:1px solid rgba(63, 63, 70, 0.2); border-radius:var(--radius-md); align-items:center;">
                    <div style="width:24px; height:24px; border-radius:50%; background:${ev.color}15; display:flex; align-items:center; justify-content:center; flex-shrink:0;">
                        <i class="fa-solid ${ev.icon}" style="color:${ev.color}; font-size:10px;"></i>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center; flex:1; gap:var(--space-2);">
                        <span style="font-size:11px; color:var(--text-secondary); line-height:1.4;">${ev.event}</span>
                        <span style="font-size:9px; color:var(--text-muted); font-weight:600; flex-shrink:0;">${ev.time}</span>
                    </div>
                </div>
            `).join("");

            el.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="height:100%;">
                    <div class="card-header" style="display:flex; justify-content:space-between; align-items:center;">
                        <h3><i class="fa-solid fa-bolt text-warning"></i> Live Activity Feed</h3>
                        <span style="font-size:9px; color:var(--text-muted);"><i class="fa-solid fa-circle text-success pulse"></i> Live Updates</span>
                    </div>
                    <div class="card-body" style="padding:var(--space-3); display:flex; flex-direction:column; gap:var(--space-2); max-height:300px; overflow-y:auto;">
                        ${items || '<p style="color:var(--text-muted); font-size:11px; text-align:center;">No activities logged.</p>'}
                    </div>
                </div>
            `;
        }
    };
    window.ActivityFeed = ActivityFeed;
})();
