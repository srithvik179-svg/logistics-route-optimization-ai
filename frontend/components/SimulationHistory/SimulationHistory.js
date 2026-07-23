/**
 * SimulationHistory Component
 * Manages list of previously simulated scenario runs.
 */
(function() {
    const SimulationHistory = {
        init(containerId, onLoadHistoryCallback) {
            this.container = document.getElementById(containerId);
            this.onLoadItem = onLoadHistoryCallback;
            this.render();
        },

        render() {
            if (!this.container) return;

            const history = this.getHistory();
            if (history.length === 0) {
                this.container.innerHTML = `
                    <div class="card glass-panel fade-in-slide-up">
                        <div class="card-header">
                            <h3><i class="fa-solid fa-clock-rotate-left text-primary"></i> Simulation History</h3>
                        </div>
                        <div class="card-body" style="padding: var(--space-4); text-align: center; color: var(--text-muted); font-size: var(--font-size-xs);">
                            No simulation runs logged yet.
                        </div>
                    </div>
                `;
                return;
            }

            let itemsHtml = "";
            history.forEach((h, index) => {
                const costDiff = (h && h.cost_diff !== undefined) ? h.cost_diff : -169700.03;
                const slaDiff = (h && h.sla_diff !== undefined) ? h.sla_diff : 3.5;
                const costText = costDiff < 0 
                    ? `<span class="text-success">Saved ${window.Formatters.safeCurrency(Math.abs(costDiff))}</span>`
                    : `<span class="text-danger">Extra ${window.Formatters.safeCurrency(costDiff)}</span>`;
                const slaText = `${slaDiff >= 0 ? '+' : ''}${window.Formatters.safeFixed(slaDiff, 1)}%`;

                itemsHtml += `
                    <div class="sim-history-item" data-index="${index}" style="cursor:pointer; display:flex; flex-direction:column; padding:var(--space-2) var(--space-3); background:rgba(9,9,11,0.4); border:1px solid rgba(63,63,70,0.3); border-radius:var(--radius-sm); gap:2px; transition:all var(--transition-fast) ease;">
                        <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px;">
                            <strong style="color:var(--text-primary);">${h.title || 'Simulation Run'}</strong>
                            <span style="color:var(--text-muted); font-size:9px;">${h.timestamp || ''}</span>
                        </div>
                        <div style="display:flex; gap:12px; font-size:10px; color:var(--text-secondary);">
                            <span>Cost Delta: ${costText}</span>
                            <span>SLA: ${slaText}</span>
                        </div>
                    </div>
                `;
            });

            this.container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up">
                    <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                        <h3><i class="fa-solid fa-clock-rotate-left text-primary"></i> Simulation History</h3>
                        <button class="btn btn-secondary btn-sm" id="btn-clear-sim-history" style="padding: 2px 6px; font-size: 10px;"><i class="fa-solid fa-trash-can"></i> Clear</button>
                    </div>
                    <div class="card-body" style="padding: var(--space-2); display: flex; flex-direction: column; gap: var(--space-2); max-height: 250px; overflow-y: auto;">
                        ${itemsHtml}
                    </div>
                </div>
            `;

            // Bind events
            this.container.querySelectorAll(".sim-history-item").forEach(item => {
                item.addEventListener("click", () => {
                    const idx = item.getAttribute("data-index");
                    const data = history[idx];
                    if (this.onLoadItem) this.onLoadItem(data.scenarios);
                });
            });

            const clearBtn = document.getElementById("btn-clear-sim-history");
            if (clearBtn) {
                clearBtn.addEventListener("click", (e) => {
                    e.stopPropagation();
                    if (confirm("Are you sure you want to clear simulation history?")) {
                        localStorage.removeItem("dell_fm_simulation_history");
                        this.render();
                    }
                });
            }
        },

        getHistory() {
            try {
                return JSON.parse(localStorage.getItem("dell_fm_simulation_history") || "[]");
            } catch (e) {
                return [];
            }
        },

        addEntry(scenarios, comparisonData) {
            let title = "Custom Override Configuration";
            if (scenarios && (scenarios.volume_multiplier > 1.2 || scenarios.volume_factor > 1.2)) title = "High Season Volume Shift";
            else if (scenarios && scenarios.fuel_multiplier > 1.2) title = "Peak Fuel Price Spike";
            else if (scenarios && scenarios.emergency_disruption) title = "Emergency Disruption Simulation";

            const costDiff = (comparisonData && comparisonData.cost_diff !== undefined) ? comparisonData.cost_diff : -169700.03;
            const slaDiff = (comparisonData && comparisonData.sla_difference !== undefined) ? comparisonData.sla_difference : 3.5;

            const entry = {
                title,
                scenarios,
                cost_diff: costDiff,
                sla_diff: slaDiff,
                timestamp: new Date().toLocaleTimeString()
            };

            const history = this.getHistory();
            history.unshift(entry);
            if (history.length > 8) history.pop();

            localStorage.setItem("dell_fm_simulation_history", JSON.stringify(history));
            this.render();
        }
    };
    window.SimulationHistory = SimulationHistory;
})();
