"""General page routes."""
import json
from flask import Blueprint, render_template, g
from flask import current_app as app
from shared.models import Teams, Players
from playhouse.shortcuts import model_to_dict


# Blueprint Configuration
players_bp = Blueprint(
    'players_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/players/static/'
)



@players_bp.route('/players', methods=['GET'])
def players():
    player_list = Players.select()
    player_dict = [model_to_dict(player) for player in player_list]
    return render_template(
        'players.html',
        player_list=player_list,
        player_dict=player_dict
    )

@players_bp.route('/players/<player_id>', methods=['GET'])
def player_page(player_id):
    player = Players.get(Players.Player_ID == player_id)
    return render_template(
        'player_page.html',
        player = player
    )