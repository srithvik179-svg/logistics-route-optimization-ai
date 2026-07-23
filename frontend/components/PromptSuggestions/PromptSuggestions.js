/**
 * PromptSuggestions Component
 * Renders quick-select prompt action cards for enterprise planners to ask natural language questions.
 */
(function() {
    const SUGGESTED_PROMPTS = [
        "Which hub has the most SLA breaches?",
        "Top Cost Saving Opportunities",
        "Which routes generate the highest logistics cost?",
        "Which repair center is overloaded?",
        "Current SLA Breach Risks",
        "Which parts experience the most delays?",
        "Reverse Logistics Summary",
        "Carbon Impact & Sustainability",
        "Warehouse Inventory & Utilization",
        "Which routes should be optimized first?",
        "Show redeployment opportunities",
        "Executive Business Summary"
    ];

    const PromptSuggestions = {
        render(containerId, onSelect) {
            const container = document.getElementById(containerId);
            if (!container) return;

            container.innerHTML = `
                <div style="font-family:sans-serif; margin-bottom:var(--space-3);">
                    <div style="font-size:10px; color:var(--text-muted); text-transform:uppercase; margin-bottom:8px; font-weight:bold; letter-spacing:0.5px;">
                        💡 Quick Action Prompts (Click to ask)
                    </div>
                    <div style="display:flex; flex-wrap:wrap; gap:6px;">
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
                        font-size: 10px !important; padding: 6px 12px !important;
                        background: rgba(18, 18, 22, 0.6) !important;
                        border: 1px solid rgba(63, 63, 70, 0.4) !important;
                        border-radius: 20px !important; color: var(--text-secondary) !important;
                        transition: all 0.2s ease !important; cursor: pointer;
                    }
                    .prompt-pill-btn:hover {
                        background: rgba(59, 130, 246, 0.15) !important;
                        border-color: rgba(59, 130, 246, 0.5) !important;
                        color: #fff !important;
                        transform: translateY(-1px);
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
