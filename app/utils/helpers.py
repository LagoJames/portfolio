import re
from datetime import datetime, timezone
from markupsafe import Markup
import markdown
import bleach


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def format_date(dt, fmt='%b %d, %Y'):
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except (ValueError, TypeError):
            return dt
    if dt:
        return dt.strftime(fmt)
    return ''


def render_markdown(text):
    if not text:
        return ''
    html = markdown.markdown(text, extensions=['fenced_code', 'tables', 'toc'])
    allowed_tags = list(bleach.ALLOWED_TAGS) + [
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'pre', 'code',
        'table', 'thead', 'tbody', 'tr', 'th', 'td', 'img', 'br', 'hr',
        'div', 'span', 'ul', 'ol', 'li', 'blockquote', 'strong', 'em'
    ]
    allowed_attrs = dict(bleach.ALLOWED_ATTRIBUTES)
    allowed_attrs['img'] = ['src', 'alt', 'title']
    allowed_attrs['code'] = ['class']
    allowed_attrs['pre'] = ['class']
    allowed_attrs['a'] = ['href', 'title', 'target', 'rel']
    clean = bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs)
    return Markup(clean)


def get_setting(key, default=''):
    from app.models import Setting
    from app import db
    try:
        s = db.session.query(Setting).filter_by(key=key).first()
        return s.value if s else default
    except Exception:
        return default


def time_ago(dt):
    if not dt:
        return 'never'
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = now - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        mins = int(seconds / 60)
        return f'{mins} minute{"s" if mins != 1 else ""} ago'
    elif seconds < 86400:
        hrs = int(seconds / 3600)
        return f'{hrs} hour{"s" if hrs != 1 else ""} ago'
    else:
        days = int(seconds / 86400)
        return f'{days} day{"s" if days != 1 else ""} ago'
