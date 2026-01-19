/**
 * Gold Dataset Editor - Main Application Logic
 */

// Global state
window.currentFileId = null;
window.currentEntryIndex = 0;
window.totalEntries = 0;
window.hasUnsavedChanges = false;
window.activeSlot = null;

/**
 * Select a file from the sidebar
 */
function selectFile(element, fileId) {
    // Update active state in sidebar
    document.querySelectorAll('.file-item').forEach(item => {
        item.classList.remove('active');
    });
    element.closest('.file-item').classList.add('active');

    // Update global state
    window.currentFileId = fileId;
    window.currentEntryIndex = 0;

    // Total entries will be updated when content loads
    const fileContent = document.querySelector('.file-content');
    if (fileContent) {
        window.totalEntries = parseInt(fileContent.dataset.totalEntries) || 0;
    }
}

/**
 * Navigate to the next entry
 */
function nextEntry() {
    if (window.currentFileId && window.currentEntryIndex < window.totalEntries - 1) {
        loadEntry(window.currentEntryIndex + 1);
    }
}

/**
 * Navigate to the previous entry
 */
function prevEntry() {
    if (window.currentFileId && window.currentEntryIndex > 0) {
        loadEntry(window.currentEntryIndex - 1);
    }
}

/**
 * Load a specific entry by index
 */
function loadEntry(index) {
    if (!window.currentFileId) return;

    window.currentEntryIndex = index;
    const container = document.getElementById('entry-container');
    if (container) {
        htmx.ajax('GET', `/partial/entry/${window.currentFileId}/${index}`, {
            target: '#entry-container',
            swap: 'innerHTML'
        });
    }
    updateNavigationButtons();
}

/**
 * Update navigation button states
 */
function updateNavigationButtons() {
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');

    if (prevBtn) {
        prevBtn.disabled = window.currentEntryIndex <= 0;
    }
    if (nextBtn) {
        nextBtn.disabled = window.currentEntryIndex >= window.totalEntries - 1;
    }
}

/**
 * Update a slot value via API
 */
async function updateSlot(slotName, value) {
    if (!window.currentFileId) return;

    // Convert empty string to null
    const actualValue = value === '' ? null : value;

    try {
        const response = await fetch(`/api/files/${window.currentFileId}/entries/${window.currentEntryIndex}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                slots: { [slotName]: actualValue }
            })
        });

        if (response.ok) {
            markAsUnsaved();
            // Validate after update
            validateSlot(slotName, actualValue);
        } else {
            showToast('Failed to update slot', 'error');
        }
    } catch (error) {
        console.error('Error updating slot:', error);
        showToast('Error updating slot', 'error');
    }
}

/**
 * Clear a slot (set to null)
 */
function clearSlot(slotName) {
    const input = document.getElementById(`slot-${slotName}`);
    if (input) {
        input.value = '';
        updateSlot(slotName, null);
    }
}

/**
 * Set a boolean slot value
 */
async function setBoolSlot(slotName, value) {
    if (!window.currentFileId) return;

    try {
        const response = await fetch(`/api/files/${window.currentFileId}/entries/${window.currentEntryIndex}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                slots: { [slotName]: value }
            })
        });

        if (response.ok) {
            markAsUnsaved();
            // Update UI
            const tristate = document.querySelector(`.tristate[data-slot="${slotName}"]`);
            if (tristate) {
                tristate.querySelectorAll('.ts-btn').forEach(btn => btn.classList.remove('active'));
                if (value === true) {
                    tristate.querySelector('.ts-true').classList.add('active');
                } else if (value === false) {
                    tristate.querySelector('.ts-false').classList.add('active');
                } else {
                    tristate.querySelector('.ts-null').classList.add('active');
                }
                tristate.dataset.value = JSON.stringify(value);
            }
        } else {
            showToast('Failed to update slot', 'error');
        }
    } catch (error) {
        console.error('Error updating bool slot:', error);
        showToast('Error updating slot', 'error');
    }
}

/**
 * Update evidence for a slot
 */
async function updateEvidence(slotName, value) {
    if (!window.currentFileId) return;

    const actualValue = value === '' ? null : value;

    try {
        const response = await fetch(`/api/files/${window.currentFileId}/entries/${window.currentEntryIndex}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                evidence: { [slotName]: actualValue }
            })
        });

        if (response.ok) {
            markAsUnsaved();
        } else {
            showToast('Failed to update evidence', 'error');
        }
    } catch (error) {
        console.error('Error updating evidence:', error);
        showToast('Error updating evidence', 'error');
    }
}

/**
 * Update main message role (syncs across all entries with same ts_ms)
 */
async function updateMessageRole(role) {
    if (!window.currentFileId) return;

    try {
        const response = await fetch(`/api/files/${window.currentFileId}/entries/${window.currentEntryIndex}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message_role: role })
        });

        if (response.ok) {
            const data = await response.json();
            markAsUnsaved();
            // Update CSS class for visual feedback
            const msgBox = document.querySelector('.message-box');
            if (msgBox) {
                msgBox.classList.remove('client', 'brand');
                msgBox.classList.add(role);
            }
            // Show sync feedback if other entries were updated
            if (data.synced_count > 0) {
                showToast(`Role synced to ${data.synced_count} other entries`, 'success');
            }
        } else {
            showToast('Failed to update role', 'error');
        }
    } catch (error) {
        console.error('Error updating message role:', error);
        showToast('Error updating role', 'error');
    }
}

/**
 * Update context message role (syncs across all entries with same ts_ms)
 */
async function updateContextRole(contextIndex, role) {
    if (!window.currentFileId) return;

    try {
        const response = await fetch(`/api/files/${window.currentFileId}/entries/${window.currentEntryIndex}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ context_updates: [{ index: contextIndex, role: role }] })
        });

        if (response.ok) {
            const data = await response.json();
            markAsUnsaved();
            // Update CSS class for visual feedback
            const ctxMsgs = document.querySelectorAll('.context-msg');
            if (ctxMsgs[contextIndex]) {
                ctxMsgs[contextIndex].classList.remove('client', 'brand');
                ctxMsgs[contextIndex].classList.add(role);
            }
            // Show sync feedback if other entries were updated
            if (data.synced_count > 0) {
                showToast(`Role synced to ${data.synced_count} other entries`, 'success');
            }
        } else {
            showToast('Failed to update context role', 'error');
        }
    } catch (error) {
        console.error('Error updating context role:', error);
        showToast('Error updating context role', 'error');
    }
}

/**
 * Update QA hint
 */
async function updateQaHint(value) {
    if (!window.currentFileId) return;

    const actualValue = value === '' ? null : value;

    try {
        const response = await fetch(`/api/files/${window.currentFileId}/entries/${window.currentEntryIndex}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                qa_hint: actualValue
            })
        });

        if (response.ok) {
            markAsUnsaved();
        } else {
            showToast('Failed to update QA hint', 'error');
        }
    } catch (error) {
        console.error('Error updating QA hint:', error);
        showToast('Error updating QA hint', 'error');
    }
}

/**
 * Toggle reviewed status
 */
async function toggleReviewed() {
    if (!window.currentFileId) return;

    try {
        const response = await fetch(`/api/files/${window.currentFileId}/entries/${window.currentEntryIndex}/reviewed`, {
            method: 'POST',
        });

        if (response.ok) {
            const data = await response.json();
            markAsUnsaved();

            // Update button
            const btn = document.getElementById('reviewed-btn');
            if (btn) {
                if (data.entry.reviewed) {
                    btn.classList.remove('btn-secondary');
                    btn.classList.add('btn-success');
                    btn.textContent = 'Reviewed';
                } else {
                    btn.classList.remove('btn-success');
                    btn.classList.add('btn-secondary');
                    btn.textContent = 'Mark as Reviewed';
                }
            }

            // Update sidebar item color
            const fileItem = document.querySelector(`.file-item[data-file-id="${window.currentFileId}"]`);
            if (fileItem) {
                if (data.entry.reviewed) {
                    fileItem.classList.add('reviewed');
                } else {
                    fileItem.classList.remove('reviewed');
                }
            }
        } else {
            showToast('Failed to toggle reviewed status', 'error');
        }
    } catch (error) {
        console.error('Error toggling reviewed:', error);
        showToast('Error toggling reviewed status', 'error');
    }
}

/**
 * Save changes to file
 */
async function saveFile() {
    if (!window.currentFileId) return;

    try {
        const response = await fetch(`/api/files/${window.currentFileId}/save`, {
            method: 'POST',
        });

        if (response.ok) {
            const data = await response.json();
            markAsSaved();
            showToast(data.message, 'success');
        } else {
            showToast('Failed to save file', 'error');
        }
    } catch (error) {
        console.error('Error saving file:', error);
        showToast('Error saving file', 'error');
    }
}

/**
 * Mark current entry as unsaved
 */
function markAsUnsaved() {
    window.hasUnsavedChanges = true;
    const saveBtn = document.getElementById('save-btn');
    if (saveBtn) {
        saveBtn.textContent = 'Save *';
    }
    const entryCard = document.querySelector('.entry-card');
    if (entryCard) {
        entryCard.classList.add('unsaved');
    }
    // Add/show unsaved badge
    const entryId = document.querySelector('.entry-id');
    if (entryId && !entryId.querySelector('.unsaved-badge')) {
        const badge = document.createElement('span');
        badge.className = 'unsaved-badge';
        badge.textContent = 'Unsaved';
        entryId.appendChild(badge);
    }
}

/**
 * Mark as saved
 */
function markAsSaved() {
    window.hasUnsavedChanges = false;
    const saveBtn = document.getElementById('save-btn');
    if (saveBtn) {
        saveBtn.textContent = 'Save';
    }
    const entryCard = document.querySelector('.entry-card');
    if (entryCard) {
        entryCard.classList.remove('unsaved');
    }
    const badge = document.querySelector('.unsaved-badge');
    if (badge) {
        badge.remove();
    }
}

/**
 * Set the currently active slot (for keyboard shortcuts)
 */
function setActiveSlot(slotName) {
    window.activeSlot = slotName;
}

/**
 * Show a toast notification
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    // Auto-remove after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Initialize when file content loads
document.addEventListener('htmx:afterSwap', function(event) {
    // Update total entries when file content loads
    const fileContent = document.querySelector('.file-content');
    if (fileContent && fileContent.dataset.totalEntries) {
        window.totalEntries = parseInt(fileContent.dataset.totalEntries);
        window.currentFileId = fileContent.dataset.fileId;
    }
    updateNavigationButtons();
});

// Warn before leaving with unsaved changes
window.addEventListener('beforeunload', function(event) {
    if (window.hasUnsavedChanges) {
        event.preventDefault();
        event.returnValue = '';
    }
});
