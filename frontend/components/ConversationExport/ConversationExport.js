/**
 * ConversationExport Component
 * Handles formatting and downloading the active conversation log history as JSON or CSV.
 */
(function() {
    const ConversationExport = {
        render(containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;

            container.innerHTML = `
                <div class="card glass-panel" style="padding:var(--space-3); border:1px solid rgba(63,63,70,0.4); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:var(--space-2);">
                    <span style="font-size:11px; color:var(--text-muted);"><i class="fa-solid fa-file-export"></i> Export Chat Log:</span>
                    <div style="display:flex; gap:var(--space-2);">
                        <button class="btn btn-secondary btn-sm" onclick="ConversationExport.downloadJSON()"><i class="fa-solid fa-file-code"></i> Export JSON</button>
                        <button class="btn btn-secondary btn-sm" onclick="ConversationExport.downloadCSV()"><i class="fa-solid fa-file-csv"></i> Export CSV</button>
                    </div>
                </div>
            `;
        },

        async downloadJSON() {
            try {
                const res = await fetch("/api/copilot/history/export");
                if (!res.ok) throw new Error("Failed to fetch export payload");
                const data = await res.json();

                const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `copilot_chat_export_${Date.now()}.json`;
                a.click();
            } catch(e) {
                console.error("Failed to export JSON:", e);
                alert("Failed to export conversation.");
            }
        },

        async downloadCSV() {
            try {
                const res = await fetch("/api/copilot/history/export");
                if (!res.ok) throw new Error("Failed to fetch export payload");
                const data = await res.json();

                // Format simple CSV
                let csv = "Timestamp,Role,Message\n";
                data.forEach(msg => {
                    const cleanMsg = msg.message.replace(/"/g, '""');
                    csv += `"${msg.timestamp}","${msg.role}","${cleanMsg}"\n`;
                });

                const blob = new Blob([csv], { type: "text/csv" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `copilot_chat_export_${Date.now()}.csv`;
                a.click();
            } catch(e) {
                console.error("Failed to export CSV:", e);
                alert("Failed to export conversation.");
            }
        }
    };

    window.ConversationExport = ConversationExport;
})();
