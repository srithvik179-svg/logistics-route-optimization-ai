/**
 * CopilotChat Component
 * Handles the main chat conversation viewport containing message bubbles, typing indicators, and user inputs.
 */
(function() {
    let _onSendCallback = null;

    const CopilotChat = {
        render(containerId, history = [], onSend) {
            const container = document.getElementById(containerId);
            if (!container) return;

            _onSendCallback = onSend;

            container.innerHTML = `
                <div class="card glass-panel copilot-chat-card" style="padding:var(--space-3); border:1px solid rgba(63,63,70,0.4); display:flex; flex-direction:column; height:450px;">
                    <div style="font-size:11px; font-weight:bold; color:#fff; text-transform:uppercase; border-bottom:1px solid rgba(63,63,70,0.4); padding-bottom:var(--space-2); margin-bottom:var(--space-2); display:flex; justify-content:space-between; align-items:center;">
                        <span><i class="fa-solid fa-comments text-primary"></i> Copilot Active Conversation</span>
                        <span style="font-size:9px; background:rgba(16,185,129,0.1); color:#10b981; padding:1px 5px; border-radius:3px; border:1px solid rgba(16,185,129,0.2);"><i class="fa-solid fa-circle"></i> Online</span>
                    </div>

                    <!-- Chat bubbles container -->
                    <div id="copilot-bubbles-view" style="flex:1; overflow-y:auto; padding:var(--space-2); display:flex; flex-direction:column; gap:12px; margin-bottom:var(--space-3);">
                        <!-- Default greeting bubble -->
                        <div class="chat-bubble assistant-bubble">
                            <div class="bubble-header">AI Logistics Copilot</div>
                            <div class="bubble-body">
                                Hello operations manager! I am your conversational Logistics Copilot. I can query health KPIs, predicted breaches, reverse logistics, and orchestrator workflow runs. How can I assist you today?
                            </div>
                        </div>

                        ${history.map(msg => this.generateBubbleHtml(msg)).join('')}
                    </div>

                    <!-- Input row controls -->
                    <div style="display:flex; gap:var(--space-2); align-items:center; border-top:1px solid rgba(63,63,70,0.4); padding-top:var(--space-2);">
                        <input type="text" id="copilot-chat-input" placeholder="Ask Copilot a question..." onkeydown="CopilotChat.handleKey(event)" style="flex:1; background:rgba(9,9,11,0.6); border:1px solid rgba(63,63,70,0.4); color:#fff; border-radius:6px; padding:10px 12px; font-size:11px; outline:none;">
                        <button class="btn btn-primary" onclick="CopilotChat.sendMessage()" style="padding:10px var(--space-4);">
                            <i class="fa-solid fa-paper-plane"></i> Send
                        </button>
                    </div>
                </div>
            `;

            // Scroll to bottom
            this.scrollToBottom();

            if (!document.getElementById("copilot-chat-bubble-styles")) {
                const style = document.createElement("style");
                style.id = "copilot-chat-bubble-styles";
                style.textContent = `
                    .chat-bubble {
                        max-width: 80%; display: flex; flex-direction: column; gap: 4px; padding: 10px 12px; border-radius: 8px; font-size: 11px; line-height: 1.4;
                    }
                    .user-bubble {
                        align-self: flex-end; background: var(--primary-color); color: #fff;
                        border-bottom-right-radius: 2px; border: 1.5px solid rgba(255,255,255,0.15);
                    }
                    .assistant-bubble {
                        align-self: flex-start; background: rgba(39, 39, 42, 0.6); border: 1px solid rgba(63, 63, 70, 0.4); color: var(--text-secondary);
                        border-bottom-left-radius: 2px;
                    }
                    .bubble-header {
                        font-size: 9px; text-transform: uppercase; color: var(--text-muted); font-weight: bold;
                    }
                    .user-bubble .bubble-header {
                        color: rgba(255,255,255,0.8);
                    }
                    .typing-indicator {
                        align-self: flex-start; display: flex; gap: 4px; padding: 10px 15px; background: rgba(39, 39, 42, 0.6); border-radius: 8px;
                    }
                    .typing-dot {
                        width: 5px; height: 5px; background: var(--text-muted); border-radius: 50%;
                        animation: typingPulse 1.2s infinite alternate;
                    }
                    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
                    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
                    @keyframes typingPulse {
                        from { opacity: 0.3; transform: scale(0.8); }
                        to { opacity: 1; transform: scale(1.2); }
                    }
                `;
                document.head.appendChild(style);
            }
        },

        generateBubbleHtml(msg) {
            const isUser = msg.role === "user";
            let contentHtml = msg.message;
            
            // If assistant response contains structured payload, parse with RichResponse
            if (!isUser && msg.payload) {
                contentHtml = window.RichResponse.renderHtml(msg.payload);
            }

            return `
                <div class="chat-bubble ${isUser ? 'user-bubble' : 'assistant-bubble'}">
                    <div class="bubble-header">${isUser ? 'Operations Manager' : 'AI Logistics Copilot'}</div>
                    <div class="bubble-body">${contentHtml}</div>
                </div>
            `;
        },

        handleKey(e) {
            if (e.key === "Enter") {
                this.sendMessage();
            }
        },

        sendMessage() {
            const input = document.getElementById("copilot-chat-input");
            if (!input || !input.value.trim()) return;

            const text = input.value.trim();
            input.value = "";

            // Render user bubble immediately
            const view = document.getElementById("copilot-bubbles-view");
            const bubble = document.createElement("div");
            bubble.className = "chat-bubble user-bubble";
            bubble.innerHTML = `<div class="bubble-header">Operations Manager</div><div class="bubble-body">${text}</div>`;
            view.appendChild(bubble);

            // Add typing indicator
            const typing = document.createElement("div");
            typing.id = "copilot-typing-loader";
            typing.className = "typing-indicator";
            typing.innerHTML = `<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>`;
            view.appendChild(typing);

            this.scrollToBottom();

            if (typeof _onSendCallback === "function") {
                _onSendCallback(text);
            }
        },

        hideTyping() {
            const el = document.getElementById("copilot-typing-loader");
            if (el) el.remove();
        },

        scrollToBottom() {
            const view = document.getElementById("copilot-bubbles-view");
            if (view) {
                setTimeout(() => {
                    view.scrollTop = view.scrollHeight;
                }, 50);
            }
        }
    };

    window.CopilotChat = CopilotChat;
})();
