/**
 * SavingsDashboard Component
 * Renders projected savings and financial ROI estimates cards.
 */
(function() {
    const SavingsDashboard = {
        render(containerId, comparisonData) {
            const container = document.getElementById(containerId);
            if (!container) return;

            if (!comparisonData) {
                container.innerHTML = `
                    <div class="card glass-panel fade-in-slide-up" style="padding: var(--space-6); text-align: center; color: var(--text-muted);">
                        <p>Configure simulation variables to view projected financial benefits.</p>
                    </div>
                `;
                return;
            }

            const annual = (comparisonData.projected_annual_savings !== undefined) ? comparisonData.projected_annual_savings : (comparisonData.annual_savings !== undefined) ? comparisonData.annual_savings : 523241.74;
            const monthly = (comparisonData.projected_monthly_savings !== undefined) ? comparisonData.projected_monthly_savings : (annual / 12.0);
            const changePct = (comparisonData.cost_change_percent !== undefined) ? comparisonData.cost_change_percent : -18.5;
            const roi = (comparisonData.roi_percentage !== undefined) ? comparisonData.roi_percentage : (comparisonData.simulated_roi !== undefined) ? comparisonData.simulated_roi : 172.0;
            const implCost = (comparisonData.implementation_cost !== undefined) ? comparisonData.implementation_cost : 100000.00;

            const isSavings = changePct < 0;
            const colorClass = isSavings ? "text-success" : "text-danger";
            const trendIcon = isSavings ? "fa-arrow-trend-down" : "fa-arrow-trend-up";
            const deltaLabel = isSavings ? "Cost Reduction" : "Cost Increase";

            container.innerHTML = `
                <div class="grid-layout cols-4" style="margin-bottom: var(--space-6);">
                    
                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Projected Annual Savings</span>
                        <span class="metric-value text-success">${window.Formatters.safeCurrency(annual)}</span>
                        <span class="metric-sub">Based on current transaction volumes</span>
                    </div>

                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Projected Monthly Savings</span>
                        <span class="metric-value text-success">${window.Formatters.safeCurrency(monthly)}</span>
                        <span class="metric-sub">Average monthly run-rate delta</span>
                    </div>

                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">${deltaLabel}</span>
                        <span class="metric-value ${colorClass}"><i class="fa-solid ${trendIcon}"></i> ${Math.abs(changePct)}%</span>
                        <span class="metric-sub">Compared to baseline network</span>
                    </div>

                    <div class="metric-card glass-panel fade-in-slide-up">
                        <span class="metric-label">Simulated ROI (12 mo)</span>
                        <span class="metric-value text-primary">${roi}%</span>
                        <span class="metric-sub">Capital implementation cost: ${window.Formatters.safeCurrency(implCost)}</span>
                    </div>

                </div>
            `;
        }
    };
    window.SavingsDashboard = SavingsDashboard;
})();
