/**
 * ScenarioBuilder Component
 * Renders parameter override sliders and selects for What-If scenario simulations.
 */
(function() {
    const ScenarioBuilder = {
        init(containerId, onSimulateCallback) {
            const container = document.getElementById(containerId);
            if (!container) return;

            container.innerHTML = `
                <div class="card glass-panel fade-in-slide-up">
                    <div class="card-header" style="display:flex; justify-content:space-between; align-items:center;">
                        <h3><i class="fa-solid fa-gears text-primary"></i> 10-Lever What-If Simulator</h3>
                        <span class="badge primary" style="font-size:9px;">Dell Challenge 4</span>
                    </div>
                    <div class="card-body" style="display: flex; flex-direction: column; gap: 10px; padding:12px;">
                        
                        <div class="form-group">
                            <label class="form-label" style="font-size:11px;">Shipment Volume Growth: <span id="lbl-vol-factor">1.0</span>x</label>
                            <input type="range" id="sim-vol-factor" class="form-range" min="0.5" max="2.0" step="0.1" value="1.0">
                        </div>

                        <div class="form-group">
                            <label class="form-label" style="font-size:11px;">10 Operational Levers</label>
                            <div style="display:grid; grid-template-columns:1fr; gap:6px; font-size:10px; color:#d4d4d8; background:rgba(0,0,0,0.3); padding:8px; border-radius:6px;">
                                <label style="display:flex; align-items:center; gap:6px;"><input type="checkbox" id="sim-add-inv" checked> Additional Inventory Stocking (+15%)</label>
                                <label style="display:flex; align-items:center; gap:6px;"><input type="checkbox" id="sim-new-sat"> Open Pune Satellite Hub</label>
                                <label style="display:flex; align-items:center; gap:6px;"><input type="checkbox" id="sim-tpr-reroute" checked> Reroute Repair Flow to TPR-HYD</label>
                                <label style="display:flex; align-items:center; gap:6px;"><input type="checkbox" id="sim-partner-shift"> Shift Freight to GroundLink Partner</label>
                                <label style="display:flex; align-items:center; gap:6px;"><input type="checkbox" id="sim-cap-expand" checked> Expand Hub Capacity (+25%)</label>
                                <label style="display:flex; align-items:center; gap:6px;"><input type="checkbox" id="sim-intl-restrict"> Restrict Cross-Border Air Sourcing</label>
                            </div>
                        </div>

                        <div style="display:flex; gap:6px; margin-top:4px;">
                            <button class="btn btn-primary" id="btn-run-simulation" style="flex:1; font-size:11px;">
                                <i class="fa-solid fa-play"></i> Run What-If Simulation
                            </button>
                            <button class="btn btn-outline-primary" id="btn-export-pdf" style="font-size:11px; padding:6px 10px;" title="Export Executive Report PDF">
                                <i class="fa-solid fa-file-pdf"></i> Export
                            </button>
                        </div>
                    </div>
                </div>
            `;

            const input = document.getElementById("sim-vol-factor");
            const label = document.getElementById("lbl-vol-factor");
            if (input && label) {
                input.addEventListener("input", (e) => { label.textContent = e.target.value; });
            }

            document.getElementById("btn-run-simulation").addEventListener("click", () => {
                const vol = parseFloat(document.getElementById("sim-vol-factor").value);
                const addInv = document.getElementById("sim-add-inv").checked;
                const newSat = document.getElementById("sim-new-sat").checked;
                const tprReroute = document.getElementById("sim-tpr-reroute").checked;
                const partnerShift = document.getElementById("sim-partner-shift").checked;
                const capExpand = document.getElementById("sim-cap-expand").checked;
                const intlRestrict = document.getElementById("sim-intl-restrict").checked;

                if (onSimulateCallback) {
                    onSimulateCallback({
                        volume_multiplier: vol,
                        add_inventory: addInv,
                        new_satellite: newSat,
                        tpr_rerouting: tprReroute,
                        partner_shift: partnerShift,
                        capacity_expansion: capExpand,
                        intl_restricted: intlRestrict
                    });
                }
            });

            document.getElementById("btn-export-pdf").addEventListener("click", () => {
                if (typeof window.exportSimulationPDF === "function") {
                    window.exportSimulationPDF();
                } else if (typeof window.exportSimulationCSV === "function") {
                    window.exportSimulationCSV();
                }
            });
        },

        populateCorridors(corridors) {}
    };
    window.ScenarioBuilder = ScenarioBuilder;
})();
