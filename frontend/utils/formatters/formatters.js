/**
 * Global Formatters Utility for Logistics Platform
 * Provides safe text outputs without crashes or NaN flags.
 */
(function() {
    const Formatters = {
        safeNumber(val, decimals = 0) {
            if (!window.Validators.isValidNumber(val)) return "0";
            return Number(val).toLocaleString(undefined, {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            });
        },
        safeCurrency(val, decimals = 2) {
            if (!window.Validators.isValidNumber(val)) return "$0.00";
            return "$" + Number(val).toLocaleString(undefined, {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            });
        },
        safePercentage(val, decimals = 1) {
            if (!window.Validators.isValidNumber(val)) return "0.0%";
            const n = Number(val);
            // Handle fractional percentage checks
            const pct = n <= 1 && n !== 0 ? n * 100 : n;
            return pct.toFixed(decimals) + "%";
        },
        safeDuration(val) {
            if (!window.Validators.isValidNumber(val)) return "0.0 Days";
            return Number(val).toFixed(1) + " Days";
        },
        safeDistance(val) {
            if (!window.Validators.isValidNumber(val)) return "0.0 mi";
            return Number(val).toFixed(1) + " mi";
        },
        safeDate(val) {
            if (!window.Validators.isValidDate(val)) return "Pending";
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
