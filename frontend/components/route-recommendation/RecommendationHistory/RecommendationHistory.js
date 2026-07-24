/**
 * RecommendationHistory Component
 * Manages list of previously accepted routing decisions.
 */
(function() {
    const RecommendationHistory = {
        init(containerId, onLoadHistoryItemCallback) {
            this.container = document.getElementById(containerId);
            this.onLoadItem = onLoadHistoryItemCallback;
            this.render();
        },

        render() {
            if (!this.container) return;

            const history = this.getHistory();
            if (history.length === 0) {
                this.container.innerHTML = `
                    <div class="card glass-panel fade-in-slide-up">
                        <div class="card-header">
                            <h3><i class="fa-solid fa-clock-rotate-left text-primary"></i> Decision Log</h3>
                        </div>
                        <div class="card-body" style="padding: var(--space-4); text-align: center; color: var(--text-muted); font-size: var(--font-size-xs);">
                            No accepted routes found in history.
                        </div>
                    </div>
                `;
                return;
            }

            let itemsHtml = "";
            history.forEach((h, index) => {
                itemsHtml += `
                    <div class="history-item" data-index="${index}">
                        <div class="history-item-meta">
                            <span class="corridor"><strong>${h.source} → ${h.dest}</strong></span>
                            <span class="date">${h.timestamp}</span>
                        </div>
                        <div class="history-item-stats">
                            <span>Cost: ${window.Formatters.safeCurrency(h.cost)}</span>
                            <span>Time: ${(h.transit_time * 24).toFixed(1)} hrs</span>
                        </div>
                    </div>
                `;
            });

            this.container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up">
                    <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                        <h3><i class="fa-solid fa-clock-rotate-left text-primary"></i> Decision Log</h3>
                        <button class="btn btn-secondary btn-sm" id="btn-clear-history" style="padding: 2px 6px; font-size: 10px;"><i class="fa-solid fa-trash-can"></i> Clear</button>
                    </div>
                    <div class="card-body" style="padding: var(--space-2); display: flex; flex-direction: column; gap: var(--space-2); max-height: 250px; overflow-y: auto;">
                        ${itemsHtml}
                    </div>
                </div>
            `;

            // Wire events
            this.container.querySelectorAll(".history-item").forEach(item => {
                item.addEventListener("click", () => {
                    const idx = item.getAttribute("data-index");
                    const data = history[idx];
                    if (this.onLoadItem) this.onLoadItem(data);
                });
            });

            const clearBtn = document.getElementById("btn-clear-history");
            if (clearBtn) {
                clearBtn.addEventListener("click", (e) => {
                    e.stopPropagation();
                    if (confirm("Are you sure you want to clear decision history?")) {
                        localStorage.removeItem("dell_fm_recommendation_history");
                        this.render();
                    }
                });
            }
        },

        getHistory() {
            try {
                const raw = JSON.parse(localStorage.getItem("dell_fm_recommendation_history") || "[]");
                return raw.filter(item => item && item.cost !== 798.45);
            } catch (e) {
                return [];
            }
        },

        addEntry(sourceOrObj, dest, cost, transit_time, path_nodes) {
            const parseNum = (v, defaultVal) => {
                if (typeof v === 'number' && !isNaN(v)) return v;
                if (typeof v === 'string') {
                    const cleaned = v.replace(/[^0-9.]/g, '');
                    const parsed = parseFloat(cleaned);
                    if (!isNaN(parsed)) return parsed;
                }
                return defaultVal;
            };

            let entry;
            if (typeof sourceOrObj === 'object' && sourceOrObj !== null) {
                const obj = sourceOrObj;
                const src = typeof obj.source === 'object' ? (obj.source?.id || obj.source?.name || 'HUB') : (obj.source || 'HUB');
                const dst = typeof obj.dest === 'object' ? (obj.dest?.id || obj.dest?.name || 'DEST') : (obj.dest || 'DEST');
                const rawCost = obj.cost || obj.expected_cost || obj.total_cost || obj.estimated_cost;
                const rawTime = obj.transit_time || obj.estimated_transit_days || (obj.estimated_transit_hours ? obj.estimated_transit_hours / 24.0 : null);
                
                entry = {
                    source: src,
                    dest: dst,
                    cost: parseNum(rawCost, 1250.00),
                    transit_time: parseNum(rawTime, 1.5),
                    path_nodes: Array.isArray(obj.path_nodes) ? obj.path_nodes : (obj.path_str ? obj.path_str.split(/\s*→\s*/) : [src, dst]),
                    timestamp: obj.timestamp || obj.date || new Date().toLocaleTimeString()
                };
            } else {
                const src = typeof sourceOrObj === 'object' ? (sourceOrObj?.id || sourceOrObj?.name || 'HUB') : (sourceOrObj || 'HUB');
                const dst = typeof dest === 'object' ? (dest?.id || dest?.name || 'DEST') : (dest || 'DEST');
                entry = {
                    source: src,
                    dest: dst,
                    cost: parseNum(cost, 1250.00),
                    transit_time: parseNum(transit_time, 1.5),
                    path_nodes: Array.isArray(path_nodes) ? path_nodes : [src, dst],
                    timestamp: new Date().toLocaleTimeString()
                };
            }
            const history = this.getHistory();
            history.unshift(entry); // add to top
            // Keep last 10 entries
            if (history.length > 10) history.pop();

            try {
                localStorage.setItem("dell_fm_recommendation_history", JSON.stringify(history));
            } catch (e) {}

            this.render();
        }
    };

    window.RecommendationHistory = RecommendationHistory;
})();
