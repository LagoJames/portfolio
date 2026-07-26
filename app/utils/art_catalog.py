"""Shared art gallery and store catalog data."""
from __future__ import annotations

from flask import url_for


ART_FACEBOOK_URL = 'https://www.facebook.com/ArtByLago'


ART_GALLERY = [
    {
        'slug': 'rihanna-colored-portrait',
        'title': 'Rihanna Study',
        'medium': 'Colored portrait study',
        'filename': 'img/Rihanna_drawing.jpg',
        'store_enabled': False,
    },
    {
        'slug': 'antelope-pencil-drawing',
        'title': 'Antelope',
        'medium': 'Graphite drawing',
        'filename': 'img/Antelope drawing.jpg',
        'store_enabled': True,
    },
    {
        'slug': 'rhino-pencil-drawing',
        'title': 'Rhino',
        'medium': 'Graphite drawing',
        'filename': 'img/Rhino drawing.jpg',
        'store_enabled': True,
    },
    {
        'slug': 'cub-pencil-drawing',
        'title': 'Cub Study',
        'medium': 'Graphite drawing',
        'filename': 'img/Cub drawing.jpg',
        'store_enabled': True,
    },
    {
        'slug': 'tiger-pencil-drawing',
        'title': 'Tiger',
        'medium': 'Graphite drawing',
        'filename': 'img/tiger_drawing.jpg',
        'store_enabled': True,
    },
    {
        'slug': 'damon-portrait',
        'title': 'Portrait Study',
        'medium': 'Graphite portrait',
        'filename': 'img/Damon drawing.jpg',
        'store_enabled': True,
    },
    {
        'slug': 'lion-portrait-pencil-drawing',
        'title': 'Lion Portrait',
        'medium': 'Graphite drawing',
        'filename': 'img/Lion drawing.jpg',
        'store_enabled': True,
    },
]


def gallery_items():
    items = []
    for item in ART_GALLERY:
        entry = dict(item)
        entry['image_url'] = url_for('static', filename=item['filename'])
        items.append(entry)
    return items


def store_prints():
    products = []
    for item in ART_GALLERY:
        if not item['store_enabled']:
            continue
        products.append({
            'slug': item['slug'],
            'title': f"{item['title']} Print",
            'subtitle': 'Art Print',
            'description': f"{item['medium']} available as a free download.",
            'price_label': 'Free download',
            'image_url': url_for('static', filename=item['filename']),
            'download_filename': item['filename'],
            'checkout_kind': 'download',
        })
    return products
