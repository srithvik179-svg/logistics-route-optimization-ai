/**
 * AnalyticsCard Helper Component
 * Animates metric values, renders trend indicators, and attaches detail drawers.
 */
(Menu = function() {
    const AnalyticsCard = {
        init(cardId, title, subtext, value, trendPct, isUp = true, detailsHtml = "") {
            const card = document.getElementById(cardId);
            if (!card) return;
            
            card.className = "metric-card glass-panel fade-in-slide-up";
            
            let trendClass = isUp ? "up" : "down";
            let trendIcon = isUp ? "fa-arrow-trend-up" : "fa-arrow-trend-down";
            
            card.innerHTML = `
                <div class="card-kpi-header">
                    <span class="metric-label">${title}</span>
                    <div class="kpi-icon"><i class="fa-solid fa-chart-line"></i></div>
                </div>
                <div class="card-kpi-body">
                    <span class="metric-value" data-value="${value}">0</span>
                    <div class="kpi-trend ${trendClass}">
                        <i class="fa-solid ${trendIcon}"></i> ${trendPct}%
                    </div>
                </div>
                <div class="card-kpi-footer">
                    <span class="metric-sub">${subtext}</span>
                </div>
            `;
            
            // Wire click to expandable details panel
            if (detailsHtml) {
                card.style.cursor = "pointer";
                card.onclick = (e) => {
                    // Prevent trigger if clicking on icon/child elements that handle other flows
                    if (e.target.closest(".kpi-icon")) return;
                    window.ExpandablePanel.render(title, detailsHtml);
                };
            }
            
            // Run value counter animation
            const valSpan = card.querySelector(".metric-value");
            if (valSpan && window.Validators.isValidNumber(value)) {
                let start = 0;
                const end = parseFloat(value);
                const duration = 1000; // 1 second
                const startTime = performance.now();
                
                function updateCounter(currentTime) {
                    const elapsed = currentTime - startTime;
                    const progress = Math.min(elapsed / duration, 1);
                    const currentVal = start + progress * (end - start);
                    
                    if (end % 1 === 0) {
                        valSpan.textContent = Math.floor(currentVal).toLocaleString();
                    } else {
                        valSpan.textContent = currentVal.toFixed(2);
                    }
                    
                    if (progress < 1) {
                        requestAnimationFrame(updateCounter);
                    } else {
                        valSpan.textContent = end.toLocaleString(undefined, {
                            minimumFractionDigits: end % 1 === 0 ? 0 : 2,
                            maximumFractionDigits: end % 1 === 0 ? 0 : 2
                        });
                    }
                }
                requestAnimationFrame(updateCounter);
            }
        }
    };
    window.AnalyticsCard = AnalyticsCard;
})();
