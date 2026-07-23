/**
 * DecisionExplanation Component
 * Renders why a route recommendation was made, its advantages, trade-offs, and risks.
 */
(function() {
    const DecisionExplanation = {
        render(containerId, routeData, goal = "fastest_route") {
            const container = document.getElementById(containerId);
            if (!container) return;

            if (!routeData) {
                container.innerHTML = `
                    <div class="card glass-panel fade-in-slide-up" style="padding: var(--space-6); text-align: center; color: var(--text-muted);">
                        <i class="fa-solid fa-brain" style="font-size: 3rem; margin-bottom: var(--space-3); opacity: 0.3;"></i>
                        <p>Generate recommendations to view AI explanation.</p>
                    </div>
                `;
                return;
            }

            const algorithm = routeData.algorithm || "A* Pathfinding";
            // Support both primaryRec shape (confidence_score) and explainableAi shape (no confidence)
            const rawConf = routeData.confidence_score ?? routeData.confidence ?? 0.92;
            const confidence = (typeof rawConf === 'number' && rawConf <= 1 ? rawConf * 100 : rawConf).toFixed(0);
            
            // Format explanations dynamically based on goal
            let goalLabel = "Fastest Time";
            let selectionReason = routeData.why_selected || routeData.selectionReason || `This route was computed via the ${algorithm} engine as the optimal path for minimizing transit duration.`;
            let advantages = routeData.advantages || [
                "Reduces total shipping lead time to the lowest possible threshold.",
                "Decreases risk of transit-time SLA violations."
            ];
            let tradeOffs = routeData.trade_offs || routeData.tradeOffs || [
                "May choose toll roads or premium lanes, increasing total transit cost.",
                "Slightly higher fuel consumption and carbon footprint."
            ];
            let risks = routeData.potential_risks || routeData.risks || [
                "High speed transit zones are sensitive to weather and construction bottlenecks.",
                "Higher probability of speed traps or ground safety hazards."
            ];
            let businessImpact = "Increases supply chain velocity and client satisfaction indices by meeting tight SLA requirements.";

            if (goal === "cheapest_route") {
                goalLabel = "Lowest Cost";
                selectionReason = `This route was computed via the ${algorithm} engine as the optimal path for minimizing operational expenses.`;
                advantages = [
                    "Saves operational budget by choosing low-tariff logistics lanes.",
                    "Optimized vehicle loading and route pathing coefficients."
                ];
                tradeOffs = [
                    "Increases transit duration by avoiding high-speed express corridors.",
                    "Slightly lower SLA cushion margin in case of local delivery delays."
                ];
                risks = [
                    "Susceptible to route capacity locks at regional hubs.",
                    "Increased layover times during loading swaps."
                ];
                businessImpact = "Improves margin performance per order, saving overhead capital across the supplying hub mesh.";
            } else if (goal === "highest_sla_route") {
                goalLabel = "SLA Reliability";
                selectionReason = `This route was computed via the ${algorithm} engine as the optimal path for ensuring highest delivery consistency.`;
                advantages = [
                    "Chooses supply nodes with high performance ratings.",
                    "Maximizes buffer windows for handling unexpected cargo blocks."
                ];
                tradeOffs = [
                    "Marginally higher pricing and distance compared to shortest options."
                ];
                risks = [
                    "Relies on specific hub availability. System congestion at these hubs will impact transit schedules."
                ];
                businessImpact = "Solidifies customer satisfaction ratings and preserves corporate vendor credibility scores.";
            } else if (goal === "balanced_route") {
                goalLabel = "Balanced Goals";
                selectionReason = `This route was computed via the ${algorithm} engine as a Pareto-optimal compromise between transit cost and delivery speed.`;
                advantages = [
                    "Provides moderate costs while preserving quick transit lead times.",
                    "Excellent overall efficiency scorecard score."
                ];
                tradeOffs = [
                    "Not absolute lowest cost, nor absolute fastest path."
                ];
                risks = [
                    "Accumulates moderate risk metrics across multiple supply nodes."
                ];
                businessImpact = "Ensures operational stability without capital over-spend or service degradation.";
            }

            container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up">
                    <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                        <h3><i class="fa-solid fa-brain text-primary"></i> Decision Explanation</h3>
                        <span class="badge info">Confidence: ${confidence}%</span>
                    </div>
                    <div class="card-body" style="display: flex; flex-direction: column; gap: var(--space-4);">
                        <div>
                            <h4 style="font-size: var(--font-size-xs); color: var(--text-primary); margin: 0 0 var(--space-1) 0; font-weight: var(--font-weight-bold); text-transform: uppercase;">Why Selected</h4>
                            <p style="font-size: var(--font-size-xs); color: var(--text-secondary); margin: 0; line-height: 1.5;">${selectionReason}</p>
                        </div>
                        
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4);">
                            <div>
                                <h4 style="font-size: var(--font-size-xs); color: var(--success-color); margin: 0 0 var(--space-2) 0; font-weight: var(--font-weight-bold); text-transform: uppercase;"><i class="fa-solid fa-circle-check"></i> Advantages</h4>
                                <ul style="margin: 0; padding-left: var(--space-4); color: var(--text-secondary); font-size: var(--font-size-xs); display: flex; flex-direction: column; gap: 4px; line-height: 1.4;">
                                    ${advantages.map(a => `<li>${a}</li>`).join("")}
                                </ul>
                            </div>
                            <div>
                                <h4 style="font-size: var(--font-size-xs); color: var(--warning-color); margin: 0 0 var(--space-2) 0; font-weight: var(--font-weight-bold); text-transform: uppercase;"><i class="fa-solid fa-scale-balanced"></i> Trade-Offs</h4>
                                <ul style="margin: 0; padding-left: var(--space-4); color: var(--text-secondary); font-size: var(--font-size-xs); display: flex; flex-direction: column; gap: 4px; line-height: 1.4;">
                                    ${tradeOffs.map(t => `<li>${t}</li>`).join("")}
                                </ul>
                            </div>
                        </div>

                        <div>
                            <h4 style="font-size: var(--font-size-xs); color: var(--danger-color); margin: 0 0 var(--space-2) 0; font-weight: var(--font-weight-bold); text-transform: uppercase;"><i class="fa-solid fa-triangle-exclamation"></i> Potential Risks</h4>
                            <ul style="margin: 0; padding-left: var(--space-4); color: var(--text-secondary); font-size: var(--font-size-xs); display: flex; flex-direction: column; gap: 4px; line-height: 1.4;">
                                ${risks.map(r => `<li>${r}</li>`).join("")}
                            </ul>
                        </div>

                        <div style="border-top: 1px solid rgba(63, 63, 70, 0.3); padding-top: var(--space-3);">
                            <h4 style="font-size: var(--font-size-xs); color: var(--text-primary); margin: 0 0 var(--space-1) 0; font-weight: var(--font-weight-bold); text-transform: uppercase;">Business Impact</h4>
                            <p style="font-size: var(--font-size-xs); color: var(--text-secondary); margin: 0; line-height: 1.5;">${businessImpact}</p>
                        </div>
                    </div>
                </div>
            `;
        }
    };
    window.DecisionExplanation = DecisionExplanation;
})();
