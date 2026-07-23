/**
 * Global Validators Utility for Logistics Platform
 * Verifies variable types to prevent NaN, null, and division by zero.
 * Supports raw numbers, formatted strings, and nested KPI objects.
 */
(function() {
    const Validators = {
        isValidNumber(val) {
            if (val === null || val === undefined || val === "") return false;
            if (typeof val === "object") {
                if (val.raw_value !== undefined && !isNaN(Number(val.raw_value))) return true;
                if (val.value !== undefined) val = val.value;
            }
            if (typeof val === "number") return !isNaN(val) && isFinite(val);
            if (typeof val === "string") {
                const cleaned = val.replace(/,/g, '').replace(/[\$,%\sDaysUnitsmi]/gi, '').trim();
                const n = Number(cleaned);
                return !isNaN(n) && isFinite(n);
            }
            return !isNaN(Number(val)) && isFinite(Number(val));
        },
        isValidString(val) {
            return typeof val === "string" && val.trim().length > 0;
        },
        isValidDate(val) {
            if (!val) return false;
            const d = new Date(val);
            return d instanceof Date && !isNaN(d.getTime());
        }
    };
    window.Validators = Validators;
})();
