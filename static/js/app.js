// ============ API Helper ============
const API_URL = '';

async function apiRequest(endpoint, method = 'GET', data = null, requireAuth = false) {
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (requireAuth) {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '/faculty/login';
            return;
        }
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const options = {
        method,
        headers
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_URL}${endpoint}`, options);
        
        const result = await response.json();
        
        if (response.status === 401) {
            // Only redirect if it's a protected API call (requireAuth = true)
            // For login attempts, just throw the error to show the message
            if (requireAuth) {
                localStorage.removeItem('token');
                localStorage.removeItem('userType');
                localStorage.removeItem('userName');
                const userType = localStorage.getItem('userType');
                window.location.href = userType === 'admin' ? '/admin/login' : '/faculty/login';
                return;
            }
            throw new Error(result.detail || 'Invalid credentials');
        }
        
        if (!response.ok) {
            throw new Error(result.detail || 'Something went wrong');
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ============ Alert Functions ============
function showAlert(message, type = 'error') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    const container = document.querySelector('.auth-card') || document.querySelector('.container') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// ============ Loading Functions ============
function showLoading() {
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.id = 'loadingOverlay';
    overlay.innerHTML = '<div class="spinner"></div>';
    document.body.appendChild(overlay);
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.remove();
    }
}

// ============ Auth Functions ============
function isLoggedIn() {
    return localStorage.getItem('token') !== null;
}

function getUserType() {
    return localStorage.getItem('userType');
}

function getUserName() {
    return localStorage.getItem('userName');
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('userType');
    localStorage.removeItem('userName');
    window.location.href = '/';
}

// ============ Format Functions ============
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-IN', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Period timings cache (loaded from API)
let periodTimingsCache = null;

// Load period timings from API
async function loadPeriodTimings() {
    if (periodTimingsCache) return periodTimingsCache;
    
    try {
        const response = await fetch('/api/period-timings');
        periodTimingsCache = await response.json();
        return periodTimingsCache;
    } catch (error) {
        console.error('Error loading period timings:', error);
        // Fallback to default timings
        return {
            1: '08:00 AM - 08:45 AM',
            2: '08:45 AM - 09:30 AM',
            3: '09:45 AM - 10:30 AM',
            4: '10:30 AM - 11:15 AM',
            5: '11:15 AM - 12:00 PM',
            6: '01:00 PM - 01:45 PM',
            7: '01:45 PM - 02:30 PM',
            8: '02:30 PM - 03:15 PM',
            9: '03:30 PM - 04:15 PM'
        };
    }
}

// Initialize period timings on page load
loadPeriodTimings();

function getPeriodTime(period) {
    // Use cached timings if available
    if (periodTimingsCache && periodTimingsCache[period]) {
        return periodTimingsCache[period];
    }
    
    // Fallback to default timings
    const times = {
        1: '08:00 AM - 08:45 AM',
        2: '08:45 AM - 09:30 AM',
        3: '09:45 AM - 10:30 AM',
        4: '10:30 AM - 11:15 AM',
        5: '11:15 AM - 12:00 PM',
        6: '01:00 PM - 01:45 PM',
        7: '01:45 PM - 02:30 PM',
        8: '02:30 PM - 03:15 PM',
        9: '03:30 PM - 04:15 PM'
    };
    return times[period] || 'Unknown';
}

function getOrdinal(n) {
    const s = ['th', 'st', 'nd', 'rd'];
    const v = n % 100;
    return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

// ============ Parse Markdown (simple) ============
function parseMarkdown(text) {
    // Bold
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Newlines
    text = text.replace(/\n/g, '<br>');
    // Emojis are already supported
    return text;
}
