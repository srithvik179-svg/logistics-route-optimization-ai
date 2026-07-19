/**
 * Global Validators Utility for Logistics Platform
 * Verifies variable types to prevent NaN, null, and division by zero.
 */
(function() {
    const Validators = {
        isValidNumber(val) {
            return val !== null && val !== undefined && val !== "" && !isNaN(Number(val)) && isFinite(Number(val));
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
