/**
 * ScenarioComparison Component
 * Displays side-by-side comparison between Baseline and Simulated networks.
 */
(function() {
    const ScenarioComparison = {
        render(containerId, baseline, simulated, comparison) {
            const container = document.getElementById(containerId);
            if (!container) return;

            if (!baseline || !simulated) {
                container.innerHTML = `
                    <div class="card glass-panel fade-in-slide-up" style="padding: var(--space-6); text-align: center; color: var(--text-muted);">
                        <p>Generate simulation parameters to view side-by-side metrics details.</p>
                    </div>
                `;
                return;
            }

            // Differences calculation
            const formatDiff = (diff, formatFn, inverse = false) => {
                if (diff === 0) return `<span class="text-muted">--</span>`;
                const isPositive = diff > 0;
                // Cost or transit time increases are bad (danger), decreases are good (success)
                const isGood = inverse ? !isPositive : isPositive;
                const sign = isPositive ? "+" : "";
                const color = isGood ? "text-success" : "text-danger";
                return `<strong class="${color}">${sign}${formatFn(diff)}</strong>`;
            };

            container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up">
                    <div class="card-header">
                        <h3><i class="fa-solid fa-code-compare text-primary"></i> Simulation Variance Comparison</h3>
                    </div>
                    <div class="card-body" style="padding: 0;">
                        <div class="table-container">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Metrics Target</th>
                                        <th class="text-right">Baseline Mesh</th>
                                        <th class="text-right">Simulated Override</th>
                                        <th class="text-right">Variance Delta</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td><strong>Total Logistics Cost</strong></td>
                                        <td class="text-right">${window.Formatters.safeCurrency(baseline.total_cost)}</td>
                                        <td class="text-right">${window.Formatters.safeCurrency(simulated.total_cost)}</td>
                                        <td class="text-right">${formatDiff(comparison.cost_diff, window.Formatters.safeCurrency, true)}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Transportation Cost</strong></td>
                                        <td class="text-right">${window.Formatters.safeCurrency(baseline.transportation_cost)}</td>
                                        <td class="text-right">${window.Formatters.safeCurrency(simulated.transportation_cost)}</td>
                                        <td class="text-right">${formatDiff(simulated.transportation_cost - baseline.transportation_cost, window.Formatters.safeCurrency, true)}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Fuel Cost</strong></td>
                                        <td class="text-right">${window.Formatters.safeCurrency(baseline.fuel_cost)}</td>
                                        <td class="text-right">${window.Formatters.safeCurrency(simulated.fuel_cost)}</td>
                                        <td class="text-right">${formatDiff(simulated.fuel_cost - baseline.fuel_cost, window.Formatters.safeCurrency, true)}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Average Transit Time</strong></td>
                                        <td class="text-right">${baseline.avg_transit_time.toFixed(1)} days</td>
                                        <td class="text-right">${simulated.avg_transit_time.toFixed(1)} days</td>
                                        <td class="text-right">${formatDiff(comparison.transit_diff, (v) => `${v.toFixed(1)} days`, true)}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>SLA Compliance Met</strong></td>
                                        <td class="text-right ${baseline.delivery_success_rate < 70 ? 'text-danger' : 'text-success'}">${baseline.delivery_success_rate.toFixed(1)}%</td>
                                        <td class="text-right ${simulated.delivery_success_rate < 70 ? 'text-danger' : 'text-success'}">${simulated.delivery_success_rate.toFixed(1)}%</td>
                                        <td class="text-right">${formatDiff(comparison.sla_difference, (v) => `${v.toFixed(1)}%`, false)}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Carbon CO2 Emissions</strong></td>
                                        <td class="text-right">${baseline.carbon_emissions.toFixed(1)} kg</td>
                                        <td class="text-right">${simulated.carbon_emissions.toFixed(1)} kg</td>
                                        <td class="text-right">${formatDiff(comparison.carbon_diff, (v) => `${v.toFixed(1)} kg`, true)}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Network Efficiency Score</strong></td>
                                        <td class="text-right">${baseline.network_efficiency_score.toFixed(1)}%</td>
                                        <td class="text-right">${simulated.network_efficiency_score.toFixed(1)}%</td>
                                        <td class="text-right">${formatDiff(simulated.network_efficiency_score - baseline.network_efficiency_score, (v) => `${v.toFixed(1)}%`, false)}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        }
    };
    window.ScenarioComparison = ScenarioComparison;
})();
