from flask import Blueprint, render_template, g, session, request, redirect, url_for
from flask import current_app as app
from models import Teams, Players, Games, GameCreationForm, LineupBoxForm, Lineups, db
from MLG_app.auth.auth import login_required
from peewee import *


# Blueprint Configuration
games_bp = Blueprint(
    'games_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/games/static/'
)

@games_bp.route('/games', methods=['GET'])
def games():
    game_list = Games.select()
    return render_template(
        'games.html',
        game_list=game_list
    )

@games_bp.route('/games/<game_number>', methods=['GET'])
def game_page(game_number):
    game = Games.get(Games.Game_Number == game_number)
    lineups = Lineups.select().where(Lineups.Game_Number == game.Game_Number).order_by(Lineups.Team, Lineups.Order.asc(), Lineups.Box.asc())
    return render_template(
        'game_page.html',
        game = game,
        lineups = lineups
    )

#@games_bp.route('/games/create',methods=['GET','POST'])
#@login_required
#def games_create():
#    game = Games()
#    if request.method == 'POST':
#        form = GameCreationForm(request.form, obj=game)
#        if form.validate():
#            form.populate_obj(game)
#            game.save()
#            flash('Successfully added %s' % game, 'success')
#            return redirect(url_for('game_page', game_number=game.Game_Number))
#    else:
#        form = GameCreationForm(obj=game)
#
#    return render_template('game_create.html', game=game, form=form)
##    if session['commissioner']:
##        teams = Teams.select()
##        return render_template(
##            'game_create.html',
##            teams=teams
##        )

@games_bp.route('/games/manage',methods=['GET'])
@login_required
def games_manage():
    game_list=Games.select()
    if session['umpire']:
        visible_games = []
        for game in game_list:
            if game.Umpires:
                if session['username'] in game.Umpires:
                    visible_games.append(game)
    if session['commissioner']:
        visible_games = game_list
    return render_template(
        'manage/games_manage.html',
        game_list=visible_games
    )

@games_bp.route('/games/manage/<game_number>', methods=['GET', 'POST'])
@login_required
def game_manage(game_number):
    game = Games.get(Games.Game_Number == game_number)
    lineups = Lineups.select().where(Lineups.Game_Number == game.Game_Number).order_by(Lineups.Team, Lineups.Order.asc(), Lineups.Box.asc())
    return render_template(
        'manage/game_manage.html',
        game = game,
        lineups = lineups
    )

@games_bp.context_processor
def jinja_utilities():
    def boxscore_active(lineups,entry):
        max_box = lineups.select(fn.MAX(Lineups.Box)).where((Lineups.Game_Number == entry.Game_Number.Game_Number) & (Lineups.Position == entry.Position) & (Lineups.Team == entry.Team.Team_Abbr)).scalar()
        if entry.Box == max_box: 
            status = 'active'
        else: 
            status = 'inactive'
        return status
    return dict(boxscore_active=boxscore_active)

@games_bp.route('/games/manage/<game_number>/lineups', methods=['GET', 'POST'])
@login_required
def lineup_manage(game_number):
    form = LineupBoxForm()
    game = Games.get(Games.Game_Number == game_number)
    if game.Status == 'Staged' or game.Status == 'Final':
        return redirect(url_for('games_bp.game_manage',game_number=game_number))
    lineups = Lineups.select().where(Lineups.Game_Number == game.Game_Number).order_by(Lineups.Team, Lineups.Order.asc(), Lineups.Box.asc())
    if request.method == 'POST':
        if form.validate_on_submit():
            for entry in form.bop:
                player = Lineups.get((Lineups.Player==entry.player_id.data) & (Lineups.Game_Number == game.Game_Number)).Player
                player_update = {'Game_Number':game_number, 'Team':player.Team.Team_Abbr,'Player':player.Player_ID,'Box':entry.box.data,'Order':entry.order.data,'Position':entry.pos.data}
                num = Lineups.update(player_update).where((Lineups.Game_Number == game.Game_Number) & (Lineups.Player == player.Player_ID)).execute()
        return redirect(url_for('games_bp.game_manage',game_number=game_number))
    else:
        for entry in lineups:
            form.bop.append_entry(data=lineup_populate(entry.Player,game))
    return render_template(
        'manage/lineup_manage.html',
        form = form,
        game = game,
        lineups = lineups
    )

@games_bp.route('/games/manage/<game_number>/init', methods=['GET', 'POST'])
@login_required
def game_init(game_number):
    game = Games.get(Games.Game_Number == game_number)
    if session['commissioner'] and game.Status == 'Staged':
        a_players = Players.select().where(Players.Team == game.Away.Team_Abbr)
        h_players = Players.select().where(Players.Team == game.Home.Team_Abbr)
        player_adds = []
        for player in a_players+h_players:
            player_add = {'Game_Number':game_number, 'Team':player.Team.Team_Abbr,'Player':player.Player_ID,'Box':0,'Order':0,'Position':'-'}
            player_adds.append(player_add)
        print(player_adds)
        with db.atomic():
            Lineups.insert_many(player_adds).execute()
            game.Status = 'Initialized'
            game.save()
    return redirect(url_for('games_bp.game_manage',game_number=game_number))

def lineup_populate(player,game):
    data = {}
    player_select = Lineups.get((Lineups.Game_Number == game.Game_Number) & (Lineups.Player == player.Player_ID))
    data['player_id'] = player.Player_ID
    try:
       data['box'] = player_select.Box
       data['order'] = player_select.Order
       data['pos'] = player_select.Position
    except:
        pass
    return data