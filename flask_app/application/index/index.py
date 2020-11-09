"""General page routes."""
import requests, discord
from flask import Blueprint, render_template
from flask import current_app as app
from discord import Webhook, RequestsWebhookAdapter

# Blueprint Configuration
index_bp = Blueprint(
    'index_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

# With Connexion, 'index.html' is overriden for some reason
@index_bp.route('/', methods=['GET'])
def index():
    """Homepage."""
    return render_template(
        'index0.html',
    )