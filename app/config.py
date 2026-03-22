import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-fallback-key')
    _db_url = os.environ.get('DATABASE_URL', 'sqlite:///portfolio.db')
    # Render uses postgres:// but SQLAlchemy needs postgresql://
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 10 * 1024 * 1024))
    WTF_CSRF_ENABLED = True

    # External feeds
    GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME', 'LagoJames')
    SUBSTACK_QUANT_URL = os.environ.get('SUBSTACK_QUANT_URL', 'https://quanthedge.substack.com')
    SUBSTACK_JARIDA_URL = os.environ.get('SUBSTACK_JARIDA_URL', 'https://jaridalahisa.substack.com')

    # Email
    CONTACT_TO_EMAIL = os.environ.get('CONTACT_TO_EMAIL', 'lago@lagobrian.com')
    SES_FROM_EMAIL = os.environ.get('SES_FROM_EMAIL', 'hello@lagobrian.com')
    AWS_SES_REGION = os.environ.get('AWS_SES_REGION', 'eu-west-1')

    # Payment integrations
    INTASEND_API_KEY = os.environ.get('INTASEND_API_KEY', '')
    INTASEND_PUBLISHABLE_KEY = os.environ.get('INTASEND_PUBLISHABLE_KEY', '')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    WISE_API_KEY = os.environ.get('WISE_API_KEY', '')
