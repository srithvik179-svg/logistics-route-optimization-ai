/**
 * AI Copilot Main Page Controller
 * Handles conversation payloads send/receive triggers, histories, and exports.
 */
(function() {
    let _activeHistory = [];

    async function initCopilotWorkspace() {
        console.log("[Copilot] Initializing AI Logistics Copilot workspace...");

        // Load logs
        await fetchHistory();

        // Render suggested prompt buttons
        window.PromptSuggestions.render("copilot-suggestions-container", (selectedText) => {
            // Populate and trigger send
            const input = document.getElementById("copilot-chat-input");
            if (input) {
                input.value = selectedText;
                window.CopilotChat.sendMessage();
            }
        });

        // Render export options
        window.ConversationExport.render("copilot-export-container");
    }

    async function fetchHistory() {
        try {
            const res = await fetch("/api/copilot/history");
            if (!res.ok) throw new Error("Failed to fetch chat logs");
            const data = await res.json();
            _activeHistory = data.history || [];

            // 1. Render active chatBubbles view console
            window.CopilotChat.render("copilot-chat-container", _activeHistory, async (promptText) => {
                await sendPromptToCopilot(promptText);
            });

            // 2. Render sidebar logs archive lists
            window.ConversationHistory.render("copilot-history-container", _activeHistory);

        } catch (err) {
            console.error("[Copilot] Error loading history logs:", err);
        }
    }

    async function sendPromptToCopilot(promptText) {
        try {
            const res = await fetch("/api/copilot/message", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: promptText })
            });

            window.CopilotChat.hideTyping();

            if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
            const data = await res.json();

            // Refresh logs
            await fetchHistory();
        } catch (err) {
            console.error("[Copilot] Failed sending message:", err);
            window.CopilotChat.hideTyping();
            
            // Append error bubble
            const view = document.getElementById("copilot-bubbles-view");
            const bubble = document.createElement("div");
            bubble.className = "chat-bubble assistant-bubble";
            bubble.innerHTML = `<div class="bubble-header">AI Logistics Copilot</div><div class="bubble-body text-danger"><i class="fa-solid fa-triangle-exclamation"></i> Error: Failed to contact Copilot service.</div>`;
            view.appendChild(bubble);
            window.CopilotChat.scrollToBottom();
        }
    }

    window.loadCopilotWorkspace = initCopilotWorkspace;
})();
