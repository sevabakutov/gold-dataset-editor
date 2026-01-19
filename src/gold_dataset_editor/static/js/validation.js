/**
 * Gold Dataset Editor - Field Validation
 *
 * Provides visual warnings (non-blocking) for field format validation.
 */

// Validation patterns
const VALIDATION_RULES = {
    number_phone: {
        pattern: /^\+?[0-9]{10,15}$/,
        warning: 'Phone number should match E.164 format (e.g., +380501234567)'
    }
    // date_time: no validation - can be any string format
};

/**
 * Initialize validation for all slot inputs
 */
function initValidation() {
    // Validate phone input
    const phoneInput = document.getElementById('slot-number_phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', function() {
            validateSlot('number_phone', this.value);
        });
        // Validate current value
        validateSlot('number_phone', phoneInput.value);
    }

}

/**
 * Validate a slot value and show/hide warning
 */
function validateSlot(slotName, value) {
    const rule = VALIDATION_RULES[slotName];
    if (!rule) return;

    const warningEl = document.getElementById(`warning-${slotName}`);
    if (!warningEl) return;

    const input = document.getElementById(`slot-${slotName}`);

    // Don't validate empty/null values
    if (!value || value === '') {
        warningEl.textContent = '';
        if (input) {
            input.classList.remove('invalid');
        }
        return;
    }

    // Check against pattern
    if (!rule.pattern.test(value)) {
        warningEl.textContent = rule.warning;
        if (input) {
            input.classList.add('invalid');
        }
    } else {
        warningEl.textContent = '';
        if (input) {
            input.classList.remove('invalid');
        }
    }
}

/**
 * Validate all fields on the current entry
 */
function validateAllFields() {
    for (const slotName of Object.keys(VALIDATION_RULES)) {
        const input = document.getElementById(`slot-${slotName}`);
        if (input) {
            validateSlot(slotName, input.value);
        }
    }
}

// Add CSS for invalid state
const style = document.createElement('style');
style.textContent = `
    .slot-input.invalid {
        border-color: var(--warning) !important;
    }
`;
document.head.appendChild(style);

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', initValidation);

// Re-initialize when HTMX swaps content
document.addEventListener('htmx:afterSwap', initValidation);
