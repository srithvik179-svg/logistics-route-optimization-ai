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
                    <div class="card-header">
                        <h3><i class="fa-solid fa-gears text-primary"></i> Simulation Parameters</h3>
                    </div>
                    <div class="card-body" style="display: flex; flex-direction: column; gap: var(--space-4);">
                        
                        <div class="form-group">
                            <label class="form-label">Fuel Cost Scale Factor: <span id="lbl-fuel-factor">1.0</span>x</label>
                            <input type="range" id="sim-fuel-factor" class="form-range" min="0.5" max="2.0" step="0.1" value="1.0">
                        </div>

                        <div class="form-group">
                            <label class="form-label">Driver Cost Scale Factor: <span id="lbl-driver-factor">1.0</span>x</label>
                            <input type="range" id="sim-driver-factor" class="form-range" min="0.5" max="2.0" step="0.1" value="1.0">
                        </div>

                        <div class="form-group">
                            <label class="form-label">Shipment Volume: <span id="lbl-vol-factor">1.0</span>x</label>
                            <input type="range" id="sim-vol-factor" class="form-range" min="0.5" max="2.0" step="0.1" value="1.0">
                        </div>

                        <div class="form-group">
                            <label class="form-label">Transportation Mode</label>
                            <select id="sim-mode" class="form-control">
                                <option value="Keep Current" selected>Keep Current</option>
                                <option value="Air Freight">Force Air Freight</option>
                                <option value="Ground Transport">Force Ground Transport</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label class="form-label">Close Route Corridor</label>
                            <select id="sim-close-route" class="form-control">
                                <option value="">-- No Closures --</option>
                            </select>
                        </div>

                        <div class="form-group" style="display: flex; align-items: center; gap: 8px; margin-top: 4px;">
                            <input type="checkbox" id="sim-disruption" style="cursor: pointer; width: 16px; height: 16px;">
                            <label for="sim-disruption" class="form-label" style="margin: 0; cursor: pointer; text-transform: none;">Emergency Disruption Lock</label>
                        </div>

                        <button class="btn btn-primary" id="btn-run-simulation" style="width: 100%; margin-top: var(--space-2);">
                            <i class="fa-solid fa-play"></i> Run What-If Simulation
                        </button>
                    </div>
                </div>
            `;

            // Bind labels updates
            const bindLabel = (inputId, labelId) => {
                const input = document.getElementById(inputId);
                const label = document.getElementById(labelId);
                if (input && label) {
                    input.addEventListener("input", (e) => {
                        label.textContent = e.target.value;
                    });
                }
            };
            bindLabel("sim-fuel-factor", "lbl-fuel-factor");
            bindLabel("sim-driver-factor", "lbl-driver-factor");
            bindLabel("sim-vol-factor", "lbl-vol-factor");

            // Bind simulate trigger
            document.getElementById("btn-run-simulation").addEventListener("click", () => {
                const fuel = parseFloat(document.getElementById("sim-fuel-factor").value);
                const driver = parseFloat(document.getElementById("sim-driver-factor").value);
                const vol = parseFloat(document.getElementById("sim-vol-factor").value);
                const mode = document.getElementById("sim-mode").value;
                const closeRoute = document.getElementById("sim-close-route").value;
                const disruption = document.getElementById("sim-disruption").checked;

                if (onSimulateCallback) {
                    onSimulateCallback({
                        fuel_multiplier: fuel,
                        driver_multiplier: driver,
                        volume_multiplier: vol,
                        transport_mode: mode,
                        close_routes: closeRoute ? [closeRoute] : [],
                        emergency_disruption: disruption
                    });
                }
            });
        },

        populateCorridors(corridors) {
            const select = document.getElementById("sim-close-route");
            if (!select) return;

            select.innerHTML = `<option value="">-- No Closures --</option>`;
            corridors.forEach(c => {
                const opt = document.createElement("option");
                const val = `${c.origin} -> ${c.destination}`;
                opt.value = val;
                opt.textContent = val;
                select.appendChild(opt);
            });
        }
    };
    window.ScenarioBuilder = ScenarioBuilder;
})();
