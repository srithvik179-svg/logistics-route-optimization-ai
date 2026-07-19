/**
 * OptimizationPanel Component
 * Renders selection controls for hubs, priority, vehicle type, and optimization goals.
 */
(function() {
    const OptimizationPanel = {
        init(containerId, onGenerateCallback) {
            const container = document.getElementById(containerId);
            if (!container) return;

            container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up">
                    <div class="card-header">
                        <h3><i class="fa-solid fa-sliders text-primary"></i> Routing Inputs</h3>
                    </div>
                    <div class="card-body" style="display: flex; flex-direction: column; gap: var(--space-4);">
                        <div class="form-group">
                            <label class="form-label">Source Hub</label>
                            <select id="route-source-hub" class="form-control">
                                <option value="">-- Select Origin --</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Destination Hub</label>
                            <select id="route-dest-hub" class="form-control">
                                <option value="">-- Select Destination --</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Shipment Priority</label>
                            <select id="route-priority" class="form-control">
                                <option value="High Priority">High Priority</option>
                                <option value="Medium Priority" selected>Medium Priority</option>
                                <option value="Low Priority">Low Priority</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Vehicle Type</label>
                            <select id="route-vehicle" class="form-control">
                                <option value="Ground Transport" selected>Ground Transport (Truck)</option>
                                <option value="Air Freight">Air Freight (Cargo Plane)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Optimization Goal</label>
                            <select id="route-goal" class="form-control">
                                <option value="cheapest_route">Lowest Cost</option>
                                <option value="fastest_route" selected>Fastest Route</option>
                                <option value="highest_sla_route">Highest SLA Reliability</option>
                                <option value="balanced_route">Balanced Optimization</option>
                                <option value="min_distance">Minimum Distance</option>
                                <option value="min_fuel">Minimum Fuel Usage</option>
                            </select>
                        </div>
                        <button class="btn btn-primary" id="btn-generate-recommendations" style="width: 100%; margin-top: var(--space-2);">
                            <i class="fa-solid fa-wand-magic-sparkles"></i> Generate Recommendations
                        </button>
                    </div>
                </div>
            `;

            document.getElementById("btn-generate-recommendations").addEventListener("click", () => {
                const source = document.getElementById("route-source-hub").value;
                const dest = document.getElementById("route-dest-hub").value;
                const priority = document.getElementById("route-priority").value;
                const vehicle = document.getElementById("route-vehicle").value;
                const goal = document.getElementById("route-goal").value;

                if (!source || !dest) {
                    alert("Please select both origin and destination hubs.");
                    return;
                }
                if (source === dest) {
                    alert("Origin and destination hubs must be different.");
                    return;
                }

                if (onGenerateCallback) {
                    onGenerateCallback({ source, dest, priority, vehicle, goal });
                }
            });
        },

        populateHubs(nodes) {
            const srcSelect = document.getElementById("route-source-hub");
            const destSelect = document.getElementById("route-dest-hub");
            if (!srcSelect || !destSelect) return;

            // Filter out Repair Centers to show only Hubs for primary routes
            const hubs = nodes.filter(n => n.type !== "Repair Center");

            const populate = (select, defText) => {
                select.innerHTML = `<option value="">${defText}</option>`;
                hubs.forEach(h => {
                    const opt = document.createElement("option");
                    opt.value = h.id;
                    opt.textContent = h.name;
                    select.appendChild(opt);
                });
            };

            populate(srcSelect, "-- Select Origin --");
            populate(destSelect, "-- Select Destination --");
        }
    };
    window.OptimizationPanel = OptimizationPanel;
})();
