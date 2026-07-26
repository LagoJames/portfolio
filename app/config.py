import os

class Config:
    _env = (os.environ.get('FLASK_ENV') or os.environ.get('ENV') or '').lower()
    IS_PRODUCTION = bool(os.environ.get('RAILWAY_ENVIRONMENT')) or _env == 'production'
    SECRET_KEY = os.environ.get('SECRET_KEY', '')
    _db_url = os.environ.get('DATABASE_URL', 'sqlite:///portfolio.db')
    # Render uses postgres:// but SQLAlchemy needs postgresql://
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 10 * 1024 * 1024))
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = IS_PRODUCTION
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = IS_PRODUCTION
    PREFERRED_URL_SCHEME = 'https' if IS_PRODUCTION else 'http'
    ADMIN_LOGIN_WINDOW_SECONDS = int(os.environ.get('ADMIN_LOGIN_WINDOW_SECONDS', '900'))
    ADMIN_LOGIN_MAX_ATTEMPTS = int(os.environ.get('ADMIN_LOGIN_MAX_ATTEMPTS', '8'))

    # External feeds
    GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME', 'LagoJames')
    SUBSTACK_QUANT_URL = os.environ.get('SUBSTACK_QUANT_URL', 'https://quanthedge.substack.com')
    SUBSTACK_JARIDA_URL = os.environ.get('SUBSTACK_JARIDA_URL', 'https://jaridalahisa.substack.com')

    # Email
    CONTACT_TO_EMAIL = os.environ.get('CONTACT_TO_EMAIL', 'lagobrian@outlook.com')
    SES_FROM_EMAIL = os.environ.get('SES_FROM_EMAIL', 'lagobrian@outlook.com')
    AWS_SES_REGION = os.environ.get('AWS_SES_REGION', 'eu-west-1')
    PM_OWNER_EMAIL = os.environ.get('PM_OWNER_EMAIL', CONTACT_TO_EMAIL)
    PM_FREELANCER_EMAIL = os.environ.get('PM_FREELANCER_EMAIL', '')

    # Payment integrations
    MPESA_TILL = '107798'
    MPESA_NUMBER = '+254799841016'
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    STRIPE_CURRENCY = os.environ.get('STRIPE_CURRENCY', 'usd')
    STRIPE_SUCCESS_URL = os.environ.get('STRIPE_SUCCESS_URL', '')
    STRIPE_CANCEL_URL = os.environ.get('STRIPE_CANCEL_URL', '')
    WISE_PAYMENT_LINK = os.environ.get('WISE_PAYMENT_LINK', 'https://wise.com/pay/me/jamesl3050')
    WISE_BILLING_EMAIL = os.environ.get('WISE_BILLING_EMAIL', 'jamesl3050-9486@inbox.wise.com')
