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

@index_bp.route('/', methods=['GET'])
def index():
    """Homepage."""
    return render_template(
        'index.html',
    )

@index_bp.route('/test',methods=['GET','POST'])
def test():
    with requests.Session() as s:
        webhook = Webhook.partial(app.config['WEBHOOK_ID'], app.config['WEBHOOK_TOKEN'], adapter=RequestsWebhookAdapter(s))
        webhook.send('test')