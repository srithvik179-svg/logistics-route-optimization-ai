/**
 * EmptyState UI helper
 * Injects beautiful icons and descriptions.
 */
(function() {
    const EmptyState = {
        render(containerId, title = "No data available", desc = "Upload logistics data to begin", icon = "fa-folder-open", actionText = "", actionFn = null) {
            const container = document.getElementById(containerId);
            if (!container) return;
            
            let buttonHtml = "";
            if (actionText && actionFn) {
                const fnName = `empty_action_${containerId.replace(/-/g, '_')}`;
                window[fnName] = actionFn;
                buttonHtml = `<button class="btn btn-primary btn-sm" onclick="window.${fnName}()" style="margin-top: var(--space-4);"><i class="fa-solid fa-arrow-rotate-right"></i> ${actionText}</button>`;
            }
            
            container.innerHTML = `
                <div class="empty-state-container">
                    <div class="empty-state-icon">
                        <i class="fa-solid ${icon}"></i>
                    </div>
                    <h4 class="empty-state-title">${title}</h4>
                    <p class="empty-state-desc">${desc}</p>
                    ${buttonHtml}
                </div>
            `;
        }
    };
    window.EmptyState = EmptyState;
})();
