/**
 * CommandPalette Component
 * Keyboard-driven shortcut menu command palette overlay (Ctrl+K or Cmd+K).
 */
(function() {
    const CommandPalette = {
        render() {
            // Check if overlay already exists
            if (document.getElementById("command-palette-overlay")) return;

            const overlay = document.createElement("div");
            overlay.id = "command-palette-overlay";
            overlay.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background: rgba(9, 9, 11, 0.85); backdrop-filter: blur(4px);
                z-index: 999999; display: flex; align-items: center; justify-content: center;
                animation: fadeIn 0.2s ease; font-family: sans-serif;
            `;

            overlay.innerHTML = `
                <div class="card glass-panel" style="width: 100%; max-width: 500px; padding: var(--space-4); border: 1px solid rgba(63, 63, 70, 0.6); box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);">
                    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(63, 63, 70, 0.4); padding-bottom:var(--space-2); margin-bottom:var(--space-3);">
                        <h3 style="margin:0; font-size:var(--font-size-md); color:#fff;"><i class="fa-solid fa-terminal text-primary"></i> Command Menu Palette</h3>
                        <kbd style="background:#27272a; border:1px solid #3f3f46; color:#a1a1aa; padding:2px 6px; border-radius:4px; font-size:10px;">ESC</kbd>
                    </div>
                    <div style="display:flex; flex-direction:column; gap:var(--space-2);">
                        <div style="font-size:10px; color:var(--text-muted); text-transform:uppercase; margin-bottom:4px;">NAVIGATE WORKSPACES</div>
                        <div class="palette-item" onclick="CommandPalette.select('route-section')">
                            <span><i class="fa-solid fa-compass"></i> Go to Route optimization Workspace</span>
                            <kbd>1</kbd>
                        </div>
                        <div class="palette-item" onclick="CommandPalette.select('corridor-section')">
                            <span><i class="fa-solid fa-chart-line"></i> Go to Corridor Efficiency Dashboard</span>
                            <kbd>2</kbd>
                        </div>
                        <div class="palette-item" onclick="CommandPalette.select('optimization-section')">
                            <span><i class="fa-solid fa-calculator"></i> Go to Cost What-If Simulator</span>
                            <kbd>3</kbd>
                        </div>
                        <div class="palette-item" onclick="CommandPalette.select('reverse-section')">
                            <span><i class="fa-solid fa-rotate-left"></i> Go to Reverse Logistics platform</span>
                            <kbd>4</kbd>
                        </div>
                        <div class="palette-item" onclick="CommandPalette.select('sla-section')">
                            <span><i class="fa-solid fa-hourglass-half"></i> Go to SLA prediction Console</span>
                            <kbd>5</kbd>
                        </div>
                        <div class="palette-item" onclick="CommandPalette.select('orchestrator-section')">
                            <span><i class="fa-solid fa-network-wired"></i> Go to AI Orchestrator Workspace</span>
                            <kbd>6</kbd>
                        </div>
                        <div class="palette-item" onclick="CommandPalette.select('reports-section')">
                            <span><i class="fa-solid fa-file-invoice"></i> Go to Reports Center</span>
                            <kbd>7</kbd>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(overlay);

            // Add CSS styling inside style tag safely
            if (!document.getElementById("palette-styles")) {
                const style = document.createElement("style");
                style.id = "palette-styles";
                style.textContent = `
                    .palette-item {
                        display: flex; justify-content: space-between; align-items: center;
                        padding: 10px 12px; background: rgba(9, 9, 11, 0.4);
                        border: 1px solid rgba(63, 63, 70, 0.2); border-radius: 6px;
                        cursor: pointer; font-size: 11px; color: var(--text-secondary);
                        transition: all 0.2s ease;
                    }
                    .palette-item:hover {
                        background: rgba(59, 130, 246, 0.1); border-color: rgba(59, 130, 246, 0.4);
                        color: #fff;
                    }
                    .palette-item kbd {
                        background: #27272a; border: 1px solid #3f3f46; color: #a1a1aa;
                        padding: 1px 5px; border-radius: 3px; font-size: 9px;
                    }
                `;
                document.head.appendChild(style);
            }

            // Keyboard listener for ESC
            overlay.addEventListener("click", (e) => {
                if (e.target === overlay) CommandPalette.close();
            });
        },

        close() {
            const el = document.getElementById("command-palette-overlay");
            if (el) el.remove();
        },

        select(sectionId) {
            this.close();
            const link = document.querySelector(`.nav-link[data-target="${sectionId}"]`);
            if (link) {
                link.click();
            }
        }
    };

    // Hotkey listener Ctrl+K or Cmd+K
    window.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "k") {
            e.preventDefault();
            CommandPalette.render();
        }
        if (e.key === "Escape") {
            CommandPalette.close();
        }
    });

    window.toggleCommandPalette = function() {
        CommandPalette.render();
    };

    window.CommandPalette = CommandPalette;
})();
