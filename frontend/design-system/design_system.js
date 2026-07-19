/**
 * Design System Interactive Engine & Observability Logger
 * Handles page transitions, KPI animated counters, micro-interactions, and required design system logging.
 */
(function() {
    // Flag to prevent double loading
    if (window.__DesignSystemLoaded) return;
    window.__DesignSystemLoaded = true;

    // Direct output logging required by Phase 36 Specifications
    console.log("[Design System] Design System Loaded");
    console.log("[Design System] Theme Applied");

    document.addEventListener("DOMContentLoaded", () => {
        initPageTransitions();
        initKpiCounters();
        initFocusRingHelper();
        setupObserverForRenderLogs();
        console.log("[Design System] UI Components Rendered");
    });

    /**
     * Set up MutationObserver to track DOM changes and log 'Layout Updated' and 'UI Components Rendered'
     */
    function setupObserverForRenderLogs() {
        // Log whenever layout target section is activated or navigation click happens
        const navLinks = document.querySelectorAll(".nav-link");
        navLinks.forEach(link => {
            link.addEventListener("click", () => {
                // Layout updated log triggered on navigation
                setTimeout(() => {
                    console.log("[Design System] Layout Updated");
                    console.log("[Design System] UI Components Rendered");
                    initKpiCounters(); // Re-trigger KPI animations for newly loaded view
                }, 50);
            });
        });
        
        // Also observe section activation
        const observer = new MutationObserver((mutations) => {
            let layoutUpdated = false;
            mutations.forEach(mutation => {
                if (mutation.attributeName === "class" && mutation.target.classList.contains("viewport-section")) {
                    layoutUpdated = True;
                }
            });
            if (layoutUpdated) {
                console.log("[Design System] Layout Updated");
                console.log("[Design System] UI Components Rendered");
            }
        });

        const sections = document.querySelectorAll(".viewport-section");
        sections.forEach(s => observer.observe(s, { attributes: true }));
    }

    /**
     * Interactive KPI Number Animation Counter.
     * Counts up from 0 (or a starting point) to the final loaded value.
     */
    function initKpiCounters() {
        const kpiElements = document.querySelectorAll(".kpi-card .kpi-value, .kpi-value-large, .metric-value, .stat-value");
        kpiElements.forEach(el => {
            if (el.dataset.counterInitialized) return;
            
            const rawText = el.textContent.trim();
            // Parse numerical part out of currency ($2,382.00), days (2.0 Days), percent (98%), or count (11)
            const cleanNumStr = rawText.replace(/[^\d.-]/g, '');
            const targetVal = parseFloat(cleanNumStr);
            
            if (isNaN(targetVal)) return; // Skip if no parsable number
            
            el.dataset.counterInitialized = "true";
            el.style.opacity = "0.7"; // slight fade during count
            
            const isCurrency = rawText.startsWith("$");
            const isPercent = rawText.endsWith("%");
            const isDays = rawText.toLowerCase().includes("day");
            const hasDecimals = cleanNumStr.includes(".");
            
            let start = 0;
            const duration = 800; // ms animation duration
            const startTime = performance.now();
            
            function updateCounter(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                // Ease-out quad formula
                const easeProgress = progress * (2 - progress);
                const currentVal = start + easeProgress * (targetVal - start);
                
                // Format appropriately
                let formatted = "";
                if (isCurrency) {
                    formatted = "$" + currentVal.toLocaleString('en-US', {
                        minimumFractionDigits: hasDecimals ? 2 : 0,
                        maximumFractionDigits: hasDecimals ? 2 : 0
                    });
                } else if (isPercent) {
                    formatted = currentVal.toFixed(hasDecimals ? 1 : 0) + "%";
                } else if (isDays) {
                    formatted = currentVal.toFixed(hasDecimals ? 1 : 0) + " Days";
                } else {
                    formatted = Math.floor(currentVal).toLocaleString('en-US');
                }
                
                el.textContent = formatted;
                
                if (progress < 1) {
                    requestAnimationFrame(updateCounter);
                } else {
                    el.textContent = rawText; // Set back original string exactly (retains decimals/text)
                    el.style.opacity = "1";
                }
            }
            requestAnimationFrame(updateCounter);
        });
    }

    /**
     * Page transitions utility to smoothly reveal pages.
     */
    function initPageTransitions() {
        const sections = document.querySelectorAll(".viewport-section");
        sections.forEach(s => {
            s.style.transition = "opacity 0.2s ease-in-out, transform 0.2s ease-in-out";
            s.style.opacity = s.classList.contains("active") ? "1" : "0";
            s.style.transform = s.classList.contains("active") ? "translateY(0)" : "translateY(8px)";
        });

        // Hook navigation click transitions
        const originalActive = document.querySelector(".viewport-section.active");
        if (originalActive) {
            originalActive.style.opacity = "1";
            originalActive.style.transform = "translateY(0)";
        }
        
        // Listen for visibility switches
        const observer = new MutationObserver((mutations) => {
            mutations.forEach(mutation => {
                if (mutation.attributeName === "class") {
                    const target = mutation.target;
                    if (target.classList.contains("active")) {
                        target.style.opacity = "0";
                        target.style.transform = "translateY(8px)";
                        // Force reflow
                        target.offsetHeight;
                        target.style.opacity = "1";
                        target.style.transform = "translateY(0)";
                    } else {
                        target.style.opacity = "0";
                        target.style.transform = "translateY(8px)";
                    }
                }
            });
        });
        
        sections.forEach(s => observer.observe(s, { attributes: true }));
    }

    /**
     * Accessibility focus ring helper.
     * Only shows focus outline when navigating with keyboard, keeping click interactions clean.
     */
    function initFocusRingHelper() {
        window.addEventListener("keydown", (e) => {
            if (e.key === "Tab") {
                document.body.classList.add("keyboard-user");
            }
        });
        
        window.addEventListener("mousedown", () => {
            document.body.classList.remove("keyboard-user");
        });
    }
})();
