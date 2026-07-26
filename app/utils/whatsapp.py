import os
import hashlib
import atexit
from collections import defaultdict
from datetime import datetime
from urllib.parse import quote, urlparse

import requests

# ── Config ────────────────────────────────────────────────────────────────────
CALLMEBOT_PHONE  = os.environ.get('CALLMEBOT_PHONE')
CALLMEBOT_APIKEY = os.environ.get('CALLMEBOT_APIKEY')
TEXTMEBOT_APIKEY = os.environ.get('TEXTMEBOT_APIKEY')

# ── In-memory tracking (resets on redeploy — fine for a freelancing site) ─────
alerted_ips       = set()             # one alert per IP per server session
all_time_ips      = set()             # for returning-visitor detection
daily_visitors    = set()
daily_proposals   = []
page_views        = defaultdict(int)
referrers         = defaultdict(int)
peak_hours        = defaultdict(int)
returning_visitors = set()


# ── Core sender ───────────────────────────────────────────────────────────────
def send_whatsapp(message: str):
    if not CALLMEBOT_PHONE or not CALLMEBOT_APIKEY:
        print('[WhatsApp] Missing CALLMEBOT_PHONE or CALLMEBOT_APIKEY — skipping.')
        return
    url = (
        'https://api.callmebot.com/whatsapp.php'
        f'?phone={CALLMEBOT_PHONE}'
        f'&text={quote(message)}'
        f'&apikey={CALLMEBOT_APIKEY}'
    )
    try:
        requests.get(url, timeout=5)
    except Exception as e:
        print(f'[WhatsApp] Send failed: {e}')


# ── TextMeBot: send FROM your number TO a client ─────────────────────────────
def _clean_phone(phone: str) -> str:
    """Strip +, spaces, dashes from a phone number."""
    return phone.replace('+', '').replace(' ', '').replace('-', '').strip()


def send_whatsapp_to_client(recipient_phone: str, message: str) -> bool:
    apikey = TEXTMEBOT_APIKEY
    if not apikey:
        print('[TextMeBot] TEXTMEBOT_APIKEY not set — skipping client message.')
        return False
    phone = _clean_phone(recipient_phone)
    if not phone:
        return False
    url = (
        'https://api.textmebot.com/send.php'
        f'?recipient={phone}&apikey={apikey}&text={quote(message)}'
    )
    try:
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except Exception as e:
        print(f'[TextMeBot] Send failed: {e}')
        return False


def _wa(phone, message):
    """Fire-and-forget TextMeBot send in a background thread."""
    import threading
    if not phone:
        return
    threading.Thread(
        target=send_whatsapp_to_client,
        args=(phone, message),
        daemon=True,
    ).start()


def _wa_phone(hr) -> str:
    """Return the best WhatsApp number for a HireRequest."""
    return getattr(hr, 'whatsapp_number', None) or getattr(hr, 'client_phone', '') or ''


def confirm_hire_client(name: str, phone: str, project_title: str):
    """Proposal received — sent automatically on hire form submit."""
    label = name or 'there'
    _wa(phone,
        f'Hi {label}! 👋\n\n'
        f'Thanks for reaching out. I\'ve received your proposal for '
        f'*{project_title}* and will review it within 24 hours.\n\n'
        f'I\'ll be in touch soon — Brian (lagobrian.com)')


def alert_proposal_accepted(hr, start_in_days: int = 0):
    """Proposal accepted — sent when admin clicks Accept."""
    phone = _wa_phone(hr)
    name = hr.client_name or 'there'
    if start_in_days == 0:
        timing = 'and I\'ll start work *immediately*'
    elif start_in_days == 1:
        timing = 'and I\'ll start work *tomorrow*'
    else:
        timing = f'and I\'ll start work in *{start_in_days} days*'
    _wa(phone,
        f'Hi {name}! 🎉\n\n'
        f'Great news — I\'ve reviewed your proposal for *{hr.project_title}* '
        f'{timing}.\n\n'
        f'I\'ll keep you updated as we make progress. '
        f'Feel free to reach out if you have any questions.\n\n'
        f'— Brian')


def alert_payment_received(hr, amount_paid: float, amount_remaining: float = 0):
    """Payment confirmed — sent when admin confirms a payment."""
    phone = _wa_phone(hr)
    name = hr.client_name or 'there'
    if amount_remaining > 0:
        balance = f'Remaining balance: *${amount_remaining:,.2f}*'
    else:
        balance = 'Your account is now *fully paid* ✅'
    _wa(phone,
        f'Hi {name} ✅\n\n'
        f'I\'ve received your payment of *${amount_paid:,.2f}* for '
        f'*{hr.project_title}*.\n\n'
        f'{balance}\n\n'
        f'Thank you — Brian')


def alert_milestone_done(hr, milestone_name: str, note: str = ''):
    """A milestone was completed."""
    phone = _wa_phone(hr)
    name = hr.client_name or 'there'
    extra = f'\n\n{note}' if note else ''
    _wa(phone,
        f'Hi {name} ✅\n\n'
        f'Milestone complete: *{milestone_name}*\n'
        f'Project: *{hr.project_title}*{extra}\n\n'
        f'Let me know if you\'d like to review this stage before I continue.\n\n'
        f'— Brian')


def alert_project_delivered(hr, note: str = ''):
    """Final delivery — project is done."""
    phone = _wa_phone(hr)
    name = hr.client_name or 'there'
    extra = f'\n\n{note}' if note else ''
    _wa(phone,
        f'Hi {name} 🎉\n\n'
        f'Your project *{hr.project_title}* is complete and has been delivered!\n\n'
        f'Check your email for the files.{extra}\n\n'
        f'It was a pleasure working with you. '
        f'Let me know if you need any revisions.\n\n'
        f'— Brian (lagobrian.com)')


def alert_need_info(hr, what_needed: str):
    """Request additional information from the client."""
    phone = _wa_phone(hr)
    name = hr.client_name or 'there'
    _wa(phone,
        f'Hi {name} 👋\n\n'
        f'I\'m working on *{hr.project_title}* and need a bit more from you:\n\n'
        f'{what_needed}\n\n'
        f'Please reply here or email me at lagobrian@outlook.com.\n\n'
        f'— Brian')


def alert_revision_done(hr, note: str = ''):
    """Revision completed."""
    phone = _wa_phone(hr)
    name = hr.client_name or 'there'
    extra = f'\n\n{note}' if note else ''
    _wa(phone,
        f'Hi {name} ✅\n\n'
        f'The revision for *{hr.project_title}* is done!{extra}\n\n'
        f'Updated files have been sent to your email. '
        f'Let me know if anything else needs adjusting.\n\n'
        f'— Brian')


def send_invoice_reminder(client_phone: str, client_name: str,
                          amount: str, due_date: str):
    """Remind a client about an outstanding invoice."""
    _wa(client_phone,
        f'Hi {client_name} 👋\n\n'
        f'Just a friendly reminder that your invoice of *${amount}* '
        f'is due on *{due_date}*.\n\n'
        f'Let me know if you have any questions — Brian')


def send_followup(client_phone: str, client_name: str, project_type: str):
    """Follow up with a client who hasn't responded."""
    _wa(client_phone,
        f'Hi {client_name} 👋\n\n'
        f'Just following up on your enquiry about *{project_type}*. '
        f'I\'d love to help — are you still interested?\n\n'
        f'— Brian (lagobrian.com)')


# ── Visitor alert (call from before_request) ───────────────────────────────────
def track_visitor(path: str, remote_addr: str, forwarded_for: str | None, referrer: str | None):
    if path.startswith('/static'):
        return

    ip      = forwarded_for or remote_addr
    ip_hash = hashlib.md5(ip.encode()).hexdigest()[:8]
    hour    = datetime.now().hour

    page_views[path] += 1
    peak_hours[hour] += 1

    if referrer:
        try:
            domain = urlparse(referrer).netloc.replace('www.', '')
            if domain:
                referrers[domain] += 1
        except Exception:
            pass

    if ip_hash in all_time_ips:
        returning_visitors.add(ip_hash)

    daily_visitors.add(ip_hash)
    all_time_ips.add(ip_hash)

    if ip_hash not in alerted_ips:
        alerted_ips.add(ip_hash)
        source = 'direct'
        if referrer:
            try:
                source = urlparse(referrer).netloc.replace('www.', '') or 'direct'
            except Exception:
                pass
        time_str = datetime.now().strftime('%H:%M')
        send_whatsapp(
            f'👁 New visitor at {time_str}\n'
            f'📄 Page: {path}\n'
            f'🔗 Source: {source}'
        )


# ── Hire-form alert ────────────────────────────────────────────────────────────
def alert_hire(name: str, email: str, project_title: str,
               budget: str, payment_method: str):
    entry = {
        'name':    name,
        'email':   email,
        'project': project_title,
        'budget':  budget,
        'time':    datetime.now().strftime('%H:%M'),
    }
    daily_proposals.append(entry)

    label = name if name else 'Anonymous'
    send_whatsapp(
        f'💼 New proposal from {label}!\n'
        f'📧 {email}\n'
        f'📁 {project_title}\n'
        f'💰 Budget: {budget}\n'
        f'💳 Payment: {payment_method}'
    )


# ── Nightly summary ────────────────────────────────────────────────────────────
def send_daily_summary():
    today          = datetime.now().strftime('%A, %d %b %Y')
    visitor_count  = len(daily_visitors)
    returning_count = len(returning_visitors)
    new_count      = visitor_count - returning_count
    proposal_count = len(daily_proposals)

    top_pages = sorted(page_views.items(), key=lambda x: x[1], reverse=True)[:3]
    pages_text = ''.join(f'\n  {p} ({c} views)' for p, c in top_pages) or '\n  No views today'

    top_refs = sorted(referrers.items(), key=lambda x: x[1], reverse=True)[:3]
    refs_text = ''.join(f'\n  {d} ({c})' for d, c in top_refs) or '\n  Direct / unknown'

    peak_text = 'N/A'
    if peak_hours:
        ph = max(peak_hours, key=peak_hours.get)
        peak_text = f'{ph:02d}:00–{ph+1:02d}:00'

    proposals_text = ''
    for p in daily_proposals:
        proposals_text += f"\n  • {p['name']} | {p['project']} | {p['budget']} @ {p['time']}"

    nudge = ''
    if visitor_count == 0:
        nudge = '\n\n💡 No visitors today — share your portfolio link!'
    elif proposal_count == 0 and visitor_count >= 5:
        nudge = '\n\n💡 Good traffic but no proposals — review your call-to-action.'
    elif proposal_count >= 3:
        nudge = '\n\n🔥 Strong day — follow up with proposals promptly!'

    send_whatsapp(
        f'📊 Daily Report — {today}\n\n'
        f'👥 Visitors: {visitor_count} ({new_count} new, {returning_count} returning)\n'
        f'📩 Proposals: {proposal_count}{proposals_text}\n\n'
        f'📄 Top pages:{pages_text}\n\n'
        f'🔗 Traffic sources:{refs_text}\n\n'
        f'⏰ Peak hour: {peak_text}'
        f'{nudge}'
    )

    # Reset daily counters (keep all_time_ips for returning-visitor detection)
    daily_visitors.clear()
    daily_proposals.clear()
    returning_visitors.clear()
    page_views.clear()
    referrers.clear()
    peak_hours.clear()


# ── Scheduler bootstrap (call once from create_app) ───────────────────────────
def start_scheduler():
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler(timezone='Africa/Nairobi')
        scheduler.add_job(send_daily_summary, 'cron', hour=23, minute=59)
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown(wait=False))
        print('[WhatsApp] Nightly summary scheduler started (23:59 EAT).')
    except ImportError:
        print('[WhatsApp] apscheduler not installed — nightly summary disabled.')
    except Exception as e:
        print(f'[WhatsApp] Scheduler failed to start: {e}')
