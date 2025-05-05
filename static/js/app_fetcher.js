// static/js/app-fetcher.js

/**
 * Fetch user's accessible apps from the API
 * @returns {Promise} Promise that resolves to the list of apps
 */
function fetchUserApps() {
    return fetch('/api/user/apps/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            // Include CSRF token for Django
            'X-CSRFToken': getCookie('csrftoken')
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            return data.apps;
        } else {
            throw new Error(data.error || 'Failed to fetch apps');
        }
    });
}

/**
 * Render app cards to a container element
 * @param {Array} apps - List of app objects
 * @param {HTMLElement} container - Container element to render cards into
 */
function renderAppCards(apps, container) {
    // Clear container
    container.innerHTML = '';
    
    if (apps.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center py-5">
                <div class="alert alert-info">
                    <h4>No applications are available</h4>
                    <p>Contact your administrator to request access to applications.</p>
                </div>
            </div>
        `;
        return;
    }
    
    // Render each app card
    apps.forEach(app => {
        const cardHtml = `
            <div class="col-md-4 mb-4">
                <a href="${app.link}" class="text-decoration-none">
                    <div class="card app-card h-100 shadow-sm" style="background-color: ${app.background_color};">
                        <div class="card-body text-white d-flex flex-column">
                            <div class="d-flex mb-3">
                                <div class="me-3">
                                    <i class="fas ${app.icon} fa-2x"></i>
                                </div>
                                <div>
                                    <h5 class="card-title mb-0">${app.name}</h5>
                                </div>
                            </div>
                            <p class="card-text flex-grow-1">${app.description}</p>
                            <div class="text-end mt-2">
                                <span class="btn btn-sm btn-light">
                                    Launch App <i class="fas fa-arrow-right ms-1"></i>
                                </span>
                            </div>
                        </div>
                    </div>
                </a>
            </div>
        `;
        
        const cardElement = document.createElement('div');
        cardElement.innerHTML = cardHtml;
        container.appendChild(cardElement.firstElementChild);
    });
}

/**
 * Render app links to a navigation menu
 * @param {Array} apps - List of app objects
 * @param {HTMLElement} container - Container element to render links into
 */
function renderAppNavLinks(apps, container) {
    // Clear container
    container.innerHTML = '';
    
    if (apps.length === 0) {
        return;
    }
    
    // Render each app link
    apps.forEach(app => {
        const linkHtml = `
            <li class="nav-item">
                <a href="${app.link}" class="nav-link text-white-50 py-2">
                    <i class="fas ${app.icon} me-2"></i>
                    ${app.name}
                </a>
            </li>
        `;
        
        const linkElement = document.createElement('div');
        linkElement.innerHTML = linkHtml;
        container.appendChild(linkElement.firstElementChild);
    });
}

/**
 * Get CSRF token from cookies
 * @param {string} name - Cookie name
 * @returns {string} Cookie value
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Example usage:
// document.addEventListener('DOMContentLoaded', () => {
//     const appContainer = document.getElementById('app-container');
//     const navContainer = document.querySelector('.sidebar-apps ul');
//     
//     fetchUserApps()
//         .then(apps => {
//             renderAppCards(apps, appContainer);
//             renderAppNavLinks(apps, navContainer);
//         })
//         .catch(error => {
//             console.error('Error fetching apps:', error);
//         });
// });