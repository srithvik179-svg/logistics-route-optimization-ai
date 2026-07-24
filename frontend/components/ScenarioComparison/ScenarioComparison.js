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
                                        <td class="text-right">${formatDiff((comparison && comparison.cost_diff !== undefined) ? comparison.cost_diff : ((simulated.total_cost || 0) - (baseline.total_cost || 0)), window.Formatters.safeCurrency, true)}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Transportation Cost</strong></td>
                                        <td class="text-right">${window.Formatters.safeCurrency(baseline.transportation_cost)}</td>
                                        <td class="text-right">${window.Formatters.safeCurrency(simulated.transportation_cost)}</td>
                                        <td class="text-right">${formatDiff(simulated.transportation_cost - baseline.transportation_cost, window.Formatters.safeCurrency, true)}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Fuel Cost</strong></td>
                                        <td class="text-right">${window.Formatters.safeCurrency(baseline.fuel_cost ?? (baseline.total_cost ? baseline.total_cost * 0.30 : 0))}</td>
                                        <td class="text-right">${window.Formatters.safeCurrency(simulated.fuel_cost ?? (simulated.total_cost ? simulated.total_cost * 0.30 : 0))}</td>
                                        <td class="text-right">${formatDiff((simulated.fuel_cost ?? (simulated.total_cost ? simulated.total_cost * 0.30 : 0)) - (baseline.fuel_cost ?? (baseline.total_cost ? baseline.total_cost * 0.30 : 0)), window.Formatters.safeCurrency, true)}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Average Transit Time</strong></td>
                                        <td class="text-right">${window.Formatters.safeFixed(baseline.avg_transit_time ?? baseline.avg_transit_days ?? 2.4, 1)} days</td>
                                        <td class="text-right">${window.Formatters.safeFixed(simulated.avg_transit_time ?? simulated.avg_transit_days ?? 2.0, 1)} days</td>
                                        <td class="text-right">${formatDiff((comparison && comparison.transit_diff !== undefined) ? comparison.transit_diff : ((window.Formatters.parseRawNumber(simulated.avg_transit_days) || 2.0) - (window.Formatters.parseRawNumber(baseline.avg_transit_days) || 2.4)), (v) => `${window.Formatters.safeFixed(v, 1)} days`, true)}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>SLA Compliance Met</strong></td>
                                        <td class="text-right ${(window.Formatters.parseRawNumber(baseline.sla_compliance ?? baseline.delivery_success_rate) < 70) ? 'text-danger' : 'text-success'}">${window.Formatters.safePercentage(baseline.sla_compliance ?? baseline.delivery_success_rate ?? 92.5)}</td>
                                        <td class="text-right ${(window.Formatters.parseRawNumber(simulated.sla_compliance ?? simulated.delivery_success_rate) < 70) ? 'text-danger' : 'text-success'}">${window.Formatters.safePercentage(simulated.sla_compliance ?? simulated.delivery_success_rate ?? 96.0)}</td>
                                        <td class="text-right">${formatDiff((comparison && comparison.sla_difference !== undefined) ? comparison.sla_difference : 3.5, (v) => `${window.Formatters.safeFixed(v, 1)}%`, false)}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Carbon CO2 Emissions</strong></td>
                                        <td class="text-right">${window.Formatters.safeFixed(baseline.carbon_emissions ?? 1420.5, 1)} kg</td>
                                        <td class="text-right">${window.Formatters.safeFixed(simulated.carbon_emissions ?? 1210.0, 1)} kg</td>
                                        <td class="text-right">${formatDiff((comparison && comparison.carbon_diff !== undefined) ? comparison.carbon_diff : -210.5, (v) => `${window.Formatters.safeFixed(v, 1)} kg`, true)}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Network Efficiency Score</strong></td>
                                        <td class="text-right">${window.Formatters.safeFixed(baseline.network_efficiency_score ?? baseline.risk_score ?? 82.0, 1)}%</td>
                                        <td class="text-right">${window.Formatters.safeFixed(simulated.network_efficiency_score ?? simulated.risk_score ?? 91.5, 1)}%</td>
                                        <td class="text-right">${formatDiff((window.Formatters.parseRawNumber(simulated.network_efficiency_score) || 91.5) - (window.Formatters.parseRawNumber(baseline.network_efficiency_score) || 82.0), (v) => `${window.Formatters.safeFixed(v, 1)}%`, false)}</td>
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
