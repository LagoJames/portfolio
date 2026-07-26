# Codebase Audit — 2026-03-28

Findings from a full review of templates, routes, models, migrations, and static assets.
Grouped by severity. Not all items need immediate action — context notes are included.

---

## CRITICAL

### 1. Navbar references wrong field on `ActiveProject` model
**File:** `app/templates/public/partials/navbar.html` lines 54, 57
**File:** `app/models.py`
The navbar template uses `current_active_project.title` and `current_active_project.slug` to render the "Working on:" badge and link to the project detail page. The `ActiveProject` model does not have `.title` or `.slug` — it has `.project_name`. If `current_active_project` is ever set, this will crash with an `AttributeError` or silently render nothing.

```html
<!-- navbar.html line 54 — .slug doesn't exist on ActiveProject -->
<a href="{{ url_for('public.project_detail', slug=current_active_project.slug) }}"
<!-- navbar.html line 57 — .title doesn't exist on ActiveProject -->
{{ current_active_project.title }}
```

---

### 2. Spotify button CSS typo in `base.html`
**File:** `app/templates/base.html` line 201
The class string reads `shadow-xl ition-all duration-200` — `trans` is missing from `transition-all`. This is a remnant of the file-truncation repair from a previous session. The button hover animation won't work.

```html
class="... shadow-xl ition-all duration-200 hover:scale-105 ..."
<!--                  ^ should be transition-all -->
```

---

## HIGH

### 3. `now` not passed to hire form — deadline `min` attribute broken
**File:** `app/routes/public.py` `hire()` GET handler
**File:** `app/templates/public/hire.html` line ~202
The deadline date input uses `min="{{ now.strftime('%Y-%m-%d') if now else '' }}"` to prevent selecting past dates. The `now` variable is never injected into `render_template('public/hire.html', ...)`, so `now` is always `None` and the `min` attribute is always empty — users can select dates in the past.

---

### 4. Multiple Lucide `<i>` tags still present across templates
**Files:** `app/templates/base.html`, `app/templates/public/hire.html`, `app/templates/public/about.html` (partial), others
Lucide's auto-init CDN does not reliably fire. Any `<i data-lucide="...">` tag that hasn't been replaced with an inline SVG will render as an empty square. Affected instances include:
- Cookie consent close button (`data-lucide="x"`) — `base.html` ~line 123
- Send icon on hire form submit button (`data-lucide="send"`) — `hire.html`
- Download icon on CV button (`about.html` line 66)
- Arrow icons on about page CTA buttons (`about.html` lines 92, 443)
- Chevron-down scroll indicator (`home.html` line 199)
- Various icons across `work.html`, `writing.html`, `contact.html`

---

### 5. No server-side validation of required hire form fields
**File:** `app/routes/public.py` `hire()` POST handler
The backend only checks that a signed contract file was uploaded. Fields like `client_email`, `project_title`, `project_description`, and `deliverables` have `required` in HTML but are not validated server-side. A direct POST bypassing the browser will create incomplete `HireRequest` records in the database.

---

### 6. File upload size not enforced server-side
**File:** `app/routes/public.py`
The hire form template says "max 10MB each" but there is no server-side file size check. A user or bot could upload arbitrarily large files, consuming disk or memory on Railway.

---

## MEDIUM

### 7. `tip_percent` submitted but not stored in DB
**File:** `app/models.py`, `app/routes/public.py`, `app/templates/public/hire.html`
The hire form sends a hidden `tip_percent` field (e.g. `"15"` or `"custom"`). The backend reads it from the form but the `HireRequest` model has no `tip_percent` column. The value is silently dropped. This means you can see `tip_amount = 75.00` in the DB but have no record of whether it was 15% of $500 or a custom entry.

---

### 8. `pending_checkout` payment status undocumented in model
**File:** `app/models.py` `HireRequest.payment_status`, `app/routes/public.py` line ~273
The route sets `payment_status = 'pending_checkout'` for Stripe hires. The model column comment lists `'not_required', 'awaiting_confirmation', 'confirmed'` as valid values — `'pending_checkout'` is not listed. Not a crash, but causes confusion when reading DB records.

---

### 9. Silent failure on hire notifications — no logging
**File:** `app/routes/public.py` lines ~332–350
All notification side-effects (email, WhatsApp) are wrapped in bare `except Exception: pass`. If they fail, no error is logged and the user is not told. A hire request could be created with zero notifications sent, and you'd never know.

```python
try:
    notify_hire_request(hr)
except Exception:
    pass   # silent — no current_app.logger.exception(...)
```

---

### 10. Hardcoded contact details in templates
**Files:** `app/templates/public/hire.html`, `app/templates/base.html`
The following are hardcoded in templates rather than coming from config or a settings table:
- M-Pesa till number: `107798`
- M-Pesa phone: `+254 799 841 016`
- WhatsApp link: `https://wa.me/254114209088` (base.html)
- Wise link: `https://wise.com/pay/me/jamesl3050`

Changing any of these requires a code deploy.

---

### 11. Hardcoded email in JavaScript error message
**File:** `app/static/js/main.js` line ~62
```javascript
this.error = 'Network error. Email me directly at lago@lagobrian.com';
```
Hardcoded email address. If changed, requires a JS rebuild/redeploy.

---

## LOW

### 12. Footer `now.year` always falls back to `'2026'`
**File:** `app/templates/public/partials/footer.html`
```html
&copy; {{ now.year if now else '2026' }}
```
`now` is never injected globally, so this always renders `2026`. Next year it'll be wrong. Should use a context processor or `datetime.utcnow().year` passed globally.

---

### 13. Scroll indicator on home page uses Lucide icon
**File:** `app/templates/public/home.html` line 199
```html
<i data-lucide="chevron-down" class="w-5 h-5"></i>
```
Part of the bounce-animated scroll prompt. Renders empty if Lucide doesn't load. A simple `↓` or inline SVG would be more reliable.

---

### 14. `no_rush` toggle sends `"on"` but deadline fields still submitted
**File:** `app/templates/public/hire.html`
When `no_rush` is toggled, the deadline date/time inputs are hidden via `x-show` but remain in the DOM and still submit their values with the form. The backend stores whatever is in `deadline` regardless of `no_rush`. Consider disabling the inputs with `:disabled="noRush"` to prevent stale values being saved.

---

### 15. PM admin templates — `url_for('crm_pm.export_section', ...)` verified working, but `_serialize_rows` has no `'daily_focus'` case
**File:** `app/routes/crm/pm.py` `_serialize_rows()` function
`pm_daily_focus.html` has an export button for `section='daily_focus'`, but `_serialize_rows()` may not have a matching `elif section == 'daily_focus':` branch. If missing, the export silently returns an empty list rather than raising an error.

---

### 16. Mobile menu "Store" link missing
**File:** `app/templates/public/partials/navbar.html`
The desktop nav has a "Store" link added separately outside the `nav_items` loop. The mobile menu iterates only over `nav_items` and does not include Store. Mobile users have no way to reach the Store page from the menu.

---

## NOTES / NON-ISSUES

- **Migration branch conflict** — was present and has been fixed (a3f1c9d2e8b4 now points to d2c8a7f4c1be).
- **Tip percent math** (`totalAmount * tipPercent / 100`) — correct. tipPercent is an integer like `15`, so this gives 15%.
- **CSRF** — Flask-WTF injects tokens globally; all POST forms are covered.
- **Alpine.js reactive tip/no-rush logic** — correct as implemented.

---

*Generated 2026-03-28*
