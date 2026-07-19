/**
 * SafeValue accessor Utility
 * Safely traverses nested objects to retrieve values and formats them.
 */
(function() {
    const SafeValue = {
        get(obj, path, fallback = "—", formatter = null) {
            if (!obj) return fallback;
            const parts = path.split('.');
            let current = obj;
            for (const p of parts) {
                if (current === null || current === undefined) {
                    return fallback;
                }
                current = current[p];
            }
            if (current === null || current === undefined || (typeof current === "number" && isNaN(current))) {
                return fallback;
            }
            if (formatter) {
                try {
                    return formatter(current);
                } catch (e) {
                    console.error(`[SafeValue] Formatting error at path "${path}":`, e);
                    return fallback;
                }
            }
            return current;
        }
    };
    window.SafeValue = SafeValue;
})();
