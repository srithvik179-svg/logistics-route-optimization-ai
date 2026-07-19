/**
 * PromptSuggestions Component
 * Renders quick-select prompt buttons for planners to click and ask standard questions.
 */
(function() {
    const SUGGESTED_PROMPTS = [
        "Show network health overview",
        "Predict SLA breach risk",
        "Explain AI orchestrator workflows",
        "Check reverse logistics metrics",
        "Evaluate corridor bottlenecks",
        "Generate cost savings report"
    ];

    const PromptSuggestions = {
        render(containerId, onSelect) {
            const container = document.getElementById(containerId);
            if (!container) return;

            container.innerHTML = `
                <div style="font-family:sans-serif; margin-bottom:var(--space-4);">
                    <div style="font-size:10px; color:var(--text-muted); text-transform:uppercase; margin-bottom:6px; font-weight:bold;">
                        Suggested Copilot Prompts
                    </div>
                    <div style="display:flex; flex-wrap:wrap; gap:8px;">
                        ${SUGGESTED_PROMPTS.map((p, idx) => `
                            <button class="btn btn-secondary btn-sm prompt-pill-btn" onclick="PromptSuggestions.clickPrompt(${idx})">
                                <i class="fa-regular fa-lightbulb text-warning" style="margin-right:4px;"></i> ${p}
                            </button>
                        `).join('')}
                    </div>
                </div>
            `;

            // Store select callback
            this._onSelect = onSelect;

            if (!document.getElementById("prompt-suggestion-styles")) {
                const style = document.createElement("style");
                style.id = "prompt-suggestion-styles";
                style.textContent = `
                    .prompt-pill-btn {
                        font-size: 10px !important; padding: 6px 10px !important;
                        background: rgba(9, 9, 11, 0.4) !important;
                        border: 1px solid rgba(63, 63, 70, 0.3) !important;
                        border-radius: 20px !important; color: var(--text-secondary) !important;
                        transition: all 0.2s ease !important; cursor: pointer;
                    }
                    .prompt-pill-btn:hover {
                        background: rgba(59, 130, 246, 0.1) !important;
                        border-color: rgba(59, 130, 246, 0.4) !important;
                        color: #fff !important;
                    }
                `;
                document.head.appendChild(style);
            }
        },

        clickPrompt(idx) {
            if (typeof this._onSelect === "function") {
                this._onSelect(SUGGESTED_PROMPTS[idx]);
            }
        }
    };

    window.PromptSuggestions = PromptSuggestions;
})();
