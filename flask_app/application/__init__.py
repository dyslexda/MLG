import sys, os, logging, time
import connexion
from flask_marshmallow import Marshmallow
from logging.handlers import RotatingFileHandler
from os import path
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from flask import Flask, session, g, request, has_request_context
from flask_assets import Environment
from shared.models import *

def create_app():
    basedir = os.path.abspath(os.path.dirname(__file__))
 #   print(basedir)
    connex_app = connexion.FlaskApp(__name__,specification_dir='api/')
    connex_app.add_api('specification.yml')
    app = connex_app.app
    

#    ma = Marshmallow(app)
#    app = Flask(__name__,instance_relative_config=True)
    logging.basicConfig(filename='output.log',
                        level=logging.WARNING)
    app.config.from_object('config.Config')
    assets = Environment()
    assets.init_app(app)

    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/baseball.log', maxBytes=10240,
                                       backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Baseball startup')

    with app.app_context():
        from .index import index
        from .teams import teams
        from .players import players
        from .auth import auth
        from .admin import admin
        from .games import games
        from .calc_routes import calc_routes
        from .api import api

        app.register_blueprint(index.index_bp)
        app.register_blueprint(teams.teams_bp)
        app.register_blueprint(players.players_bp)
        app.register_blueprint(auth.auth_bp)
        app.register_blueprint(admin.admin_bp)
        app.register_blueprint(games.games_bp)
        app.register_blueprint(calc_routes.calc_bp)
        app.register_blueprint(api.api_bp)

        if app.config['SCOUTING'] == True:
            from .scouting import scouting
            app.register_blueprint(scouting.scouting_bp,url_prefix='/scouting')

        @app.before_request
        def before_request():
            db.connect(reuse_if_open=True)
            username = session.get('username')
            if username is None:
                g.user = None
            else:
                g.user = Users.get_or_none(Users.Reddit_Name == username)
            if not request.environ['RAW_URI'].endswith(tuple(['.css','.js','.png','.ico'])):
                accessfile = open("accesslog.txt","a")
                try:
                    if g.user != None:
                        user = g.user.Reddit_Name
                    else: user = None
                    report = logger(request,user)
                except Exception as inst:
                    report = inst
                accessfile.write(str(report))
                accessfile.close()

        @app.teardown_request
        def after_request(response):
            db.close()
            return response

        return app

def logger(request,user):
    ip = request.environ['HTTP_X_FORWARDED_FOR']
    uri = request.environ['RAW_URI']
    if request.method == 'POST':
        payload = request.get_json(force=True)
    else: payload = ''
    report = (f"{time.asctime()}	{ip}	{user}	{uri}	{payload}\n")
    return(report)