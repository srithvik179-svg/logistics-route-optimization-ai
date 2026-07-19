/**
 * RecommendationCard Component
 * Displays metrics for the selected route recommendation.
 */
(function() {
    const RecommendationCard = {
        render(containerId, routeData, vehicleType = "Ground Transport") {
            const container = document.getElementById(containerId);
            if (!container) return;

            if (!routeData) {
                container.innerHTML = `
                    <div class="card glass-panel fade-in-slide-up" style="padding: var(--space-6); text-align: center; color: var(--text-muted);">
                        <i class="fa-solid fa-route" style="font-size: 3rem; margin-bottom: var(--space-3); opacity: 0.3;"></i>
                        <p>Generate recommendations to view metrics.</p>
                    </div>
                `;
                return;
            }

            // Calculations based on vehicle type and distances
            const dist = routeData.distance;
            const hours = routeData.transit_time * 24; // convert days to hours
            const cost = routeData.cost;
            const hops = routeData.path_nodes ? routeData.path_nodes.length : 2;
            
            // Fuel estimate: 0.15 gal/mile for truck, 0.85 gal/mile for air
            const fuelFactor = vehicleType === "Air Freight" ? 0.85 : 0.15;
            const fuel = dist * fuelFactor;

            // Carbon estimate: 10.15 kg CO2 per gallon of diesel
            const carbon = fuel * 10.15;

            // SLA confidence & Risk score (based on hops and cost quality)
            const slaConfidence = Math.max(75, Math.min(99, 99 - (hops * 2)));
            const riskScore = Math.max(10, Math.min(90, (hops * 10) + (dist > 500 ? 15 : 5)));

            container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up">
                    <div class="card-header">
                        <h3><i class="fa-solid fa-circle-info text-primary"></i> Route Scorecard</h3>
                    </div>
                    <div class="card-body" style="padding: var(--space-4);">
                        <div class="metrics-grid-scorecard">
                            <div class="scorecard-metric-item">
                                <span class="label">Total Distance</span>
                                <strong class="value">${window.Formatters.safeDistance(dist)}</strong>
                            </div>
                            <div class="scorecard-metric-item">
                                <span class="label">Estimated Time</span>
                                <strong class="value">${hours.toFixed(1)} hrs</strong>
                            </div>
                            <div class="scorecard-metric-item">
                                <span class="label">Transit Cost</span>
                                <strong class="value">${window.Formatters.safeCurrency(cost)}</strong>
                            </div>
                            <div class="scorecard-metric-item">
                                <span class="label">Fuel Estimate</span>
                                <strong class="value">${fuel.toFixed(1)} gal</strong>
                            </div>
                            <div class="scorecard-metric-item">
                                <span class="label">Hub Count</span>
                                <strong class="value">${hops} hops</strong>
                            </div>
                            <div class="scorecard-metric-item">
                                <span class="label">Risk Score</span>
                                <strong class="value ${riskScore > 50 ? 'text-danger' : 'text-success'}">${riskScore}/100</strong>
                            </div>
                            <div class="scorecard-metric-item">
                                <span class="label">SLA Confidence</span>
                                <strong class="value text-success">${slaConfidence}%</strong>
                            </div>
                            <div class="scorecard-metric-item">
                                <span class="label">Carbon Estimate</span>
                                <strong class="value text-warning">${carbon.toFixed(1)} kg CO2</strong>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
    };
    window.RecommendationCard = RecommendationCard;
})();
