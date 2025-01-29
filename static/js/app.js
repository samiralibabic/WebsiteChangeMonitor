// Initialize variables at the top level
let websiteUrlInput;
let checkIntervalInput;
let addButton;

// Utility functions
function isValidUrl(string) {
    try {
        new URL(string);
        return string.startsWith('http://') || string.startsWith('https://');
    } catch (_) {
        return false;
    }
}

function getStatusText(website) {
    if (!website.is_reachable) {
        return 'Website is currently unreachable';
    }

    const lastVisited = website.last_visited ? new Date(website.last_visited + 'Z') : null;
    const lastChange = website.last_change ? new Date(website.last_change + 'Z') : null;

    if (lastChange && lastVisited && lastChange > lastVisited) {
        return 'Changes detected since your last visit';
    }

    return 'No new changes';
}

// Helper function to format dates in local time
function formatLocalDateTime(utcDateString) {
    if (!utcDateString) return 'Never';  // Handle null/undefined dates
    
    try {
        // Remove the Z if the string already has a timezone offset
        const cleanDateString = utcDateString.replace(/\+00:00Z$/, '+00:00');
        
        // Parse the date
        const date = new Date(cleanDateString);
        if (isNaN(date.getTime())) {  // Check if date is valid
            console.error('Invalid date:', utcDateString);
            return 'Invalid date';
        }
        
        // Use the browser's locale and 24-hour format
        return new Intl.DateTimeFormat(navigator.language, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
            timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
        }).format(date);
    } catch (error) {
        console.error('Error formatting date:', error, utcDateString);
        return 'Error';
    }
}
// Core functions
async function handleAddWebsite(event) {
    event.preventDefault();

    const urls = websiteUrlInput.value
        .split(/[,;]+/)
        .map(url => url.trim())
        .filter(url => url);

    // Add early return if no valid URLs
    if (urls.length === 0) {
        return;  // Silently return if no URLs provided
    }

    const interval = parseInt(checkIntervalInput.value);

    // Validate interval
    if (isNaN(interval) || interval < 1 || interval > 24) {
        alert('Please enter a valid interval between 1 and 24 hours');
        return;
    }

    // Validate URLs
    const invalidUrls = urls.filter(url => !isValidUrl(url));
    if (invalidUrls.length > 0) {
        alert(`Please enter valid URLs (must start with http:// or https://). Invalid URLs:\n${invalidUrls.join('\n')}`);
        return;
    }

    try {
        let response;
        let data;

        if (urls.length > 1) {
            // Use bulk endpoint for multiple URLs
            response = await fetch('/api/websites/bulk', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    urls: urls,
                    interval: interval
                })
            });
        } else {
            response = await fetch('/api/websites', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: urls[0],
                    interval: interval
                })
            });
        }

        data = await response.json();

        if (response.ok) {
            websiteUrlInput.value = '';
            
            // Show feedback for both single and bulk operations
            const summary = [
                `Added: ${data.added} URL${data.added !== 1 ? 's' : ''}`,
                data.details.skipped.length > 0 ? `Skipped: ${data.details.skipped.length}` : null,
                data.details.failed.length > 0 ? `Failed: ${data.details.failed.length}` : null
            ].filter(Boolean).join('\n');

            // Show detailed feedback if there are skipped or failed URLs
            if (data.details.skipped.length > 0 || data.details.failed.length > 0) {
                let details = [];
                
                if (data.details.skipped.length > 0) {
                    details.push('\nSkipped URLs:');
                    data.details.skipped.forEach(item => {
                        details.push(`${item.url} - ${item.reason}`);
                    });
                }
                
                if (data.details.failed.length > 0) {
                    details.push('\nFailed URLs:');
                    data.details.failed.forEach(item => {
                        details.push(`${item.url} - ${item.reason}`);
                    });
                }

                alert(`${summary}\n${details.join('\n')}`);
            } else if (data.added > 0) {
                alert(summary);
            }
            
            window.location.reload();
        } else {
            throw new Error(data.message || `Server error: ${response.status}`);
        }
    } catch (error) {
        console.error('Full error:', error);
        alert(`Failed to add website(s): ${error.message}`);
    }
}

// Update interval function
window.updateInterval = async function(websiteId) {
    const input = document.querySelector(`input[data-website-id="${websiteId}"]`);
    const updateBtn = input.parentElement.querySelector('.update-btn');
    const interval = parseInt(input.value);

    if (isNaN(interval) || interval < 1 || interval > 24) {
        alert('Please enter a valid interval between 1 and 24 hours');
        return;
    }

    try {
        const response = await fetch(`/api/websites/${websiteId}/interval`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                interval: interval
            })
        });

        const data = await response.json();

        if (response.ok) {
            updateBtn.disabled = true;
            window.location.reload();
        } else {
            throw new Error(data.message || 'Failed to update interval');
        }
    } catch (error) {
        console.error('Error:', error);
        alert(error.message || 'Failed to update interval');
    }
};

// Add input change handler to enable/disable update button
function setupIntervalInputs() {
    document.querySelectorAll('.interval-input').forEach(input => {
        const updateBtn = input.parentElement.querySelector('.update-btn');
        const originalValue = input.value;
        
        // Initially disable update button
        updateBtn.disabled = true;
        
        // Enable/disable button based on value changes
        input.addEventListener('input', () => {
            const newValue = input.value;
            const isValid = !isNaN(newValue) && newValue >= 1 && newValue <= 24;
            updateBtn.disabled = newValue === originalValue || !isValid;
        });
        
        // Handle Enter key
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !updateBtn.disabled) {
                e.preventDefault();
                updateInterval(input.dataset.websiteId);
            }
        });
    });
}

// Delete website function
window.deleteWebsite = async function(websiteId) {
    if (!confirm('Are you sure you want to delete this website?')) {
        return;
    }

    try {
        const response = await fetch(`/api/websites/${websiteId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            window.location.reload();
        } else {
            const data = await response.json();
            throw new Error(data.message || 'Failed to delete website');
        }
    } catch (error) {
        console.error('Error:', error);
        alert(error.message || 'Failed to delete website');
    }
};

// Move updateLastVisited function definition before DOMContentLoaded
async function updateLastVisited(websiteId) {
    try {
        const response = await fetch(`/api/websites/${websiteId}/visit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (response.ok) {
            const data = await response.json();
            const linkCard = document.querySelector(`[data-website-id="${websiteId}"]`);
            const visitedSpan = linkCard.querySelector('.visit-time .datetime');
            if (visitedSpan && data.last_visited) {
                visitedSpan.setAttribute('data-utc', data.last_visited);
                visitedSpan.textContent = formatLocalDateTime(data.last_visited);
                
                // Update status dot
                const statusDot = linkCard.querySelector('.status-dot');
                if (statusDot) {
                    statusDot.classList.remove('status-green');
                    statusDot.classList.add('status-gray');
                }
            }
        } else {
            console.error('Failed to update last visited timestamp');
        }
    } catch (error) {
        console.error('Error updating last visited:', error);
    }
}

// Add the remove all function
async function removeAllWebsites() {
    if (!confirm('Are you sure you want to remove all websites? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch('/api/websites/all', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (response.ok) {
            window.location.reload();
        } else {
            const data = await response.json();
            throw new Error(data.message || 'Failed to remove all websites');
        }
    } catch (error) {
        console.error('Error:', error);
        alert(error.message || 'Failed to remove all websites');
    }
}

// Initialize everything when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize input elements
    websiteUrlInput = document.getElementById('website-url');
    checkIntervalInput = document.getElementById('check-interval');
    addButton = document.getElementById('add-button');

    // Set up event listeners
    if (addButton) {
        addButton.addEventListener('click', handleAddWebsite);
    }

    if (websiteUrlInput) {
        websiteUrlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleAddWebsite(e);
            }
        });
    }

    if (checkIntervalInput) {
        checkIntervalInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleAddWebsite(e);
            }
        });
    }

    // Set up notification handlers
    const notificationEmail = document.getElementById('notification-email');
    const notificationsEnabled = document.getElementById('notifications-enabled');
    const saveNotifications = document.getElementById('save-notifications');
    
    if (saveNotifications) {
        saveNotifications.addEventListener('click', async () => {
            const email = notificationEmail.value.trim();
            const enabled = notificationsEnabled.checked;
            
            if (enabled && !email) {
                alert('Please enter an email address to enable notifications');
                return;
            }
            
            try {
                const response = await fetch('/api/user/notifications', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        email: email,
                        enabled: enabled
                    }),
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.message || 'Failed to save notification settings');
                }

                alert('Notification settings saved successfully');
            } catch (error) {
                console.error('Error saving notification settings:', error);
                alert(error.message || 'Failed to save notification settings. Please try again.');
            }
        });
    }

    // Handle paste events to support all use cases
    websiteUrlInput.addEventListener('paste', (e) => {
        e.preventDefault();
        const pastedText = e.clipboardData.getData('text');
        
        // Get cursor position and current value
        const startPos = websiteUrlInput.selectionStart;
        const endPos = websiteUrlInput.selectionEnd;
        const currentValue = websiteUrlInput.value;
        
        // Check if pasted text contains multiple URLs
        const hasMultipleUrls = /[\n,;\s]/.test(pastedText);
        
        if (hasMultipleUrls) {
            // Handle multiple URLs
            const urls = pastedText
                .split(/[\n,;\s]+/)
                .map(url => url.trim())
                .filter(url => url);
                
            // Check if we need a comma (if there's content and it doesn't end with a comma)
            const needsComma = currentValue && 
                              startPos === currentValue.length && 
                              !currentValue.trim().endsWith(',');
            const prefix = needsComma ? ', ' : '';
            
            // Join URLs with commas
            const formattedUrls = prefix + urls.join(', ');
            
            // Insert at cursor position
            websiteUrlInput.value = currentValue.substring(0, startPos) + 
                                  formattedUrls + 
                                  currentValue.substring(endPos);
                                  
            // Move cursor to end of pasted text
            const newPos = startPos + formattedUrls.length;
            websiteUrlInput.setSelectionRange(newPos, newPos);
        } else {
            // Handle single URL
            // Check if we need a comma
            const needsComma = currentValue && 
                              startPos === currentValue.length && 
                              !currentValue.trim().endsWith(',');
            const prefix = needsComma ? ', ' : '';
            
            // Insert at cursor position
            websiteUrlInput.value = currentValue.substring(0, startPos) + 
                                  prefix + pastedText + 
                                  currentValue.substring(endPos);
                                  
            // Move cursor after pasted text
            const newPos = startPos + prefix.length + pastedText.length;
            websiteUrlInput.setSelectionRange(newPos, newPos);
        }
    });

    // Setup interval input handlers
    setupIntervalInputs();

    // Convert all UTC timestamps to local time
    document.querySelectorAll('.datetime').forEach(element => {
        const utcDate = element.getAttribute('data-utc');
        element.textContent = formatLocalDateTime(utcDate);
    });

    // Set up remove all button
    const removeAllButton = document.getElementById('remove-all-button');
    if (removeAllButton) {
        removeAllButton.addEventListener('click', removeAllWebsites);
    }

    const monitor = new WebsiteMonitor();

    // Add click handler to links
    document.querySelectorAll('.link-url').forEach(link => {
        link.addEventListener('click', (e) => {
            const websiteId = link.closest('.link-card').dataset.websiteId;
            updateLastVisited(websiteId);
        });
    });
});

class WebsiteCard {
    constructor(cardElement) {
        this.card = cardElement;
        this.websiteId = cardElement.dataset.websiteId;
        this.statusDot = cardElement.querySelector('.status-dot');
        this.visitedSpan = cardElement.querySelector('.visit-time .datetime');
        this.lastCheckSpan = cardElement.querySelector('.check-time .datetime');
        this.bindEvents();
    }

    bindEvents() {
        const link = this.card.querySelector('.link-url');
        link.addEventListener('click', () => this.handleVisit());
    }

    async handleVisit() {
        try {
            const response = await fetch(`/api/websites/${this.websiteId}/visit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            if (response.ok) {
                const data = await response.json();
                this.updateUI(data);
            }
        } catch (error) {
            console.error('Error updating visit:', error);
        }
    }

    updateUI(data) {
        // Update timestamps
        if (data.last_visited) {
            this.visitedSpan.setAttribute('data-utc', data.last_visited);
            this.visitedSpan.textContent = formatLocalDateTime(data.last_visited);
        }
        if (data.last_check) {
            this.lastCheckSpan.setAttribute('data-utc', data.last_check);
            this.lastCheckSpan.textContent = formatLocalDateTime(data.last_check);
        }
        
        // Update status
        this.statusDot.className = 'status-dot';
        if (!data.is_reachable) {
            this.statusDot.classList.add('status-red');
        } else if (data.last_check > data.last_visited) {
            this.statusDot.classList.add('status-green');
        } else {
            this.statusDot.classList.add('status-gray');
        }
    }
}

class WebsiteMonitor {
    constructor() {
        this.cards = new Map();
        this.initializeCards();
        this.startPolling();
    }

    initializeCards() {
        document.querySelectorAll('.link-card').forEach(cardElement => {
            const card = new WebsiteCard(cardElement);
            this.cards.set(card.websiteId, card);
        });
    }

    async pollUpdates() {
        try {
            const response = await fetch('/api/websites');
            const websites = await response.json();
            
            websites.forEach(website => {
                const card = this.cards.get(website.id.toString());
                if (card) {
                    card.updateUI(website);
                }
            });
        } catch (error) {
            console.error('Error polling updates:', error);
        }
    }

    startPolling() {
        // Poll every 30 seconds
        setInterval(() => this.pollUpdates(), 30000);
    }
}

