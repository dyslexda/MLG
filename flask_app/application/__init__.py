import sys, os, logging
from os import path
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from flask import Flask, session, g
from flask_assets import Environment
from shared.models import *

def create_app():
    app = Flask(__name__,instance_relative_config=True)
    logging.basicConfig(filename='output.log',
                        level=logging.WARNING)
    app.config.from_object('config.Config')
    assets = Environment()
    assets.init_app(app)

    with app.app_context():
        from .index import index
        from .teams import teams
        from .players import players
        from .auth import auth
        from .admin import admin
        from .games import games
        from .calc_routes import calc_routes
    
    
        app.register_blueprint(index.index_bp)
        app.register_blueprint(teams.teams_bp)
        app.register_blueprint(players.players_bp)
        app.register_blueprint(auth.auth_bp)
        app.register_blueprint(admin.admin_bp)
        app.register_blueprint(games.games_bp)
        app.register_blueprint(calc_routes.calc_bp)

        @app.before_request
        def before_request():
            db.connect()
            username = session.get('username')
            if username is None:
                g.user = None
            else:
                g.user = Users.get_or_none(Users.Reddit_Name == username)
        
        @app.teardown_request
        def after_request(response):
            db.close()
            return response

        return app