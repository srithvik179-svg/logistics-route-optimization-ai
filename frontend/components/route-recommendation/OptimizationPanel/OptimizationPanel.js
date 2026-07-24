(function() {
    const OptimizationPanel = {
        getFormInputs() {
            const source = document.getElementById("route-source-hub")?.value || "HUB-SIN";
            const dest = document.getElementById("route-dest-hub")?.value || "Bangalore";
            const part_number = document.getElementById("route-part-num")?.value || "PART-SERVER-BLADE";
            const quantity = parseInt(document.getElementById("route-quantity")?.value) || 5;
            const shipment_type = document.getElementById("route-shipment-type")?.value || "Forward Logistics";
            const priority = document.getElementById("route-priority")?.value || "High Priority";

            const constraints = [];
            if (document.getElementById("chk-fragile")?.checked) constraints.push("Fragile");
            if (document.getElementById("chk-hazardous")?.checked) constraints.push("Hazardous");
            if (document.getElementById("chk-express")?.checked) constraints.push("Express");
            if (document.getElementById("chk-temp")?.checked) constraints.push("Temperature Sensitive");

            return { source, dest, part_number, quantity, shipment_type, priority, constraints };
        },

        init(containerId, onGenerateCallback) {
            const container = document.getElementById(containerId);
            if (!container) return;

            container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up">
                    <div class="card-header" style="display:flex; justify-content:space-between; align-items:center;">
                        <h3><i class="fa-solid fa-sliders text-primary"></i> Intelligent Shipment Request</h3>
                        <span class="badge primary" style="font-size:9px;">Dell Challenge 3</span>
                    </div>
                    <div class="card-body" style="display: flex; flex-direction: column; gap: 12px; padding:14px;">
                        
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                            <div class="form-group">
                                <label class="form-label" style="font-size:11px;">Source Origin</label>
                                <select id="route-source-hub" class="form-control" style="font-size:11px;">
                                    <option value="">-- Origin --</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label" style="font-size:11px;">Destination</label>
                                <select id="route-dest-hub" class="form-control" style="font-size:11px;">
                                    <option value="">-- Destination --</option>
                                </select>
                            </div>
                        </div>

                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                            <div class="form-group">
                                <label class="form-label" style="font-size:11px;">Part Number</label>
                                <input type="text" id="route-part-num" class="form-control" value="PART-SERVER-BLADE" style="font-size:11px;" placeholder="e.g. PART-BLADE-01">
                            </div>
                            <div class="form-group">
                                <label class="form-label" style="font-size:11px;">Quantity</label>
                                <input type="number" id="route-quantity" class="form-control" value="5" min="1" max="1000" style="font-size:11px;">
                            </div>
                        </div>

                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                            <div class="form-group">
                                <label class="form-label" style="font-size:11px;">Shipment Type</label>
                                <select id="route-shipment-type" class="form-control" style="font-size:11px;">
                                    <option value="Forward Logistics" selected>Forward Logistics</option>
                                    <option value="Reverse Logistics">Reverse Logistics (Repair)</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label" style="font-size:11px;">Priority</label>
                                <select id="route-priority" class="form-control" style="font-size:11px;">
                                    <option value="High Priority" selected>High Priority</option>
                                    <option value="Medium Priority">Medium Priority</option>
                                    <option value="Low Priority">Low Priority</option>
                                </select>
                            </div>
                        </div>

                        <div class="form-group">
                            <label class="form-label" style="font-size:11px;">Special Constraints</label>
                            <div style="display:flex; flex-wrap:wrap; gap:8px; font-size:10px; color:#d4d4d8;">
                                <label style="display:flex; align-items:center; gap:4px;"><input type="checkbox" id="chk-fragile"> Fragile</label>
                                <label style="display:flex; align-items:center; gap:4px;"><input type="checkbox" id="chk-hazardous"> Hazardous</label>
                                <label style="display:flex; align-items:center; gap:4px;"><input type="checkbox" id="chk-express" checked> Express</label>
                                <label style="display:flex; align-items:center; gap:4px;"><input type="checkbox" id="chk-temp"> Temp Sensitive</label>
                            </div>
                        </div>

                        <div style="display:flex; gap:8px; margin-top:4px;">
                            <button class="btn btn-primary" id="btn-generate-recommendations" style="flex:1; font-size:11px;">
                                <i class="fa-solid fa-wand-magic-sparkles"></i> Evaluate Route
                            </button>
                            <button class="btn btn-outline-secondary" id="btn-compare-scenarios" style="font-size:11px; padding:6px 10px;" title="Compare 6 Scenarios Side-by-Side">
                                <i class="fa-solid fa-code-compare"></i> Scenarios
                            </button>
                        </div>
                    </div>
                </div>
            `;

            const triggerAutoEval = () => {
                const inputs = OptimizationPanel.getFormInputs();
                if (inputs.source && inputs.dest && inputs.source !== inputs.dest) {
                    if (onGenerateCallback) onGenerateCallback(inputs);
                }
            };

            ["route-source-hub", "route-dest-hub", "route-shipment-type", "route-priority"].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.addEventListener("change", triggerAutoEval);
            });

            document.getElementById("btn-generate-recommendations").addEventListener("click", () => {
                const inputs = OptimizationPanel.getFormInputs();
                if (!inputs.source || !inputs.dest) {
                    alert("Please select both origin and destination.");
                    return;
                }
                if (inputs.source === inputs.dest) {
                    alert("Origin and destination must be different.");
                    return;
                }

                if (onGenerateCallback) {
                    onGenerateCallback(inputs);
                }
            });

            document.getElementById("btn-compare-scenarios").addEventListener("click", () => {
                const inputs = OptimizationPanel.getFormInputs();
                if (window.openScenarioComparisonModal) {
                    window.openScenarioComparisonModal(inputs);
                }
            });
        },

        populateHubs(nodes) {
            const srcSelect = document.getElementById("route-source-hub");
            const destSelect = document.getElementById("route-dest-hub");
            if (!srcSelect || !destSelect) return;

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
