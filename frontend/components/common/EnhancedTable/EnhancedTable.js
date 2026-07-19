/**
 * EnhancedTable helper component
 * Adds sorting indicators, resizing handles, and sticky header rules.
 */
(function() {
    const EnhancedTable = {
        init(tableOrSelector) {
            const table = typeof tableOrSelector === "string"
                ? document.querySelector(tableOrSelector)
                : tableOrSelector;
            if (!table) return;
            
            table.classList.add("enhanced-data-table");
            
            // Add column resize handles
            const headers = table.querySelectorAll("th");
            headers.forEach((th, idx) => {
                if (th.querySelector(".resize-handle")) return;
                
                const handle = document.createElement("span");
                handle.className = "resize-handle";
                th.appendChild(handle);
                
                let startX, startWidth;
                handle.addEventListener("mousedown", (e) => {
                    startX = e.pageX;
                    startWidth = th.offsetWidth;
                    
                    const onMouseMove = (moveEvent) => {
                        const width = startWidth + (moveEvent.pageX - startX);
                        th.style.width = width + "px";
                        th.style.minWidth = width + "px";
                    };
                    
                    const onMouseUp = () => {
                        document.removeEventListener("mousemove", onMouseMove);
                        document.removeEventListener("mouseup", onMouseUp);
                    };
                    
                    document.addEventListener("mousemove", onMouseMove);
                    document.addEventListener("mouseup", onMouseUp);
                    e.stopPropagation();
                    e.preventDefault();
                });
            });
        }
    };
    window.EnhancedTable = EnhancedTable;
})();
