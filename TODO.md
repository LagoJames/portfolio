# Portfolio Website — To-Do List

## 1. Fix Emails & Links
- [x] Replace all instances of `hello@lagobrian.com` with `lagobrian@outlook.com`
- [x] Update seed.py — admin email → `lagobrian@outlook.com`
- [ ] Audit all external links (Upwork, LinkedIn, Substack, GitHub) — confirm they are correct
- [ ] Set correct env vars in Railway: `CONTACT_TO_EMAIL`, `SMTP_EMAIL`

## 2. Email Notifications
- [ ] Confirm SMTP settings work for Outlook (`smtp-mail.outlook.com`, port 587)
- [ ] Test contact form — email should land in `lagobrian@outlook.com`
- [ ] Test hire form — email should land in `lagobrian@outlook.com`
- [ ] Decide: keep SMTP (Outlook) or switch to AWS SES — remove unused option
- [ ] Set Railway env vars: `SMTP_EMAIL`, `SMTP_PASSWORD`, `SMTP_HOST`, `SMTP_PORT`, `CONTACT_TO_EMAIL`

## 3. Payments
- [ ] Decide on payment provider: IntaSend (KES) and/or Stripe (USD)
- [ ] Set up IntaSend account and get live API keys
- [ ] Set up Stripe account and get live API keys
- [ ] Set Railway env vars: `INTASEND_API_KEY`, `INTASEND_PUBLISHABLE_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`
- [ ] Test payment flow end-to-end on the hire form
- [ ] Add webhook handling for payment confirmations (if needed)

## 4. Admin Dashboard
- [ ] Log in and verify all sections load correctly (projects, testimonials, skills, contacts, hire requests)
- [ ] Upload profile photo and CV via admin settings
- [ ] Add sample work files to projects that need them
- [ ] Verify settings page saves correctly (display name, tagline, stats, social links)
- [ ] Change default admin password from `admin123` to something secure
- [ ] Test review token generation flow

## 5. Project Management (PM) Dashboard
- [ ] Verify PM dashboard loads and displays clients/projects/tasks
- [ ] Test adding a new client, project, and task
- [ ] Test expense logging and invoice forms
- [ ] Test payment recording against a project
- [ ] Verify project status updates reflect correctly
- [ ] Review seeded PM data (clients: Younnan Lamine, Ariana Mondiri, Joel Khalil) — update or remove test data

## 6. Samples & Work Pages
- [ ] Upload actual work samples (PDFs, notebooks, screenshots) via admin
- [ ] Link samples to the correct projects
- [ ] Verify `/samples` and `/work` pages display correctly

## 7. General QA
- [ ] Check all pages on mobile
- [ ] Verify blog posts load (Substack integration)
- [ ] Test GitHub activity feed
- [x] Confirm 500 error is fully resolved and site is stable
- [ ] Add custom domain (if desired) in Railway → Settings → Networking
