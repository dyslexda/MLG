import random, time, sys
from os import environ, path
from flask import Blueprint, render_template, g, session, request, redirect, url_for, flash
from flask import current_app as app
from shared.models import Teams, Players, Games, All_PAs, Lineups, db
from shared.forms import LineupBoxForm, GameStatusForm, GameCreationForm
from application.auth.auth import login_required
from peewee import *
import webhook_functions as webhook_functions
import shared.calculator.calculator as calc
from shared.functions import stat_generator
from shared.calculator.ranges_files.ranges_calc import brc_calc
from reddit_bot.sender import edit_thread, reddit_boxscore_gen, create_gamethread, reddit_threadURL, reddit_scorebug
from dotenv import load_dotenv
basedir = path.dirname(path.dirname(path.dirname(__file__)))
load_dotenv(path.join(basedir, '.env'))


# Blueprint Configuration
games_bp = Blueprint(
    'games_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/games/static/'
)

# Functions

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

def game_populate(game):
    data = {}
    data['game_id'] = game.Game_Number
    data['status'] = game.Status
    data['a_score'] = game.A_Score
    data['h_score'] = game.H_Score
    data['runner'] = game.Runner
    data['pitch'] = game.Pitch
    data['swing'] = game.Swing
    data['c_throw'] = game.C_Throw
    data['r_steal'] = game.R_Steal
    data['ump_flavor'] = game.Ump_Flavor
    data['b_flavor'] = game.B_Flavor
    data['step'] = game.Step
    data['ump_mode'] = game.Ump_Mode
    return data

def validate_lineups(raw_lineups,game):
    #builds list of lineup errors, such that each error is flashed to user if it isn't valid
    valid, errors = True, []
    req_positions = list(environ.get('REQ_POSITIONS').split(","))
    lineup_size = int(environ.get('LINEUP_SIZE'))
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
        for order in range(1,lineup_size+1):
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

# Routes

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
    brc = brc_calc(game)
    gamestats = stat_generator(game,lineups,game_pas)
    thread_url = reddit_threadURL(game)
    return render_template(
        'game_page.html',
        game = game,
        brc = brc,
        lineups = lineups,
        game_pas = game_pas,
        gamestats = gamestats,
        thread_url = thread_url
    )

def game_creation(form):
    season = form.season.data
    session = form.session.data
    if len(str(form.session.data)) == 1:
        session = '0' + str(form.session.data)
    prefix = str(season) + str(session)
    max_no = Games.select(fn.MAX(Games.Game_Number)).where(Games.Game_Number ** (prefix+"%")).tuples()[0][0]
    if max_no == None:
        game_number = prefix + '01'
    else:
        game_number = str(int(max_no)+1)
    game_id = form.away.data + form.home.data + str(form.session.data)
    game_dict = {
        'Game_Number':game_number,
        'Game_ID':game_id,
        'Season':season,
        'Session':session,
        'Away':form.away.data,
        'Home':form.home.data,
        'Umpires':['dyslexda']} #hardcoded, need to fix
    with db.atomic():
        Games.create(**game_dict)
    return(game_number)

@games_bp.route('/games/create',methods=['GET','POST'])
@login_required
def games_create():
    form = GameCreationForm()
    if session['commissioner']:
        if request.method == 'POST':
            if form.validate_on_submit():
                game_number = game_creation(form)
                return redirect(url_for('games_bp.game_manage',game_number=game_number))
    else:
        return redirect(url_for('index_bp.index'))
    return render_template(
           'game_create.html',
           form = form)

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
    game_pas = All_PAs.select().where(All_PAs.Game_No == game.Game_Number).order_by(All_PAs.Play_No.desc())
    brc = brc_calc(game)
    gamestats = stat_generator(game,lineups,game_pas)
    if request.method == 'POST':
        form = GameStatusForm()
        if form.validate_on_submit():
            auto = None
            game.Ump_Mode = form.ump_mode.data
            if form.status.data != '' and form.step.data != None: game.Status = form.status.data
            if form.step.data != '' and form.step.data != None: game.Step = int(form.step.data)
            game.save()
            if game.Step == 1:
                if form.ump_flavor.data != '':
                    with db.atomic():
                        game.Ump_Flavor = form.ump_flavor.data
                        game.save()
            elif game.Step == 2:
                if form.auto_options.data == 'Reset Timer':
                    game.Situation = None
                    if game.Steal_Timer:
                        game.Steal_Timer = time.time()
                    else:
                        game.PA_Timer = time.time()
                    game.save()
                elif form.auto_options.data == 'Process Auto':
                    auto = game.Situation
                else:
                    if form.r_steal.data != '' and form.runner.data != '' and not game.R_Steal:
                        webhook_functions.steal_start(game,form.runner.data)
                    try:
                        if form.bunt:
                            bunt = True
                    except:
                        bunt = False
                    try:
                        if form.infield_in:
                            infield_in = True
                    except:
                        infield_in = False
                    with db.atomic():
                        if form.runner.data == '':
                            form.runner.data = None
                        game_update = {'Status':form.status.data, 'Pitch':form.pitch.data,'Swing':form.swing.data,'R_Steal':form.r_steal.data,'C_Throw':form.c_throw.data,'Runner':form.runner.data, 'Ump_Flavor':form.ump_flavor.data,'B_Flavor':form.b_flavor.data,'Bunt':bunt,'Infield_In':infield_in}
                        Games.update(game_update).where(Games.Game_Number == game.Game_Number).execute()
                        game = Games.get(Games.Game_Number == game_number)
            calc.play_process(game,auto)
        return redirect(url_for('games_bp.game_manage',game_number=game_number))
    else:
        form = GameStatusForm(data=game_populate(game))
    return render_template(
        'manage/game_manage.html',
        game = game,
        form = form,
        brc = brc,
        lineups = lineups,
        game_pas = game_pas,
        gamestats = gamestats,
        user = g.user
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
#                        sp.rollback()
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
            game_pas = All_PAs.select().where(All_PAs.Game_No == game.Game_Number).order_by(All_PAs.Play_No.desc())
            gamestats = stat_generator(game,lineups,game_pas)
            msg = reddit_boxscore_gen(game,lineups,game_pas,gamestats)
            reddit_thread = create_gamethread(game,msg)
            game.Reddit_Thread = reddit_thread
            game.PA_Timer = time.time()
            game.Step = 2
            game.save()
            msg2 = reddit_scorebug(game)
            webhook_functions.game_start(game)
        elif not valid:
            for error in errors: flash(error)
    return redirect(url_for('games_bp.game_manage',game_number=game_number))

@games_bp.route('/games/manage/check', methods=['GET','POST'])
def game_check():
    if request.method == 'POST':
        payload = request.get_json()
        game = Games.get(Games.Game_Number == payload['Game_Number'])
#        result = calc.play_check(game)
        calc.play_check(game,url=url_for('games_bp.game_manage',game_number=game.Game_Number,_external=True))
#        if result[0][3] == 'Steal':
#            result = calc.play_check(game)
    return redirect(url_for('index_bp.index'))
