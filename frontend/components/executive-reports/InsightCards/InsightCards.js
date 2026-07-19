/**
 * InsightCards Component
 * Renders data-driven AI-extracted highlights and categorized insights.
 */
(function() {
    const InsightCards = {
        render(containerId, insights) {
            const el = document.getElementById(containerId);
            if (!el || !insights) return;

            const cards = insights.map(ins => `
                <div class="card glass-panel fade-in-slide-up" 
                     style="border: 1px solid rgba(63, 63, 70, 0.4); padding: var(--space-3); border-left: 3px solid ${ins.color}; display: flex; gap: var(--space-3); align-items: start;">
                    <div style="width:32px; height:32px; border-radius:50%; background:${ins.color}15; display:flex; align-items:center; justify-content:center; flex-shrink:0;">
                        <i class="fa-solid ${ins.icon}" style="color:${ins.color}; font-size:14px;"></i>
                    </div>
                    <div style="display:flex; flex-direction:column; gap:2px; flex:1;">
                        <span style="font-size:8px; font-weight:700; color:${ins.color}; text-transform:uppercase; letter-spacing:0.05em;">${ins.category}</span>
                        <strong style="font-size:11px; color:#fff;">${ins.title}</strong>
                        <p style="font-size:10px; color:var(--text-secondary); margin:0; line-height:1.4;">${ins.detail}</p>
                    </div>
                </div>
            `).join("");

            el.innerHTML = `
                <div style="display:flex; flex-direction:column; gap:var(--space-3);">
                    <h3><i class="fa-solid fa-lightbulb text-primary"></i> Key Executive Insights</h3>
                    <div class="grid-layout cols-2" style="gap:var(--space-3);">
                        ${cards || '<p style="color:var(--text-muted); font-size:11px;">No insights compiled.</p>'}
                    </div>
                </div>
            `;
        }
    };
    window.InsightCards = InsightCards;
})();
