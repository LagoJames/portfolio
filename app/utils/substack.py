import feedparser
import time
from flask import current_app

_cache = {}


def get_feed(substack_url, limit=20):
    """Parse Substack RSS. Cache 1 hour per feed."""
    now = time.time()
    if substack_url in _cache and (now - _cache[substack_url]['at']) < 3600:
        return _cache[substack_url]['posts']

    try:
        feed = feedparser.parse(f'{substack_url}/feed')
        posts = []
        for entry in feed.entries[:limit]:
            tags = [t.get('term', '') for t in entry.get('tags', [])]
            posts.append({
                'title': entry.get('title', ''),
                'url': entry.get('link', ''),
                'published': entry.get('published', ''),
                'published_parsed': entry.get('published_parsed'),
                'summary': entry.get('summary', '')[:250],
                'tags': tags,
                'author': entry.get('author', 'Lago Brian'),
            })
        _cache[substack_url] = {'posts': posts, 'at': now}
        return posts
    except Exception:
        if substack_url in _cache:
            return _cache[substack_url]['posts']
        return []


def get_quant_hedge_posts(limit=20):
    url = current_app.config.get('SUBSTACK_QUANT_URL', 'https://quanthedge.substack.com')
    return get_feed(url, limit)


def get_jarida_posts(limit=6):
    url = current_app.config.get('SUBSTACK_JARIDA_URL', 'https://jaridalahisa.substack.com')
    return get_feed(url, limit)


def clear_cache(substack_url=None):
    if substack_url:
        _cache.pop(substack_url, None)
    else:
        _cache.clear()


def get_last_fetched(substack_url):
    if substack_url in _cache:
        return _cache[substack_url]['at']
    return None
