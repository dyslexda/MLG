"""General page routes."""
import praw, requests, json
from flask import Blueprint, render_template, Flask, session, redirect, url_for, request
from flask import current_app as app

# Blueprint Configuration
auth_bp = Blueprint(
    'auth_bp', __name__,
    url_prefix='/auth',
    template_folder='templates',
    static_folder='static'
)

r = praw.Reddit(client_id = app.config['CLIENT_ID'],
                client_secret = app.config['CLIENT_SECRET'],
                redirect_uri = app.config['REDIRECT_URI'],
                user_agent = app.config['USER_AGENT'])

@auth_bp.route('/login', methods=['GET'])
def login():
    return redirect(r.auth.url(["identity"],'UniqueKey',"temporary"))

@auth_bp.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index_bp.index'))

@auth_bp.route('/authorize_callback', methods=['GET'])
def authorized():
    if request.args.get('code', ''):
        state = request.args.get('state', '')
        code = request.args.get('code', '')
        access_token = getOAuthToken(code)
        reddit_name = getIdentity(access_token)
        session['username'] = reddit_name
        revokeToken(access_token,"access_token")
    return redirect(url_for('index_bp.index'))

def getIdentity(access_token):
    i = requests.get('https://oauth.reddit.com/api/v1/me',
                     headers = {'User-agent':app.config['USER_AGENT'],'Authorization': f'Bearer {access_token}'})
    return json.loads(i.text)["name"]

def getOAuthToken(code):
    r = requests.post('https://www.reddit.com/api/v1/access_token',
                     auth = ('tUv_ZIIJCczWkQ','bfh-3E2wfIyvifXUhyL9xiOhrKk'),
                     headers = {'User-agent':app.config['USER_AGENT'],'Content-Type':'application/x-www-form-urlencoded'},
                     data = {'grant_type':'authorization_code','code':code,'redirect_uri':app.config['REDIRECT_URI']})
    access_token = json.loads(r.text)["access_token"]
    return access_token

def revokeToken(token, tokentype):
    r = requests.post('https://www.reddit.com/api/v1/revoke_token',
                      auth = ('tUv_ZIIJCczWkQ','bfh-3E2wfIyvifXUhyL9xiOhrKk'),
                      headers = {'User-agent':app.config['USER_AGENT'],'Content-Type':'application/x-www-form-urlencoded'},
                      data = {'token':token,'token_type_hint':tokentype})