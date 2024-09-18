document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('register-form');
    const loginForm = document.querySelector('#login-form');

    if (registerForm) {
        registerForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(registerForm);
            fetch('/register', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = data.redirect;
                } else {
                    const errorContainer = document.querySelector('.error-messages');
                    errorContainer.innerHTML = '';
                    for (const [field, errors] of Object.entries(data.errors)) {
                        const errorElement = document.createElement('p');
                        errorElement.textContent = `${field}: ${errors}`;
                        errorContainer.appendChild(errorElement);
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An unexpected error occurred. Please try again.');
            });
        });
    }

    if (loginForm) {
        loginForm.addEventListener('submit', handleFormSubmit);
    }

    function handleFormSubmit(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);
        const url = form.action;

        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = data.redirect;
            } else {
                displayErrors(data.errors || {'error': data.message});
            }
        })
        .catch(error => {
            console.error('Error:', error);
            displayErrors({'error': 'An unexpected error occurred'});
        });
    }

    function displayErrors(errors) {
        const errorContainer = document.querySelector('.error-messages');
        errorContainer.innerHTML = '';
        for (const [field, message] of Object.entries(errors)) {
            const errorElement = document.createElement('p');
            errorElement.textContent = `${field}: ${message}`;
            errorContainer.appendChild(errorElement);
        }
    }

    const websiteList = document.getElementById('website-list');
    const addButton = document.getElementById('add-button');
    const websiteUrlInput = document.getElementById('website-url');
    const checkIntervalInput = document.getElementById('check-interval');

    function fetchWebsites() {
        console.log('Fetching websites...');
        fetch('/api/websites')
            .then(response => response.json())
            .then(websites => {
                console.log('Fetched websites:', websites);
                websiteList.innerHTML = ''; // Clear the existing list
                
                // Sort websites by date_added in descending order
                websites.sort((a, b) => new Date(b.date_added) - new Date(a.date_added));
                
                websites.forEach(website => {
                    const websiteItem = createWebsiteItem(website);
                    websiteList.appendChild(websiteItem);
                });
            })
            .catch(error => console.error('Error fetching websites:', error));
    }

    function createWebsiteItem(website) {
        const item = document.createElement('div');
        item.className = 'website-item';
        item.dataset.id = website.id;
        item.innerHTML = `
            <div class="status-indicator ${getStatusClass(website)}"></div>
            <div class="website-info">
                <a href="${website.url}" target="_blank" rel="noopener noreferrer" class="website-link">${website.url}</a>
                <div class="last-visited">Last visited: ${website.last_visited ? new Date(website.last_visited + 'Z').toLocaleString() : 'Never'}</div>
            </div>
            <div class="website-actions">
                <input type="number" class="interval-input" value="${website.check_interval}" min="1">
                <button class="update-interval" disabled>Update Interval</button>
                <button class="remove-button">Remove</button>
            </div>
        `;

        const removeButton = item.querySelector('.remove-button');
        removeButton.addEventListener('click', () => removeWebsite(website.id));

        const updateIntervalButton = item.querySelector('.update-interval');
        const intervalInput = item.querySelector('.interval-input');
        let originalInterval = website.check_interval;

        intervalInput.addEventListener('input', () => {
            if (intervalInput.value !== originalInterval.toString()) {
                updateIntervalButton.disabled = false;
            } else {
                updateIntervalButton.disabled = true;
            }
        });

        updateIntervalButton.addEventListener('click', () => {
            const newInterval = intervalInput.value;
            if (newInterval !== originalInterval.toString()) {
                updateInterval(website.id, newInterval);
                originalInterval = parseInt(newInterval);
                updateIntervalButton.disabled = true;
            }
        });

        const websiteLink = item.querySelector('.website-link');
        websiteLink.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('Website link clicked:', website.url);
            fetch(`/api/websites/${website.id}/visit`, { method: 'POST' })
                .then(response => response.json())
                .then(updatedWebsite => {
                    console.log('Updated website:', updatedWebsite);
                    const statusIndicator = item.querySelector('.status-indicator');
                    statusIndicator.className = `status-indicator ${getStatusClass(updatedWebsite)}`;
                    
                    // Update the last visited time
                    const lastVisitedElement = item.querySelector('.last-visited');
                    lastVisitedElement.textContent = `Last visited: ${new Date(updatedWebsite.last_visited + 'Z').toLocaleString()}`;
                    
                    // Try to open the link in a new tab
                    const newWindow = window.open(website.url, '_blank');
                    if (!newWindow || newWindow.closed || typeof newWindow.closed == 'undefined') {
                        console.error('Pop-up blocked or failed to open new window.');
                        alert('The link could not be opened due to pop-up blocker settings. Please allow pop-ups for this site or use the following URL: ' + website.url);
                        
                        // Create a temporary input element to copy the URL
                        const tempInput = document.createElement('input');
                        tempInput.value = website.url;
                        document.body.appendChild(tempInput);
                        tempInput.select();
                        document.execCommand('copy');
                        document.body.removeChild(tempInput);
                        
                        alert('The URL has been copied to your clipboard.');
                    } else {
                        console.log('New window opened successfully');
                    }
                })
                .catch(error => {
                    console.error('Error marking website as visited:', error);
                    alert('An error occurred while trying to visit the website. Please try again.');
                });
        });

        return item;
    }

    function addWebsite(url, interval) {
        console.log(`Adding website: ${url} with interval: ${interval}`);
        fetch('/api/websites', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url, interval: parseInt(interval) }),
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw err; });
            }
            return response.json();
        })
        .then(newWebsite => {
            console.log('Website added successfully:', newWebsite);
            const websiteItem = createWebsiteItem(newWebsite);
            websiteList.insertBefore(websiteItem, websiteList.firstChild);
            websiteUrlInput.value = '';
            checkIntervalInput.value = '24';
        })
        .catch(error => {
            console.error('Error adding website:', error);
            alert(`Failed to add website: ${error.error || 'Unknown error'}`);
        });
    }

    function removeWebsite(id) {
        fetch(`/api/websites/${id}`, { method: 'DELETE' })
            .then(() => {
                const item = websiteList.querySelector(`.website-item[data-id="${id}"]`);
                if (item) {
                    item.remove();
                }
            })
            .catch(error => console.error('Error removing website:', error));
    }

    function updateInterval(id, newInterval) {
        const item = websiteList.querySelector(`.website-item[data-id="${id}"]`);
        const intervalInput = item.querySelector('.interval-input');
        const updateButton = item.querySelector('.update-interval');

        intervalInput.disabled = true;
        updateButton.disabled = true;
        
        fetch(`/api/websites/${id}/interval`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ interval: parseInt(newInterval) }),
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to update interval');
                }
                return response.json();
            })
            .then(updatedWebsite => {
                intervalInput.value = updatedWebsite.check_interval;
                console.log('Interval updated successfully:', updatedWebsite);
            })
            .catch(error => {
                console.error('Error updating interval:', error);
                alert('Failed to update interval. Please try again.');
                intervalInput.value = newInterval;
            })
            .finally(() => {
                intervalInput.disabled = false;
                updateButton.disabled = true;
            });
    }

    function getStatusClass(website) {
        console.log('Calculating status for website:', website);
        if (!website.is_reachable) {
            console.log('Website is not reachable');
            return 'status-red';
        }
        
        const lastVisited = website.last_visited ? new Date(website.last_visited + 'Z') : null;
        const lastChange = website.last_change ? new Date(website.last_change + 'Z') : null;
        
        if (lastChange && lastVisited && lastChange > lastVisited) {
            console.log('Content changed since last visit');
            return 'status-green';
        }
        
        console.log('No changes or no visit yet');
        return 'status-gray';
    }

    function isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }

    addButton.addEventListener('click', () => {
        console.log('Add button clicked');
        const url = websiteUrlInput.value.trim();
        const interval = checkIntervalInput.value;
        console.log(`Attempting to add website: ${url} with interval: ${interval}`);
        if (url && isValidUrl(url)) {
            addWebsite(url, interval);
        } else {
            console.error('Invalid URL');
            alert('Please enter a valid URL');
        }
    });

    websiteUrlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addButton.click();
        }
    });

    // Add event listener for Enter key on checkIntervalInput
    checkIntervalInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addButton.click();
        }
    });

    // Initial fetch of websites
    fetchWebsites();
});
