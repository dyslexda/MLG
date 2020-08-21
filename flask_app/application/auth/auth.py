"""General page routes."""
import praw, requests, json
import functools
from flask import Blueprint, render_template, Flask, session, redirect, url_for, request, g
from flask import current_app as app
from shared.models import Users

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
    session.clear()
    return redirect(url_for('index_bp.index'))

@auth_bp.route('/authorize_callback', methods=['GET'])
def authorized():
    if request.args.get('code', ''):
        state = request.args.get('state', '')
        code = request.args.get('code', '')
        access_token = getOAuthToken(code)
        reddit_name = getIdentity(access_token)
        session['username'] = reddit_name
        user = Users.get(Users.Reddit_Name == reddit_name)
        if 'umpire' in user.Roles:
            session['umpire'] = True
        else:
            session['umpire'] = False
        if 'commissioner' in user.Roles:
            session['commissioner'] = True
        else:
            session['commissioner'] = False
        revokeToken(access_token,"access_token")
    return redirect(url_for('index_bp.index'))

def getIdentity(access_token):
    i = requests.get('https://oauth.reddit.com/api/v1/me',
                     headers = {'User-agent':app.config['USER_AGENT'],'Authorization': f'Bearer {access_token}'})
    return json.loads(i.text)["name"]

def getOAuthToken(code):
    r = requests.post('https://www.reddit.com/api/v1/access_token',
                     auth = (app.config['CLIENT_ID'],app.config['CLIENT_SECRET']),
                     headers = {'User-agent':app.config['USER_AGENT'],'Content-Type':'application/x-www-form-urlencoded'},
                     data = {'grant_type':'authorization_code','code':code,'redirect_uri':app.config['REDIRECT_URI']})
    access_token = json.loads(r.text)["access_token"]
    return access_token

def revokeToken(token, tokentype):
    r = requests.post('https://www.reddit.com/api/v1/revoke_token',
                      auth = (app.config['CLIENT_ID'],app.config['CLIENT_SECRET']),
                      headers = {'User-agent':app.config['USER_AGENT'],'Content-Type':'application/x-www-form-urlencoded'},
                      data = {'token':token,'token_type_hint':tokentype})

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('index_bp.index'))

        return view(**kwargs)

    return wrapped_view