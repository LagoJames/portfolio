// Lucide icons init
document.addEventListener('DOMContentLoaded', () => {
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
  // Sync theme toggle icon with current theme on load
  var icon = document.getElementById('theme-toggle-icon');
  if (icon) {
    var isLight = document.documentElement.classList.contains('light');
    icon.setAttribute('data-lucide', isLight ? 'moon' : 'sun');
    if (typeof lucide !== 'undefined') lucide.createIcons();
  }
});

// Theme toggle — cycles between light and dark, stores manual preference.
// On a fresh visit (no preference stored) the site auto-detects by time of day.
window.toggleTheme = function () {
  var html = document.documentElement;
  var isLight = html.classList.contains('light');
  if (isLight) {
    html.classList.remove('light');
    localStorage.setItem('theme', 'dark');
  } else {
    html.classList.add('light');
    localStorage.setItem('theme', 'light');
  }
  var icon = document.getElementById('theme-toggle-icon');
  if (icon) {
    icon.setAttribute('data-lucide', isLight ? 'sun' : 'moon');
    if (typeof lucide !== 'undefined') lucide.createIcons();
  }
};

// Alpine.js store for contact form
document.addEventListener('alpine:init', () => {
  Alpine.store('contactForm', {
    sending: false,
    sent: false,
    error: null,

    async submit(formData) {
      this.sending = true;
      this.error = null;
      try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content ||
                          document.querySelector('#csrf_token')?.value || '';
        const resp = await fetch('/api/contact', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
          },
          body: JSON.stringify(formData),
        });
        const data = await resp.json();
        if (data.success) {
          this.sent = true;
        } else {
          this.error = data.error || 'Something went wrong.';
        }
      } catch (e) {
        this.error = 'Network error. Email me directly at lago@lagobrian.com';
      } finally {
        this.sending = false;
      }
    }
  });
});
