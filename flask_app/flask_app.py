import sys, os
sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
from flask import Flask, g
from flask_assets import Environment
from models import *

app = Flask(__name__,instance_relative_config=True)
app.config.from_object('config.Config')
assets = Environment()
assets.init_app(app)

with app.app_context():
    from index import index
    from teams import teams
    from players import players
    from auth import auth
    from admin import admin
    from games import games


    app.register_blueprint(index.index_bp)
    app.register_blueprint(teams.teams_bp)
    app.register_blueprint(players.players_bp)
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(admin.admin_bp)
    app.register_blueprint(games.games_bp)


@app.before_request
def before_request():
    g.db = db
    g.db.connect()

@app.after_request
def after_request(response):
    g.db.close()
    return response


if __name__ == "__main__":
    app.run(host='0.0.0.0')
