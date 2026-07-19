/**
 * Enterprise Authentication & Session Manager
 * Integrated with backend JWT security endpoints and handles Role-Based Access Control (RBAC).
 */
(function() {
    // Prevent double load
    if (window.__AuthManagerLoaded) return;
    window.__AuthManagerLoaded = true;

    // Permissions Mapping corresponding to backend UserRole models
    const ROLE_PERMISSIONS = {
        "Administrator": [
            "analytics:read",
            "optimization:write",
            "inventory:read",
            "transit:read",
            "cost:read",
            "sla:read",
            "decision:read",
            "system:read",
            "admin:write"
        ],
        "Operations Manager": [
            "analytics:read",
            "optimization:write",
            "inventory:read",
            "transit:read",
            "cost:read",
            "sla:read",
            "decision:read"
        ],
        "Logistics Analyst": [
            "analytics:read",
            "optimization:write",
            "transit:read",
            "cost:read",
            "sla:read"
        ],
        "Viewer": [
            "analytics:read"
        ]
    };

    // Sidebar mapping to required permission scope
    const NAV_PERMISSION_REQUIREMENTS = {
        "overview-section": "analytics:read",
        "dashboard-section": "analytics:read",
        "network-map-section": "transit:read",
        "routes-section": "optimization:write",
        "performance-section": "analytics:read",
        "dataset-section": "analytics:read",
        "explorer-section": "analytics:read",
        "workspace-section": "decision:read",
        "executive-section": "system:read",
        "admin-section": "admin:write"
    };

    // Department descriptions for profile view
    const ROLE_DEPARTMENTS = {
        "Administrator": "Global Security & System Operations",
        "Operations Manager": "Global Logistics Operations Center",
        "Logistics Analyst": "Logistics Analytics & Route Strategy",
        "Viewer": "Executive Leadership & Business Intelligence"
    };

    // Session states
    let currentUser = null;
    let sessionCheckInterval = null;
    let activeCredentials = null; // Transient store for session extension
    let isShowingTimeoutDialog = false;

    window.AuthManager = {
        init,
        login,
        logout,
        extendSession,
        getCurrentUser: () => currentUser,
        checkPermission: (perm) => currentUser && currentUser.permissions.includes(perm)
    };

    document.addEventListener("DOMContentLoaded", () => {
        init();
    });

    /**
     * Decode JWT token payload
     */
    function decodeJwt(token) {
        try {
            const parts = token.split('.');
            if (parts.length !== 3) return null;
            
            // Base64URL decode
            const payloadBase64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(window.atob(payloadBase64).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            
            return JSON.parse(jsonPayload);
        } catch (e) {
            console.error("[Security] JWT decode failed:", e);
            return null;
        }
    }

    /**
     * Initialize Auth state, check stored tokens
     */
    function init() {
        const token = localStorage.getItem("dell_gateway_auth_token");
        setupProfileMenuClick();
        
        if (token) {
            const payload = decodeJwt(token);
            const now = Math.floor(Date.now() / 1000);
            
            if (payload && payload.exp > now) {
                // Token is still valid
                currentUser = {
                    user_id: payload.sub,
                    username: payload.username,
                    role: payload.role,
                    permissions: ROLE_PERMISSIONS[payload.role] || [],
                    exp: payload.exp
                };
                
                // Restore credentials if saved for extend flow
                const savedCreds = sessionStorage.getItem("dell_transient_creds");
                if (savedCreds) {
                    try { activeCredentials = JSON.parse(savedCreds); } catch(e){}
                }
                
                applyAuthenticationSuccess();
                return;
            }
        }
        
        // Show login screen if not logged in or expired
        showLoginScreen();
    }

    /**
     * Hides the main screen and activates the Login overlay
     */
    function showLoginScreen(errorText = "") {
        const overlay = document.getElementById("auth-overlay");
        const forgotOverlay = document.getElementById("forgot-overlay");
        if (forgotOverlay) forgotOverlay.classList.remove("active");
        
        if (overlay) {
            overlay.classList.add("active");
            
            // Restore remembered username
            const rememberedUser = localStorage.getItem("dell_auth_remembered_user");
            const usernameInput = document.getElementById("login-username");
            const rememberMeInput = document.getElementById("login-remember");
            
            if (usernameInput && rememberedUser) {
                usernameInput.value = rememberedUser;
                if (rememberMeInput) rememberMeInput.checked = true;
            }
            
            // Show error if present
            const errorContainer = document.getElementById("login-error");
            if (errorContainer) {
                if (errorText) {
                    errorContainer.textContent = errorText;
                    errorContainer.style.display = "flex";
                } else {
                    errorContainer.style.display = "none";
                }
            }
        }
        
        // Clear active session updates
        clearInterval(sessionCheckInterval);
        document.body.classList.add("auth-logged-out");
    }

    /**
     * Processes login authentication request
     */
    async function login(username, password, rememberMe) {
        const errorContainer = document.getElementById("login-error");
        const submitBtn = document.getElementById("login-submit-btn");
        
        if (errorContainer) errorContainer.style.display = "none";
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Authenticating...';
        }

        try {
            // Fetch token using user credentials
            const response = await fetch("/api/v1/security/auth/token", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                const detail = await response.json().then(d => d.detail || "Authentication Failed");
                throw new Error(detail);
            }

            const data = await response.json();
            // Unwrap Gateway response payload
            const payload = data;
            const token = payload.access_token;

            if (!token) {
                throw new Error("Authorization token not found in response.");
            }

            // Save credentials transiently for session extension
            activeCredentials = { username, password };
            sessionStorage.setItem("dell_transient_creds", JSON.stringify(activeCredentials));

            if (rememberMe) {
                localStorage.setItem("dell_auth_remembered_user", username);
            } else {
                localStorage.removeItem("dell_auth_remembered_user");
            }

            // Set main auth token
            localStorage.setItem("dell_gateway_auth_token", token);
            
            // Decode claims
            const claims = decodeJwt(token);
            currentUser = {
                user_id: claims.sub,
                username: claims.username,
                role: claims.role,
                permissions: ROLE_PERMISSIONS[claims.role] || [],
                exp: claims.exp
            };

            // Set last login metadata
            const lastLogin = new Date().toLocaleString();
            localStorage.setItem("dell_auth_last_login", lastLogin);

            // Emit required observability logs
            console.log(`[Security] User Login: ${currentUser.username} (${currentUser.role})`);
            console.log("[Security] Session Created");
            console.log(`[Security] Permission Updated: [${currentUser.permissions.join(", ")}]`);

            // Apply login changes
            applyAuthenticationSuccess();
            showNotification("Successfully logged in", "success");

        } catch (err) {
            console.error("[Security] Login execution failed:", err);
            showLoginScreen(err.message || "Invalid credentials. Please try again.");
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = "Sign In";
            }
        }
    }

    /**
     * Action to apply view transformations upon successful login
     */
    function applyAuthenticationSuccess() {
        document.body.classList.remove("auth-logged-out");
        const overlay = document.getElementById("auth-overlay");
        if (overlay) overlay.classList.remove("active");

        // Initialize session monitoring loop
        clearInterval(sessionCheckInterval);
        sessionCheckInterval = setInterval(monitorSessionTimeout, 1000);

        // Update profile indicators in layout header & dropdown
        updateProfileUI();

        // Enforce role-based sidebar visibility
        enforceSidebarPermissions();
        
        // Re-load dataset details on login to refresh views
        if (typeof fetchDatasetStatus === 'function') {
            fetchDatasetStatus();
        }
    }

    /**
     * User Logout Flow
     */
    function logout() {
        if (currentUser) {
            console.log(`[Security] User Logout: ${currentUser.username}`);
        }
        
        currentUser = null;
        activeCredentials = null;
        localStorage.removeItem("dell_gateway_auth_token");
        sessionStorage.removeItem("dell_transient_creds");
        
        // Close profile dropdown
        const dropdown = document.getElementById("profile-dropdown");
        if (dropdown) dropdown.classList.remove("active");
        
        // Hide timeout overlays
        const timeoutOverlay = document.getElementById("timeout-overlay");
        if (timeoutOverlay) timeoutOverlay.classList.remove("active");
        isShowingTimeoutDialog = false;

        showLoginScreen();
        showNotification("Successfully logged out", "info");
    }

    /**
     * Session Expiration handler
     */
    function triggerSessionExpiration() {
        console.log("[Security] Session Expired");
        if (currentUser) {
            console.log(`[Security] User Logout: ${currentUser.username}`);
        }
        
        currentUser = null;
        activeCredentials = null;
        localStorage.removeItem("dell_gateway_auth_token");
        sessionStorage.removeItem("dell_transient_creds");

        const timeoutOverlay = document.getElementById("timeout-overlay");
        if (timeoutOverlay) timeoutOverlay.classList.remove("active");
        isShowingTimeoutDialog = false;

        showLoginScreen("Your session has expired. Please sign in again.");
    }

    /**
     * Background interval task to track expiration progress
     */
    function monitorSessionTimeout() {
        if (!currentUser) return;
        
        const now = Math.floor(Date.now() / 1000);
        const timeRemaining = currentUser.exp - now;

        // Update session duration indicators in profile dropdown
        const statusVal = document.getElementById("profile-status-val");
        if (statusVal) {
            if (timeRemaining > 60) {
                statusVal.textContent = `Active (${Math.ceil(timeRemaining / 60)}m left)`;
                statusVal.style.color = "var(--success-color)";
            } else {
                statusVal.textContent = `Expiring (${timeRemaining}s left)`;
                statusVal.style.color = "var(--warning-color)";
            }
        }

        // Show warning countdown if 30 seconds left
        if (timeRemaining <= 30 && timeRemaining > 0) {
            if (!isShowingTimeoutDialog) {
                showTimeoutWarning();
            }
            updateTimeoutCountdown(timeRemaining);
        } else if (timeRemaining <= 0) {
            triggerSessionExpiration();
        }
    }

    /**
     * Displays timeout dialog warning panel
     */
    function showTimeoutWarning() {
        isShowingTimeoutDialog = true;
        const timeoutOverlay = document.getElementById("timeout-overlay");
        if (timeoutOverlay) {
            timeoutOverlay.classList.add("active");
        }
    }

    /**
     * Updates countdown dialog components
     */
    function updateTimeoutCountdown(seconds) {
        const text = document.getElementById("timeout-countdown-text");
        const progress = document.getElementById("timeout-progress-bar");
        
        if (text) text.textContent = seconds;
        if (progress) {
            const percentage = (seconds / 30) * 100;
            progress.style.width = `${percentage}%`;
            
            if (seconds <= 10) {
                progress.style.backgroundColor = "var(--danger-color)";
            } else {
                progress.style.backgroundColor = "var(--warning-color)";
            }
        }
    }

    /**
     * Re-requests a token using active transient credentials to extend session
     */
    async function extendSession() {
        const timeoutOverlay = document.getElementById("timeout-overlay");
        if (timeoutOverlay) timeoutOverlay.classList.remove("active");
        isShowingTimeoutDialog = false;

        if (!activeCredentials) {
            logout();
            return;
        }

        try {
            console.log("[Security] Extending session...");
            const response = await fetch("/api/v1/security/auth/token", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    username: activeCredentials.username,
                    password: activeCredentials.password
                })
            });

            if (!response.ok) throw new Error("Could not refresh token");

            const data = await response.json();
            const token = data.access_token;
            
            localStorage.setItem("dell_gateway_auth_token", token);
            
            const claims = decodeJwt(token);
            currentUser.exp = claims.exp;

            console.log("[Security] Session extended successfully.");
            showNotification("Session extended successfully", "success");

        } catch (e) {
            console.error("[Security] Session extension failed:", e);
            logout();
        }
    }

    /**
     * Hides/shows sidebar items based on current role permissions
     */
    function enforceSidebarPermissions() {
        if (!currentUser) return;
        
        const navLinks = document.querySelectorAll(".sidebar-nav .nav-link");
        let activeLinkVisible = false;

        navLinks.forEach(link => {
            const target = link.getAttribute("data-target");
            const reqPermission = NAV_PERMISSION_REQUIREMENTS[target];
            const hasPermission = !reqPermission || currentUser.permissions.includes(reqPermission);
            
            const li = link.closest("li");
            if (hasPermission) {
                if (li) li.style.display = "block";
                if (link.classList.contains("active")) {
                    activeLinkVisible = true;
                }
            } else {
                if (li) li.style.display = "none";
                link.classList.remove("active");
            }
        });

        // If the active view became hidden, redirect to Overview tab
        if (!activeLinkVisible) {
            const overviewLink = document.querySelector('.nav-link[data-target="overview-section"]');
            if (overviewLink) {
                overviewLink.click();
            }
        }
    }

    /**
     * Fills profile menu widgets with logged-in user context
     */
    function updateProfileUI() {
        if (!currentUser) return;

        // Avatar details
        const headerName = document.querySelector(".user-profile .user-name");
        const headerRole = document.querySelector(".user-profile .user-role");
        const dropdownAvatar = document.querySelector(".profile-dropdown-header .avatar");
        const dropdownName = document.getElementById("profile-name-val");
        const dropdownRole = document.getElementById("profile-role-val");
        const dropdownDept = document.getElementById("profile-dept-val");
        const dropdownLastLogin = document.getElementById("profile-last-login-val");

        // Set Initials
        const initials = currentUser.username.slice(0, 2).toUpperCase();

        if (headerName) headerName.textContent = currentUser.username.charAt(0).toUpperCase() + currentUser.username.slice(1);
        if (headerRole) headerRole.textContent = currentUser.role;
        if (dropdownAvatar) dropdownAvatar.textContent = initials;
        if (dropdownName) dropdownName.textContent = currentUser.username.charAt(0).toUpperCase() + currentUser.username.slice(1);
        if (dropdownRole) dropdownRole.textContent = currentUser.role;
        if (dropdownDept) dropdownDept.textContent = ROLE_DEPARTMENTS[currentUser.role] || "Logistics Division";
        
        const lastLogin = localStorage.getItem("dell_auth_last_login") || "First Session";
        if (dropdownLastLogin) dropdownLastLogin.textContent = lastLogin;
    }

    /**
     * Wire up click handling on the avatar profile
     */
    function setupProfileMenuClick() {
        const avatarBox = document.getElementById("profile-avatar-click");
        const dropdown = document.getElementById("profile-dropdown");
        
        if (avatarBox && dropdown) {
            avatarBox.addEventListener("click", (e) => {
                e.stopPropagation();
                dropdown.classList.toggle("active");
            });

            document.addEventListener("click", (e) => {
                if (!dropdown.contains(e.target) && !avatarBox.contains(e.target)) {
                    dropdown.classList.remove("active");
                }
            });
        }
    }

    /**
     * Visual Toast Notification Banner helper
     */
    function showNotification(message, type = "info") {
        const toast = document.createElement("div");
        toast.className = `toast-banner ${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fa-solid ${type === 'success' ? 'fa-circle-check' : type === 'warning' ? 'fa-triangle-exclamation' : 'fa-circle-info'}"></i>
                <span>${message}</span>
            </div>
        `;
        
        // Base styles for toast notification banner
        Object.assign(toast.style, {
            position: "fixed",
            bottom: "24px",
            right: "24px",
            background: "rgba(24, 24, 27, 0.95)",
            border: `1px solid ${type === 'success' ? 'var(--success-color)' : type === 'warning' ? 'var(--warning-color)' : 'var(--accent-blue)'}`,
            borderRadius: "var(--radius-md)",
            padding: "var(--space-3) var(--space-4)",
            color: "var(--text-primary)",
            fontSize: "var(--font-size-sm)",
            zIndex: "100000",
            boxShadow: "var(--elevation-floating)",
            transform: "translateY(20px)",
            opacity: "0",
            transition: "all 0.3s ease"
        });

        // Insert
        document.body.appendChild(toast);
        
        // Trigger reflow & animation
        toast.offsetHeight;
        toast.style.transform = "translateY(0)";
        toast.style.opacity = "1";

        // Remove after 3 seconds
        setTimeout(() => {
            toast.style.transform = "translateY(20px)";
            toast.style.opacity = "0";
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
})();
