/**
 * Theme Switcher for Dozentenmanager
 *
 * Allows users to switch between different color themes
 * and persists their preference in localStorage
 */

// Available themes
const themes = [
    { id: 'academic-blue', name: 'Academic Blue', icon: 'fa-graduation-cap' },
    { id: 'modern-mint', name: 'Modern Mint', icon: 'fa-leaf' },
    { id: 'university-navy', name: 'University Navy', icon: 'fa-university' }
];

// Get current theme index
let currentThemeIndex = 0;

/**
 * Initialize theme on page load
 */
function initTheme() {
    // Check localStorage for saved theme
    const savedTheme = localStorage.getItem('dozentenmanager-theme');

    if (savedTheme) {
        // Find the index of saved theme
        currentThemeIndex = themes.findIndex(t => t.id === savedTheme);
        if (currentThemeIndex === -1) currentThemeIndex = 0;

        // Apply the saved theme
        applyTheme(themes[currentThemeIndex].id);
    } else {
        // Apply default theme (Academic Blue)
        applyTheme(themes[0].id);
    }

    // Update button icon
    updateThemeButton();
}

/**
 * Apply a theme to the document
 */
function applyTheme(themeId) {
    document.documentElement.setAttribute('data-theme', themeId);
    localStorage.setItem('dozentenmanager-theme', themeId);
}

/**
 * Cycle to the next theme
 */
function cycleTheme() {
    // Move to next theme
    currentThemeIndex = (currentThemeIndex + 1) % themes.length;

    const nextTheme = themes[currentThemeIndex];

    // Apply the theme
    applyTheme(nextTheme.id);

    // Update button
    updateThemeButton();

    // Show notification
    showThemeNotification(nextTheme.name);
}

/**
 * Update the theme button icon and tooltip
 */
function updateThemeButton() {
    const button = document.getElementById('theme-switcher-btn');
    const icon = document.getElementById('theme-icon');

    if (button && icon) {
        const currentTheme = themes[currentThemeIndex];

        // Update icon
        icon.className = `fas ${currentTheme.icon}`;

        // Update tooltip
        button.setAttribute('title', `Aktuelles Theme: ${currentTheme.name}`);
    }
}

/**
 * Show a brief notification when theme changes
 */
function showThemeNotification(themeName) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'notification is-info is-light theme-notification';
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 9999;
        min-width: 250px;
        animation: slideIn 0.3s ease-out;
    `;

    notification.innerHTML = `
        <button class="delete"></button>
        <strong>Theme geändert</strong><br>
        <small>Aktuelles Theme: ${themeName}</small>
    `;

    // Add to body
    document.body.appendChild(notification);

    // Add close button handler
    const deleteBtn = notification.querySelector('.delete');
    deleteBtn.addEventListener('click', () => {
        notification.remove();
    });

    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }
    }, 3000);
}

// Add CSS animations for notification
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }

    .theme-notification {
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
`;
document.head.appendChild(style);

// Initialize theme when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initTheme();

    // Add click handler to theme switcher button
    const themeSwitcherBtn = document.getElementById('theme-switcher-btn');
    if (themeSwitcherBtn) {
        themeSwitcherBtn.addEventListener('click', cycleTheme);
    }
});
