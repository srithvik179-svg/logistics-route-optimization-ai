/**
 * ExecutionTimeline Component
 * Visualizes the agent execution speed and sequence timings.
 */
(function() {
    const ExecutionTimeline = {
        render(containerId, executionSteps) {
            const el = document.getElementById(containerId);
            if (!el) return;

            if (!executionSteps || !executionSteps.length) {
                el.innerHTML = `
                    <div class="card glass-panel" style="height:100%; display:flex; align-items:center; justify-content:center; padding:var(--space-6); color:var(--text-muted); font-size:11px;">
                        Waiting for workflow logs...
                    </div>`;
                return;
            }

            el.innerHTML = `
                <div class="card glass-panel fade-in-slide-up" style="height:100%;">
                    <div class="card-header">
                        <h3><i class="fa-solid fa-timeline text-primary"></i> Agent Processing Latencies</h3>
                    </div>
                    <div class="card-body" style="padding:var(--space-2);">
                        <div id="execution-chart" style="width:100%; height:200px;"></div>
                    </div>
                </div>
            `;

            const labels = executionSteps.map(s => s.name);
            const values = executionSteps.map(s => s.duration_ms);

            Plotly.newPlot("execution-chart", [{
                type: "bar",
                x: values,
                y: labels,
                orientation: "h",
                marker: {
                    color: "#10b981",
                    opacity: 0.85
                },
                hoverinfo: "x"
            }], {
                paper_bgcolor: "transparent",
                plot_bgcolor: "transparent",
                font: { color: "#a1a1aa", size: 8 },
                xaxis: { gridcolor: "rgba(63,63,70,0.2)", title: { text: "Duration (ms)", font: { size: 9 } } },
                yaxis: { automargin: true },
                margin: { t: 10, b: 30, l: 120, r: 10 },
                height: 200
            }, { displayModeBar: false });
        }
    };
    window.ExecutionTimeline = ExecutionTimeline;
})();
