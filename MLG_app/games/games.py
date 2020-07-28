from flask import Blueprint, render_template, g, session, request, redirect, url_for, flash
from flask import current_app as app
from models import Teams, Players, Games, GameCreationForm, LineupBoxForm, Lineups, All_PAs, db
from MLG_app.auth.auth import login_required
from peewee import *
import MLG_app.webhook_functions as webhook_functions
import calculator.calculator as calc


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
    game_pas = All_PAs.select().where(All_PAs.Game_No == game.Game_Number).order_by(All_PAs.Play_No.desc())
    msg = score_bug(game)
    return render_template(
        'game_page.html',
        game = game,
        lineups = lineups,
        game_pas = game_pas,
        msg = msg
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
            raw_lineups = {}
            raw_lineups[game.Away.Team_Abbr],raw_lineups[game.Home.Team_Abbr] = [],[]
            with db.atomic() as txn:
                with db.savepoint() as sp:
                    for entry in form.bop:
                        player = Lineups.get((Lineups.Player==entry.player_id.data) & (Lineups.Game_Number == game.Game_Number)).Player
                        player_update = {'Game_Number':game_number, 'Team':player.Team.Team_Abbr,'Player':player.Player_ID,'Box':entry.box.data,'Order':entry.order.data,'Position':entry.pos.data}
                        raw_lineups[player.Team.Team_Abbr].append(player_update)
                        Lineups.update(player_update).where((Lineups.Game_Number == game.Game_Number) & (Lineups.Player == player.Player_ID)).execute()
                    valid, errors = validate_lineups(raw_lineups,game)
                    if not valid:
                        sp.rollback()
                        for error in errors: flash(error)
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
        with db.atomic():
            Lineups.insert_many(player_adds).execute()
            game.Status = 'Init'
            game.save()
    return redirect(url_for('games_bp.game_manage',game_number=game_number))

@games_bp.route('/games/manage/<game_number>/start', methods=['GET', 'POST'])
@login_required
def game_start(game_number):
    game = Games.get(Games.Game_Number == game_number)
    if session['commissioner'] and game.Status == 'Init':
        lineups = Lineups.select().where(Lineups.Game_Number == game.Game_Number).order_by(Lineups.Team, Lineups.Order.asc(), Lineups.Box.asc())
        raw_lineups = {}
        raw_lineups[game.Away.Team_Abbr],raw_lineups[game.Home.Team_Abbr] = [],[]
        for entry in lineups:
            player_update = {'Game_Number':game_number, 'Team':entry.Player.Team.Team_Abbr,'Player':entry.Player.Player_ID,'Box':entry.Box,'Order':entry.Order,'Position':entry.Position}
            raw_lineups[entry.Player.Team.Team_Abbr].append(player_update)
        valid, errors = validate_lineups(raw_lineups,game)
        if valid:
            calc.active_players(game)
            game.Status = 'Started'
            game.save()
            webhook_functions.game_start(game)
        elif not valid:
            for error in errors: flash(error)
    return redirect(url_for('games_bp.game_manage',game_number=game_number))

@games_bp.route('/games/manage/check', methods=['GET','POST'])
def game_check():
    if request.method == 'POST':
        payload = request.get_json()
        game = Games.get(Games.Game_Number == payload['Game_Number'])
        result = calc.play_check(game)
        print(result)
        if result[0][3] == 'Steal':
            result = calc.play_check(game) #Why isn't this working? Returns "None"
            print(result)
    return redirect(url_for('index_bp.index'))

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

def validate_lineups(raw_lineups,game):
    #builds list of lineup errors, such that each error is flashed to user if it isn't valid
    valid, errors = True, []
    req_positions = ['P','C','2B','CF']
    for team in [game.Away,game.Home]:
        #Make sure initial lineup is clean, i.e. 1 box numbers for everyone
        if game.Status == 'Init':
            max_box = max([entry['Box'] for entry in raw_lineups[team.Team_Abbr]])
            if max_box == 0:
                errors.append(f'{team.Team_Abbr} has no box set')
                valid = False
            elif max_box > 1:
                errors.append(f'{team.Team_Abbr} has a max box of {max_box}; should not be higher than 1 to start')
                valid = False
        #Make sure each position is properly accounted for, e.g. don't have a box 2 pitcher without two pitchers
        #and each box is unique, e.g don't have two pitchers as 2 box
        for pos in req_positions:
            pos_count = ([entry['Position'] for entry in raw_lineups[team.Team_Abbr]]).count(pos)
            if pos_count == 0:
                errors.append(f'{team.Team_Abbr} is missing someone in the {pos} position')
                valid = False
            else:
                pos_box = [entry['Box'] for entry in raw_lineups[team.Team_Abbr] if entry['Position'] == pos]
                if pos_count != max(pos_box):
                    errors.append(f'{team.Team_Abbr} has {pos_count} total {pos} but a max box for that position of {max(pos_box)}')
                    valid = False
                if len(set(pos_box)) != len(pos_box):
                    errors.append(f'{team.Team_Abbr} has duplicate boxes for the {pos} position')
                    valid = False
        #Do same as for positions, but now for order
        for order in range(1,4):
            order_count = ([entry['Order'] for entry in raw_lineups[team.Team_Abbr]]).count(order)
            if order_count == 0:
                errors.append(f'{team.Team_Abbr} is missing someone in the {order} spot')
                valid = False
            else:
                order_box = [entry['Box'] for entry in raw_lineups[team.Team_Abbr] if entry['Order'] == order]
                if order_count != max(order_box):
                    errors.append(f'{team.Team_Abbr} has {order_count} total {order} order, but a max box for that position of {max(order_box)}')
                    valid = False
                if len(set(order_box)) != len(order_box):
                    errors.append(f'{team.Team_Abbr} has duplicate boxes for the {order} order slot')
                    valid = False
    return(valid,errors)

def score_bug(game):
    pitcher = Players.get(Players.Player_ID == game.Pitcher.Player_ID)
    batter = Players.get(Players.Player_ID == game.Batter.Player_ID)
    empty_base = '○'
    occupied_base = '●'
    top = '▲'
    bot = '▼'
    if game.Outs == 1:
        out_text = " 1 Out"
    else:
        out_text = (str(game.Outs) + " Outs")
    if game.Inning[0] == 'T': 
        inning = ("   " + top + " " + game.Inning[1:])
    else:
        inning = ("   " + bot + " " + game.Inning[1:])
    if game.First_Base is not None: first = occupied_base
    else: first = empty_base
    if game.Second_Base is not None: second = occupied_base
    else: second = empty_base
    if game.Third_Base is not None: third = occupied_base
    else: third = empty_base
    msg = []
    line1 = game.Away.Team_Abbr + ((5 - len(game.Away.Team_Abbr)) * " ") + str(game.A_Score) + "      " + second + "      " + inning
    line2 = game.Home.Team_Abbr + ((5 - len(game.Home.Team_Abbr)) * " ") + str(game.H_Score) + "    " + third + "   " + first + "    " + out_text
    msg.append(line1)
    msg.append(line2)
    msg.append(f"On the mound: {pitcher.Player_Name}")
    msg.append(f"Up to bat:    {batter.Player_Name}")
    return(msg)
