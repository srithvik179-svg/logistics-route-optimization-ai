/**
 * API Gateway Integration & Global Interceptor Layer
 * 
 * Enforces:
 * - Transparent JWT Authentication
 * - Request Tracing and Authorization Headers
 * - Response Unwrapping (.payload extraction)
 * - Automatic Retry mechanism on transient network or server errors
 * - Refresh flow on expired tokens (401)
 * - Observability Logging
 */
(function() {
    console.log("[Observability] Frontend Connected to API Gateway Integration Layer.");

    const originalFetch = window.fetch;
    let authToken = localStorage.getItem("dell_gateway_auth_token") || null;
    let isFetchingToken = false;
    let tokenWaitQueue = [];

    /**
     * Resolves the current auth token stored in localStorage (set by auth.js on login).
     */
    async function acquireAuthToken() {
        authToken = localStorage.getItem("dell_gateway_auth_token");
        return authToken;
    }

    /**
     * Overrides window.fetch to provide centralized request wrappers, retry strategies, and response unwrappers.
     */
    window.fetch = async function(url, options = {}) {
        const urlStr = typeof url === "string" ? url : (url && url.url) || "";
        const isApiRequest = urlStr.startsWith("/api") && !urlStr.includes("/static/");

        if (!isApiRequest) {
            return originalFetch(url, options);
        }

        console.log(`[Observability] API Request Started: ${urlStr}`);
        const isAuthCall = urlStr.includes("/auth/token");

        let attempt = 0;
        const maxAttempts = 3;

        while (attempt < maxAttempts) {
            attempt++;
            try {
                const requestOptions = { ...options };
                requestOptions.headers = { ...(requestOptions.headers || {}) };

                // Inject JWT Authorization headers
                if (!isAuthCall) {
                    const token = await acquireAuthToken();
                    if (token) {
                        requestOptions.headers["Authorization"] = `Bearer ${token}`;
                    }
                }

                const response = await originalFetch(url, requestOptions);

                // Handle token expiration/revocation (401 Unauthorized)
                if (response.status === 401 && !isAuthCall) {
                    console.warn(`[Observability] JWT Token invalid or expired (401). Triggering logout...`);
                    authToken = null;
                    localStorage.removeItem("dell_gateway_auth_token");
                    if (window.AuthManager && typeof window.AuthManager.logout === "function") {
                        window.AuthManager.logout();
                    }
                    return response;
                }

                // Handle server issues (status >= 500)
                if (response.status >= 500 && attempt < maxAttempts) {
                    console.warn(`[Observability] Gateway error status ${response.status} on attempt ${attempt}. Retrying...`);
                    console.log("[Observability] Retry Executed");
                    await new Promise(resolve => setTimeout(resolve, attempt * 500));
                    continue;
                }

                // Format response to automatically unwrap the success envelope .payload
                const contentType = response.headers.get("content-type") || "";
                if (contentType.includes("application/json")) {
                    const originalJson = response.json.bind(response);
                    response.json = async function() {
                        const body = await originalJson();
                        console.log(`[Observability] API Request Completed: ${urlStr}`);

                        if (body && body.status === "success") {
                            console.log("[Observability] Data Bound Successfully");
                            return body.payload;
                        }

                        if (body && body.status === "error") {
                            console.error("[Observability] API Failure details:", body.error);
                            throw new Error(body.error.detail || "Gateway returned error status");
                        }

                        return body;
                    };
                }

                return response;

            } catch (err) {
                console.error(`[Observability] API Failure on ${urlStr} (Attempt ${attempt}):`, err);
                if (attempt >= maxAttempts) {
                    throw err;
                }
                await new Promise(resolve => setTimeout(resolve, attempt * 500));
            }
        }
    };
})();
