// Lucide icons init
document.addEventListener('DOMContentLoaded', () => {
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
});

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
