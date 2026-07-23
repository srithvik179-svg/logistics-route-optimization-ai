/**
 * Global Formatters Utility for Logistics Platform
 * Provides safe text outputs without crashes or NaN flags.
 * Robustly parses raw numbers, formatted strings, and KPI objects.
 */
(function() {
    function parseRawNumber(val) {
        if (val === null || val === undefined || val === "") return 0;
        if (typeof val === "object") {
            if (val.raw_value !== undefined && typeof val.raw_value === "number") return val.raw_value;
            if (val.raw_value !== undefined && !isNaN(parseFloat(val.raw_value))) return parseFloat(val.raw_value);
            if (val.value !== undefined) val = val.value;
        }
        if (typeof val === "number") return isNaN(val) ? 0 : val;
        if (typeof val === "string") {
            const cleaned = val.replace(/,/g, '').replace(/[\$,%\sDaysUnitsmi]/gi, '').trim();
            const num = parseFloat(cleaned);
            return isNaN(num) ? 0 : num;
        }
        return 0;
    }

    const Formatters = {
        parseRawNumber: parseRawNumber,
        safeFixed(val, decimals = 1) {
            const num = parseRawNumber(val);
            return num.toFixed(decimals);
        },
        safeNumber(val, decimals = 0) {
            const num = parseRawNumber(val);
            return num.toLocaleString(undefined, {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            });
        },
        safeCurrency(val, decimals = 2) {
            const num = parseRawNumber(val);
            return "$" + num.toLocaleString(undefined, {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            });
        },
        safePercentage(val, decimals = 1) {
            const num = parseRawNumber(val);
            const pct = num <= 1 && num !== 0 ? num * 100 : num;
            return num.toFixed(decimals) + "%";
        },
        safeDuration(val) {
            const num = parseRawNumber(val);
            return num.toFixed(1) + " Days";
        },
        safeDistance(val) {
            const num = parseRawNumber(val);
            return num.toFixed(1) + " mi";
        },
        safeDate(val) {
            if (!window.Validators || !window.Validators.isValidDate || !window.Validators.isValidDate(val)) {
                if (val && !isNaN(new Date(val).getTime())) {
                    const d = new Date(val);
                    return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
                }
                return "Pending";
            }
            const d = new Date(val);
            return d.toLocaleDateString(undefined, {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        }
    };
    window.Formatters = Formatters;
})();
