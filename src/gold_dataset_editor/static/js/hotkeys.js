/**
 * Gold Dataset Editor - Keyboard Shortcuts
 */

// Boolean slots for tri-state keyboard control
const BOOL_SLOTS = ['is_first_time', 'has_contraindications', 'is_consultation', 'can_visit_center'];

document.addEventListener('keydown', function(event) {
    // Ignore shortcuts when typing in input fields (except for specific cases)
    const target = event.target;
    const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA';

    // Handle Escape key - always clears focus
    if (event.key === 'Escape') {
        target.blur();
        window.activeSlot = null;
        return;
    }

    // Handle Ctrl+S - Save
    if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        saveFile();
        return;
    }

    // Skip other shortcuts if typing in input
    if (isInput) {
        // Allow 1/2/3 keys in tri-state focused elements
        if (target.classList.contains('tristate') || target.closest('.tristate')) {
            handleTristateKey(event, target.closest('.tristate'));
        }
        return;
    }

    // Navigation shortcuts
    switch (event.key) {
        case 'j':
        case 'ArrowDown':
            event.preventDefault();
            nextEntry();
            break;

        case 'k':
        case 'ArrowUp':
            event.preventDefault();
            prevEntry();
            break;

        case 'g':
            // Jump to entry
            event.preventDefault();
            jumpToEntry();
            break;

        case 'r':
            // Toggle reviewed
            event.preventDefault();
            toggleReviewed();
            break;

        case 's':
            // Skip file
            event.preventDefault();
            skipFile();
            break;

        case '/':
            // Focus search
            event.preventDefault();
            const searchInput = document.getElementById('search-input');
            if (searchInput) {
                searchInput.focus();
            }
            break;

        case '1':
        case '2':
        case '3':
            // Handle tri-state for focused bool slot
            if (window.activeSlot && BOOL_SLOTS.includes(window.activeSlot)) {
                event.preventDefault();
                handleTristateKeyForSlot(event.key, window.activeSlot);
            }
            break;

        case 'Tab':
            // Navigate between slots
            if (event.shiftKey) {
                // Previous slot
                focusPreviousSlot();
            } else {
                // Next slot
                focusNextSlot();
            }
            break;
    }
});

/**
 * Handle 1/2/3 keys for tri-state toggle
 */
function handleTristateKey(event, tristate) {
    if (!tristate) return;

    const slotName = tristate.dataset.slot;
    if (!slotName) return;

    switch (event.key) {
        case '1':
            event.preventDefault();
            setBoolSlot(slotName, true);
            break;
        case '2':
            event.preventDefault();
            setBoolSlot(slotName, false);
            break;
        case '3':
            event.preventDefault();
            setBoolSlot(slotName, null);
            break;
    }
}

/**
 * Handle tri-state key for a specific slot
 */
function handleTristateKeyForSlot(key, slotName) {
    switch (key) {
        case '1':
            setBoolSlot(slotName, true);
            break;
        case '2':
            setBoolSlot(slotName, false);
            break;
        case '3':
            setBoolSlot(slotName, null);
            break;
    }
}

/**
 * Focus the next slot input
 */
function focusNextSlot() {
    const slots = Array.from(document.querySelectorAll('.slot-input, .tristate'));
    const currentIndex = slots.findIndex(el =>
        el === document.activeElement ||
        el.contains(document.activeElement)
    );

    if (currentIndex >= 0 && currentIndex < slots.length - 1) {
        const nextSlot = slots[currentIndex + 1];
        if (nextSlot.classList.contains('tristate')) {
            nextSlot.focus();
            window.activeSlot = nextSlot.dataset.slot;
        } else {
            nextSlot.focus();
            window.activeSlot = nextSlot.name;
        }
    }
}

/**
 * Focus the previous slot input
 */
function focusPreviousSlot() {
    const slots = Array.from(document.querySelectorAll('.slot-input, .tristate'));
    const currentIndex = slots.findIndex(el =>
        el === document.activeElement ||
        el.contains(document.activeElement)
    );

    if (currentIndex > 0) {
        const prevSlot = slots[currentIndex - 1];
        if (prevSlot.classList.contains('tristate')) {
            prevSlot.focus();
            window.activeSlot = prevSlot.dataset.slot;
        } else {
            prevSlot.focus();
            window.activeSlot = prevSlot.name;
        }
    }
}

// Allow tri-state to receive keyboard focus
document.addEventListener('click', function(event) {
    const tristate = event.target.closest('.tristate');
    if (tristate) {
        tristate.focus();
        window.activeSlot = tristate.dataset.slot;
    }
});
