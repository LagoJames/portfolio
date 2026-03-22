import requests
import time
from flask import current_app

_cache = {'data': None, 'fetched_at': 0}


def get_repos(limit=18):
    """Fetch public repos from GitHub. Cache for 1 hour."""
    if _cache['data'] and (time.time() - _cache['fetched_at']) < 3600:
        return _cache['data']

    username = current_app.config.get('GITHUB_USERNAME', 'LagoJames')
    try:
        resp = requests.get(
            f'https://api.github.com/users/{username}/repos',
            params={'sort': 'updated', 'per_page': limit},
            headers={
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'LagoBrianPortfolio/1.0'
            },
            timeout=10
        )
        if resp.ok:
            repos = resp.json()
            _cache['data'] = repos
            _cache['fetched_at'] = time.time()
            return repos
    except Exception:
        pass
    return _cache['data'] or []


def clear_cache():
    _cache['data'] = None
    _cache['fetched_at'] = 0


def get_last_fetched():
    if _cache['fetched_at']:
        return _cache['fetched_at']
    return None
