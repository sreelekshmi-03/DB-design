from .base import 

DEBUG = False

if not ALLOWED_HOSTS:
    raise RuntimeError("ALLOWED_HOSTS must be set in .env for production")

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True