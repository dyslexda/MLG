"""Class-based Flask app configuration."""
from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))


class Config:
    """Configuration from environment variables."""

    SECRET_KEY = environ.get('SECRET_KEY')
    FLASK_ENV = environ.get('FLASK_ENV')
    FLASK_APP = 'app.py'

    # Static Assets
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    COMPRESSOR_DEBUG = True

    # Reddit Auth
    CLIENT_ID = environ.get('CLIENT_ID')
    CLIENT_SECRET = environ.get('CLIENT_SECRET')
    REDIRECT_URI = environ.get('REDIRECT_URI')
    USER_AGENT = environ.get('USER_AGENT')

    # Discord Auth
    WEBHOOK_ID = environ.get('WEBHOOK_ID')
    WEBHOOK_TOKEN = environ.get('WEBHOOK_TOKEN')