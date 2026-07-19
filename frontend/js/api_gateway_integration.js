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
     * Resolves or fetches a valid JWT auth token using mock admin credentials.
     */
    async function acquireAuthToken() {
        if (authToken) return authToken;

        if (isFetchingToken) {
            return new Promise((resolve) => {
                tokenWaitQueue.push(resolve);
            });
        }

        isFetchingToken = true;
        console.log("[Observability] JWT Access Token missing. Requesting token from security gateway...");

        try {
            const response = await originalFetch("/api/v1/security/auth/token", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username: "admin", password: "admin123" })
            });

            if (!response.ok) {
                throw new Error(`Authentication endpoint returned status ${response.status}`);
            }

            const data = await response.json();
            // Automatically unwrap success payload
            const payload = (data && data.status === "success") ? data.payload : data;
            const token = payload ? payload.access_token : null;

            if (token) {
                authToken = token;
                localStorage.setItem("dell_gateway_auth_token", token);
                console.log("[Observability] JWT Access Token successfully acquired.");
            } else {
                console.error("[Observability] Token format not recognized:", data);
            }
        } catch (err) {
            console.error("[Observability] JWT Authentication Failure:", err);
        } finally {
            isFetchingToken = false;
            const queue = [...tokenWaitQueue];
            tokenWaitQueue = [];
            queue.forEach(resolve => resolve(authToken));
        }

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
                if (response.status === 401 && !isAuthCall && attempt < maxAttempts) {
                    console.warn(`[Observability] JWT Token invalid or expired (401). Retrying with token refresh...`);
                    authToken = null;
                    localStorage.removeItem("dell_gateway_auth_token");
                    continue;
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
