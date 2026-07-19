/**
 * ErrorState UI helper
 * Injects standard reload buttons and warning parameters.
 */
(function() {
    const ErrorState = {
        render(containerId, errorType = "API Timeout", desc = "The server is taking too long to respond. Please retry.", retryFn = null) {
            const container = document.getElementById(containerId);
            if (!container) return;
            
            let icon = "fa-circle-exclamation";
            if (errorType === "Connection Error") icon = "fa-wifi";
            else if (errorType === "Dataset Missing") icon = "fa-file-excel";
            else if (errorType === "Permission Denied") icon = "fa-shield-halved";
            
            let buttonHtml = "";
            if (retryFn) {
                const fnName = `error_retry_${containerId.replace(/-/g, '_')}`;
                window[fnName] = retryFn;
                buttonHtml = `<button class="btn btn-secondary btn-sm" onclick="window.${fnName}()" style="margin-top: var(--space-4);"><i class="fa-solid fa-arrow-rotate-right"></i> Retry Operation</button>`;
            }
            
            container.innerHTML = `
                <div class="error-state-container">
                    <div class="error-state-icon">
                        <i class="fa-solid ${icon}"></i>
                    </div>
                    <h4 class="error-state-title">${errorType}</h4>
                    <p class="error-state-desc">${desc}</p>
                    ${buttonHtml}
                </div>
            `;
        },
        
        renderTableError(tbodyId, colspan = 5, errorType = "API Error", desc = "Failed to load records.", retryFn = null) {
            const tbody = document.getElementById(tbodyId);
            if (!tbody) return;
            
            let icon = "fa-triangle-exclamation";
            if (errorType === "Connection Error") icon = "fa-wifi";
            
            let buttonHtml = "";
            if (retryFn) {
                const fnName = `table_retry_${tbodyId.replace(/-/g, '_')}`;
                window[fnName] = retryFn;
                buttonHtml = `<button class="btn btn-secondary btn-sm" onclick="window.${fnName}()" style="margin-top: var(--space-2);"><i class="fa-solid fa-arrow-rotate-right"></i> Retry</button>`;
            }
            
            tbody.innerHTML = `
                <tr>
                    <td colspan="${colspan}" class="text-center" style="padding: 3rem 1.5rem;">
                        <div style="color: var(--danger-color); font-size: 2rem; margin-bottom: var(--space-2);">
                            <i class="fa-solid ${icon}"></i>
                        </div>
                        <h5 style="margin: 0 0 var(--space-1) 0; font-family: var(--font-heading); color: var(--text-primary); font-size: var(--font-size-sm);">${errorType}</h5>
                        <p style="margin: 0; color: var(--text-secondary); font-size: var(--font-size-xs);">${desc}</p>
                        ${buttonHtml}
                    </td>
                </tr>
            `;
        },
        
        renderMapError(mapContainerId, errorMsg = "Unable to connect to map services.", retryFn = null) {
            const container = document.getElementById(mapContainerId);
            if (!container) return;
            
            let overlay = container.querySelector(".map-loading-overlay");
            if (!overlay) {
                overlay = document.createElement("div");
                overlay.className = "map-loading-overlay";
                container.appendChild(overlay);
            }
            
            let buttonHtml = "";
            if (retryFn) {
                const fnName = `map_retry_${mapContainerId.replace(/-/g, '_')}`;
                window[fnName] = retryFn;
                buttonHtml = `<button class="btn btn-primary btn-sm" onclick="window.${fnName}()" style="margin-top: var(--space-3);"><i class="fa-solid fa-arrow-rotate-right"></i> Retry</button>`;
            }
            
            overlay.innerHTML = `
                <div class="error-state-container" style="background: rgba(20, 20, 25, 0.95); margin: 0; padding: 2rem; border-color: rgba(244, 63, 94, 0.3);">
                    <div class="error-state-icon" style="font-size: 2rem;"><i class="fa-solid fa-wifi"></i></div>
                    <h4 class="error-state-title" style="font-size: var(--font-size-md);">Network Map Offline</h4>
                    <p class="error-state-desc" style="font-size: var(--font-size-xs);">${errorMsg}</p>
                    ${buttonHtml}
                </div>
            `;
            overlay.style.display = "flex";
        }
    };
    window.ErrorState = ErrorState;
})();
