/**
 * ForecastTimeline Component
 * 7-day rolling risk timeline + Plotly charts (risk distribution pie, hub bar, delay forecast line).
 */
(function() {
    const ForecastTimeline = {
        renderTimeline(containerId, timeline, peakDay) {
            const el = document.getElementById(containerId);
            if (!el || !timeline) return;

            const RISK_COLORS = {
                "Very Low": "#10b981", "Low": "#06b6d4",
                "Moderate": "#f59e0b", "High": "#f97316", "Critical": "#ef4444"
            };

            const days = timeline.map(t => `
                <div style="display:flex;flex-direction:column;align-items:center;gap:4px;flex:1;min-width:60px;">
                    <span style="font-size:9px;color:var(--text-muted);text-transform:uppercase;">${t.day_name}</span>
                    <div style="width:36px;height:${Math.max(12, t.projected_miss_rate * 1.2)}px;
                                background:${RISK_COLORS[t.risk_level]};border-radius:4px 4px 0 0;
                                transition:height 0.4s ease;"
                         title="${t.projected_miss_rate}% miss rate"></div>
                    <span style="font-size:9px;color:${RISK_COLORS[t.risk_level]};font-weight:600;">${t.projected_miss_rate}%</span>
                    <span style="font-size:9px;color:var(--text-muted);">${t.date.slice(5)}</span>
                    ${t.day_name === peakDay ? `<span style="font-size:8px;color:#ef4444;font-weight:700;">PEAK</span>` : ""}
                </div>`).join("");

            el.innerHTML = `
                <div class="card glass-panel fade-in-slide-up">
                    <div class="card-header" style="display:flex;justify-content:space-between;align-items:center;">
                        <h3><i class="fa-solid fa-chart-line text-primary"></i> 7-Day Risk Forecast Timeline</h3>
                        <span style="font-size:10px;color:var(--text-muted);">Peak risk day: <strong style="color:#ef4444;">${peakDay}</strong></span>
                    </div>
                    <div class="card-body" style="padding:var(--space-4);">
                        <div style="display:flex;gap:var(--space-4);align-items:flex-end;justify-content:space-around;height:140px;padding:0 var(--space-2);">
                            ${days}
                        </div>
                    </div>
                </div>`;
        },

        renderCharts(charts) {
            if (!charts) return;

            // Risk distribution donut
            if (charts.risk_distribution_pie && document.getElementById("sla-pie-chart")) {
                Plotly.newPlot("sla-pie-chart", [{
                    type: "pie", hole: 0.55,
                    labels: charts.risk_distribution_pie.labels,
                    values: charts.risk_distribution_pie.values,
                    marker: { colors: ["#10b981","#06b6d4","#f59e0b","#f97316","#ef4444"] },
                    textinfo: "none", hoverinfo: "label+value+percent"
                }], {
                    paper_bgcolor: "transparent", showlegend: true,
                    legend: { font: { color: "#a1a1aa", size: 9 }, orientation: "h" },
                    margin: { t:10, b:20, l:10, r:10 }, height: 220
                }, { displayModeBar: false });
            }

            // Hub risk bar
            if (charts.hub_risk_bar && document.getElementById("sla-hub-bar")) {
                Plotly.newPlot("sla-hub-bar", [{
                    type: "bar",
                    x: charts.hub_risk_bar.hubs,
                    y: charts.hub_risk_bar.scores,
                    marker: { color: charts.hub_risk_bar.colors },
                    hoverinfo: "x+y"
                }], {
                    paper_bgcolor: "transparent", plot_bgcolor: "transparent",
                    font: { color: "#a1a1aa", size: 9 },
                    xaxis: { gridcolor: "rgba(63,63,70,0.2)" },
                    yaxis: { gridcolor: "rgba(63,63,70,0.2)", range: [0, 100] },
                    margin: { t:10, b:30, l:30, r:10 }, height: 220
                }, { displayModeBar: false });
            }

            // Delay forecast line
            if (charts.delay_forecast_line && document.getElementById("sla-delay-line")) {
                const df = charts.delay_forecast_line;
                Plotly.newPlot("sla-delay-line", [
                    {
                        name: "Breach %",
                        x: df.shipments, y: df.breach_probs,
                        type: "scatter", mode: "lines+markers",
                        line: { color: "#ef4444", width: 2 },
                        marker: { size: 5 }
                    },
                    {
                        name: "Delay (h)",
                        x: df.shipments, y: df.delays,
                        type: "scatter", mode: "lines",
                        line: { color: "#f97316", width: 2, dash: "dot" },
                        yaxis: "y2"
                    }
                ], {
                    paper_bgcolor: "transparent", plot_bgcolor: "transparent",
                    font: { color: "#a1a1aa", size: 9 },
                    xaxis: { gridcolor: "rgba(63,63,70,0.15)", tickangle: -25, tickfont: { size: 8 } },
                    yaxis:  { gridcolor: "rgba(63,63,70,0.15)", title: { text: "Breach %", font: { size: 8 } } },
                    yaxis2: { overlaying: "y", side: "right", title: { text: "Delay h", font: { size: 8 } } },
                    legend: { font: { color: "#a1a1aa", size: 9 } },
                    margin: { t: 10, b: 50, l: 35, r: 35 }, height: 220
                }, { displayModeBar: false });
            }
        }
    };
    window.ForecastTimeline = ForecastTimeline;
})();
