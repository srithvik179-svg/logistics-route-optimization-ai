/**
 * Widget Component helper
 * Provides draggable titlebars, resizable border anchors, collapse panels, and fullscreen triggers.
 */
(function() {
    const Widget = {
        makeDraggable(widgetEl, onDropCallback) {
            const header = widgetEl.querySelector(".widget-header");
            if (!header) return;
            
            // Set draggable properties
            widgetEl.setAttribute("draggable", "true");
            
            widgetEl.addEventListener("dragstart", (e) => {
                widgetEl.classList.add("dragging");
                e.dataTransfer.setData("text/plain", widgetEl.id);
                e.dataTransfer.effectAllowed = "move";
            });
            
            widgetEl.addEventListener("dragend", () => {
                widgetEl.classList.remove("dragging");
                document.querySelectorAll(".widget-card").forEach(w => w.classList.remove("drag-over"));
            });
            
            widgetEl.addEventListener("dragover", (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = "move";
                if (!widgetEl.classList.contains("dragging")) {
                    widgetEl.classList.add("drag-over");
                }
            });
            
            widgetEl.addEventListener("dragleave", () => {
                widgetEl.classList.remove("drag-over");
            });
            
            widgetEl.addEventListener("drop", (e) => {
                e.preventDefault();
                widgetEl.classList.remove("drag-over");
                
                const draggedId = e.dataTransfer.getData("text/plain");
                const draggedEl = document.getElementById(draggedId);
                
                if (draggedEl && draggedEl !== widgetEl) {
                    if (onDropCallback) onDropCallback(draggedEl, widgetEl);
                }
            });
        },
        
        makeResizable(widgetEl, onResizeCallback) {
            if (widgetEl.querySelector(".widget-resize-handle")) return;
            
            const handle = document.createElement("div");
            handle.className = "widget-resize-handle";
            widgetEl.appendChild(handle);
            
            let startX, startWidth, startSpan;
            
            handle.addEventListener("mousedown", (e) => {
                startX = e.pageX;
                startWidth = widgetEl.offsetWidth;
                
                // Get current column span (default is 1)
                const gridColumn = window.getComputedStyle(widgetEl).gridColumnStart;
                startSpan = gridColumn && gridColumn.includes("span") 
                    ? parseInt(gridColumn.replace("span", "").trim()) 
                    : 1;
                
                const onMouseMove = (moveEvent) => {
                    const deltaX = moveEvent.pageX - startX;
                    const containerWidth = widgetEl.parentElement.offsetWidth;
                    const oneColumnWidth = containerWidth / 3; // assume 3 cols grid
                    
                    let newSpan = startSpan + Math.round(deltaX / oneColumnWidth);
                    newSpan = Math.max(1, Math.min(3, newSpan)); // clamp between 1 and 3 cols
                    
                    widgetEl.style.gridColumn = `span ${newSpan}`;
                };
                
                const onMouseUp = () => {
                    document.removeEventListener("mousemove", onMouseMove);
                    document.removeEventListener("mouseup", onMouseUp);
                    
                    // Trigger Plotly charts resize inside
                    const chart = widgetEl.querySelector(".plotly-graph-div, [id^='chart-'], [id^='exec-']");
                    if (chart && typeof Plotly !== "undefined") {
                        Plotly.Plots.resize(chart.id);
                    }
                    
                    if (onResizeCallback) onResizeCallback(widgetEl);
                };
                
                document.addEventListener("mousemove", onMouseMove);
                document.addEventListener("mouseup", onMouseUp);
                e.stopPropagation();
                e.preventDefault();
            });
        }
    };
    window.Widget = Widget;
})();
