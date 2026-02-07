// Theme Management Script
// Handles dark/light mode toggle, persistence, and automatic detection

class ThemeManager {
  constructor() {
    this.lightTheme = 'light';
    this.darkTheme = 'dark';
    this.storageKey = 'ogctz-theme';
    this.htmlElement = document.documentElement;
    this.init();
  }

  // Initialize theme on page load
  init() {
    const savedTheme = this.getStoredTheme();
    const systemTheme = this.getSystemTheme();
    const themeToApply = savedTheme || systemTheme;
    
    this.setTheme(themeToApply);
    this.updateFavicon(themeToApply);
    this.setupToggleButton();
    this.watchSystemPreference();
  }

  // Get user's stored theme preference
  getStoredTheme() {
    return localStorage.getItem(this.storageKey);
  }

  // Detect system theme preference
  getSystemTheme() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return this.darkTheme;
    }
    return this.lightTheme;
  }

  // Set theme (light or dark)
  setTheme(theme) {
    if (theme === this.darkTheme) {
      this.htmlElement.classList.add('dark');
      document.body.style.backgroundColor = '#0f172a';
      document.body.style.color = '#f8fafc';
    } else {
      this.htmlElement.classList.remove('dark');
      document.body.style.backgroundColor = '#ffffff';
      document.body.style.color = '#0f172a';
    }
    localStorage.setItem(this.storageKey, theme);
  }

  // Update favicon based on theme
  updateFavicon(theme) {
    const faviconPath = theme === this.darkTheme 
      ? '/static/img/favicons/fav_white' 
      : '/static/img/favicons/fav_org';

    // Update favicon variants
    this.updateFaviconLink('icon16', `${faviconPath}/favicon-16x16.png`);
    this.updateFaviconLink('icon32', `${faviconPath}/favicon-32x32.png`);
    this.updateFaviconLink('icon-ico', `${faviconPath}/favicon.ico`);
    this.updateFaviconLink('apple-touch', `${faviconPath}/apple-touch-icon.png`);
  }

  // Helper to update individual favicon link
  updateFaviconLink(id, href) {
    let link = document.getElementById(id);
    if (!link) {
      link = document.createElement('link');
      link.id = id;
      document.head.appendChild(link);
    }
    
    if (id === 'icon-ico') {
      link.rel = 'icon';
      link.type = 'image/x-icon';
    } else if (id === 'apple-touch') {
      link.rel = 'apple-touch-icon';
    } else {
      link.rel = 'icon';
      link.type = 'image/png';
    }
    link.href = href;
  }

  // Setup theme toggle button
  setupToggleButton() {
    const toggleBtn = document.getElementById('theme-toggle-btn');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => this.toggleTheme());
      this.updateToggleIcon();
    }
  }

  // Toggle between light and dark theme
  toggleTheme() {
    const currentTheme = this.getStoredTheme() || this.getSystemTheme();
    const newTheme = currentTheme === this.lightTheme ? this.darkTheme : this.lightTheme;
    this.setTheme(newTheme);
    this.updateFavicon(newTheme);
    this.updateToggleIcon();
  }

  // Update toggle button icon
  updateToggleIcon() {
    const toggleBtn = document.getElementById('theme-toggle-btn');
    const icon = toggleBtn?.querySelector('svg');
    if (!icon) return;

    const currentTheme = this.getStoredTheme() || this.getSystemTheme();
    const isSun = icon.classList.contains('sun-icon');

    if (currentTheme === this.darkTheme) {
      if (isSun) {
        // Show moon icon when in dark mode
        icon.classList.remove('sun-icon');
        icon.classList.add('moon-icon');
      }
    } else {
      if (!isSun) {
        // Show sun icon when in light mode
        icon.classList.remove('moon-icon');
        icon.classList.add('sun-icon');
      }
    }
  }

  // Watch for system theme changes
  watchSystemPreference() {
    if (!window.matchMedia) return;
    
    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
    darkModeQuery.addListener((e) => {
      // Only apply system preference if user hasn't manually set a preference
      if (!this.getStoredTheme()) {
        const newTheme = e.matches ? this.darkTheme : this.lightTheme;
        this.setTheme(newTheme);
        this.updateFavicon(newTheme);
        this.updateToggleIcon();
      }
    });
  }
}

// Initialize theme manager when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new ThemeManager();
  });
} else {
  new ThemeManager();
}
