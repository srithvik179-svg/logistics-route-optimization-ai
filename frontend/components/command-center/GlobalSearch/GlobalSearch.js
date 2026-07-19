/**
 * GlobalSearch Component
 * Enterprise search bar querying shipments, hubs, and corridors with deep link navigation.
 */
(function() {
    const GlobalSearch = {
        render(containerId) {
            const el = document.getElementById(containerId);
            if (!el) return;

            el.innerHTML = `
                <div style="position:relative; width:100%; max-width:400px;">
                    <div style="display:flex; align-items:center; background:rgba(9,9,11,0.6); border:1px solid rgba(63,63,70,0.5); border-radius:8px; padding:0 10px;">
                        <i class="fa-solid fa-magnifying-glass text-muted" style="font-size:12px;"></i>
                        <input type="text" id="global-search-input" placeholder="Search shipments, hubs, corridors..." 
                               style="background:transparent; border:none; color:#fff; font-size:11px; padding:8px 6px; width:100%; outline:none;"
                               oninput="GlobalSearch.handleSearch(this.value)">
                    </div>
                    <div id="global-search-results" 
                         style="position:absolute; top:36px; left:0; width:100%; background:#18181b; border:1px solid rgba(63,63,70,0.5); border-radius:8px; box-shadow:0 10px 15px -3px rgba(0,0,0,0.5); z-index:999; display:none; max-height:280px; overflow-y:auto; padding:6px 0;">
                    </div>
                </div>
            `;
        },

        async handleSearch(val) {
            const box = document.getElementById("global-search-results");
            if (!box) return;

            if (!val || val.trim().length < 2) {
                box.style.display = "none";
                return;
            }

            try {
                const res = await fetch("/api/command-center/search", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ query: val })
                });
                if (!res.ok) throw new Error("Search request failed");
                const results = await res.json();

                if (!results.length) {
                    box.innerHTML = `<div style="padding:10px; font-size:10px; color:var(--text-muted); text-align:center;">No records found.</div>`;
                } else {
                    box.innerHTML = results.map(r => `
                        <div style="padding:8px 12px; border-bottom:1px solid rgba(63,63,70,0.2); cursor:pointer;"
                             onmouseover="this.style.background='rgba(59,130,246,0.1)'"
                             onmouseout="this.style.background='transparent'"
                             onclick="GlobalSearch.navigate('${r.target_section}', '${r.id}')">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2px;">
                                <strong style="font-size:10px; color:#fff;">${r.title}</strong>
                                <span class="badge badge-info" style="font-size:8px; padding:1px 4px;">${r.category}</span>
                            </div>
                            <div style="font-size:9px; color:var(--text-muted);">${r.subtitle}</div>
                        </div>
                    `).join("");
                }
                box.style.display = "block";

            } catch (err) {
                console.error("[GlobalSearch] Search Error:", err);
            }
        },

        navigate(sectionId, id) {
            const box = document.getElementById("global-search-results");
            if (box) box.style.display = "none";

            const input = document.getElementById("global-search-input");
            if (input) input.value = "";

            const link = document.querySelector(`.nav-link[data-target="${sectionId}"]`);
            if (link) {
                link.click();
                setTimeout(() => {
                    // Small notification toast helper
                    const toast = document.createElement("div");
                    toast.style.cssText = `position:fixed; bottom:20px; right:20px; background:rgba(59,130,246,0.9); color:#fff;
                                           padding:10px 16px; border-radius:8px; font-size:12px; z-index:9999;`;
                    toast.textContent = `Deep link navigates: loaded ${id} inside ${sectionId}`;
                    document.body.appendChild(toast);
                    setTimeout(() => toast.remove(), 3500);
                }, 500);
            }
        }
    };

    window.GlobalSearch = GlobalSearch;
})();
