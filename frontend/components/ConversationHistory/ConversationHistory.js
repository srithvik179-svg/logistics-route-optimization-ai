/**
 * ConversationHistory Component
 * Lists active session chat logs, allows pinning, favoriting, or clearing conversation steps.
 */
(function() {
    let _history = [];

    const ConversationHistory = {
        render(containerId, historyData = []) {
            const container = document.getElementById(containerId);
            if (!container) return;

            _history = historyData;

            container.innerHTML = `
                <div class="card glass-panel" style="padding:var(--space-3); border:1px solid rgba(63,63,70,0.4); display:flex; flex-direction:column; gap:6px; max-height:400px; overflow-y:auto;">
                    <div style="font-size:11px; font-weight:bold; color:#fff; text-transform:uppercase; display:flex; justify-content:space-between; align-items:center;">
                        <span><i class="fa-solid fa-clock-rotate-left text-primary"></i> Chat Logs & Pins</span>
                        <button class="btn btn-secondary btn-sm" onclick="ConversationHistory.clearLogs()" style="font-size:9px; padding:1px 5px; border:none;">
                            Clear All
                        </button>
                    </div>
                    <div style="display:flex; flex-direction:column; gap:4px; margin-top:2px;" id="history-items-list">
                        ${_history.length === 0 
                            ? `<div style="font-size:10px; color:var(--text-muted); text-align:center; padding:10px;">No messages logged yet.</div>`
                            : _history.filter(m => m.role === "user").map(msg => `
                                <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(9,9,11,0.4); padding:6px; border-radius:4px; border:1px solid rgba(63,63,70,0.1);">
                                    <span style="font-size:10px; color:#fff; cursor:pointer;" onclick="ConversationHistory.recall('${msg.message.replace(/'/g, "\\'")}')">
                                        <i class="fa-solid fa-message text-muted" style="margin-right:4px;"></i> ${msg.message}
                                    </span>
                                    <div style="display:flex; gap:4px;">
                                        <button class="btn btn-secondary btn-sm" onclick="ConversationHistory.toggleFavorite('${msg.id}')" style="padding:1px 4px; font-size:8px; border:none;" title="Favorite">
                                            <i class="${msg.favorite ? 'fa-solid text-warning' : 'fa-regular'} fa-star"></i>
                                        </button>
                                        <button class="btn btn-secondary btn-sm" onclick="ConversationHistory.togglePin('${msg.id}')" style="padding:1px 4px; font-size:8px; border:none;" title="Pin">
                                            <i class="${msg.pinned ? 'fa-solid text-primary' : 'fa-solid text-muted'} fa-thumbtack"></i>
                                        </button>
                                    </div>
                                </div>
                            `).join('')
                        }
                    </div>
                </div>
            `;
        },

        async togglePin(msgId) {
            try {
                const res = await fetch("/api/copilot/message/pin", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message_id: msgId })
                });
                if (res.ok) {
                    // Refresh view
                    if (window.loadCopilotWorkspace) window.loadCopilotWorkspace();
                }
            } catch(e) {
                console.error("Failed to pin message:", e);
            }
        },

        async toggleFavorite(msgId) {
            try {
                const res = await fetch("/api/copilot/message/favorite", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message_id: msgId })
                });
                if (res.ok) {
                    // Refresh view
                    if (window.loadCopilotWorkspace) window.loadCopilotWorkspace();
                }
            } catch(e) {
                console.error("Failed to favorite message:", e);
            }
        },

        async clearLogs() {
            if (!confirm("Are you sure you want to clear your conversation history?")) return;
            try {
                const res = await fetch("/api/copilot/history/clear", { method: "POST" });
                if (res.ok) {
                    if (window.loadCopilotWorkspace) window.loadCopilotWorkspace();
                }
            } catch(e) {
                console.error("Failed to clear chat logs:", e);
            }
        },

        recall(text) {
            const input = document.getElementById("copilot-chat-input");
            if (input) {
                input.value = text;
                input.focus();
            }
        }
    };

    window.ConversationHistory = ConversationHistory;
})();
