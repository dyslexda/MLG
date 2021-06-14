"""General page routes."""
from flask import Blueprint, render_template, g, abort
from flask import current_app as app
from shared.api_models import *
from decimal import Decimal
import flask_app.application.api.standings as calc_standings
import random
from flask_app.application.api.calc import *

# Blueprint Configuration
api_bp = Blueprint(
    'api_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

def get_person(person_id):
    person = Persons.get(Persons.PersonID == person_id)
    dumped = PersonsSchema().dump(person)
    return(dumped)

def get_persons():
    people = Persons.select()
    dumped = PersonsSchema(many=True).dump(people)
    return(dumped)

def get_some_persons(**kwargs):
    people = Persons.select()
    for kwarg in kwargs:
        people = people.where(getattr(Persons,kwarg) == kwargs[kwarg])
    dumped = PersonsSchema(many=True).dump(people)
    return(dumped)

def schedules(Team=None):
    schedules = Schedules.select()
    if Team:
        schedules = schedules.where((Schedules.Away == Team) | (Schedules.Home == Team))
    dumped = SchedulesSchema(many=True).dump(schedules)
    return(dumped)

def standings():
    return(calc_standings.LeagueStandings().to_dict())

def teams():
    teams = Teams.select().order_by(Teams.Abbr.asc())
    dumped = TeamsSchema(many=True).dump(teams)
    return(dumped)

def get_lineup(game_no):
    response = {}
    game = Schedules.get_or_none(Schedules.Game_No == game_no)
    if game == None: abort(404)
    home_lineup = Lineups.select().join(Persons).where(Lineups.Game_No == game_no, Lineups.Team == game.Home.Abbr).order_by(Lineups.Order, Lineups.Play_Entrance)
    away_lineup = Lineups.select().join(Persons).where(Lineups.Game_No == game_no, Lineups.Team == game.Away.Abbr).order_by(Lineups.Order, Lineups.Play_Entrance)
    dumped = LineupsSchema(many=True).dump(home_lineup)
    response["home"] = format_lineup(home_lineup)
    response["away"] = format_lineup(away_lineup)
    return(response)

def format_lineup(lineup):
    response = []
    lineup_lst = []
    order = lineup.select(fn.Distinct(Lineups.Order))
    ord_lst = [ num.Order for num in lineup.select(fn.Distinct(Lineups.Order)) ]
    if ord_lst[0] == None: 
        ord_lst.pop(0)
    for i in ord_lst:
        lineup_lst.append([])
        ord_q = lineup.where(Lineups.Order == i).order_by(Lineups.Play_Entrance)
        for player in ord_q:
            player_dict = {"Order": player.Order, "Play_Entrance": player.Play_Entrance, "Player_ID": player.Player.PersonID, "Player_Name": player.Player.Stats_Name, "Position": player.Position}
            lineup_lst[i-1].append(player_dict)
    pitchers_q = lineup.where(Lineups.Pitcher_No).order_by(Lineups.Pitcher_No)
    lineup_lst.append([])
    for player in pitchers_q:
        player_dict = {"Order": player.Order, "Play_Entrance": player.Play_Entrance, "Player_ID": player.Player.PersonID, "Player_Name": player.Player.Stats_Name, "Position": player.Position}
        lineup_lst[-1].append(player_dict)
    bench_q = lineup.where(Lineups.Play_Entrance == None, Lineups.Player.Primary != "P")
    lineup_lst.append([])
    for player in bench_q:
        player_dict = {"Order": player.Order, "Play_Entrance": player.Play_Entrance, "Player_ID": player.Player.PersonID, "Player_Name": player.Player.Stats_Name, "Position": player.Player.Primary}
        lineup_lst[-1].append(player_dict)
    bullpen_q = lineup.where(Lineups.Play_Entrance == None, Lineups.Player.Primary == "P")
    lineup_lst.append([])
    for player in bullpen_q:
        player_dict = {"Order": player.Order, "Play_Entrance": player.Play_Entrance, "Player_ID": player.Player.PersonID, "Player_Name": player.Player.Stats_Name, "Position": player.Player.Primary}
        lineup_lst[-1].append(player_dict)
    return(lineup_lst)

def plays(limit,offset,**kwargs):
    plays = PAs.select()
    for kwarg in kwargs:
        if kwarg == 'Season':
            if kwargs[kwarg] == 1:
                plays = plays.where(PAs.Play_No < 15000)
            else:
                low = kwargs[kwarg] * 10000000
                high = (kwargs[kwarg]+1) * 10000000
                plays = plays.where(PAs.Play_No.between(low,high))
        else:
            plays = plays.where(getattr(PAs,kwarg) == kwargs[kwarg])
    totalRecords = plays.count()
    plays = plays.limit(limit).offset(offset)
    dumped = PlaysSchema(many=True).dump(plays)
    response = {}
    response['plays'] = dumped
    response['limit'] = limit
    response['offset'] = offset
    response['totalRecords'] = totalRecords
    response['totalReturned'] = plays.count()
    return(response)

def calc(**kwargs):
    pitcher,pitch,batter,swing,runners,errors = argValidation(kwargs)
    if len(errors) != 0:
        return errors,400
    game = GameState(Pitcher=pitcher,Batter=batter,Outs=kwargs['outs'],First_Base=runners['b1'],Second_Base=runners['b2'],Third_Base=runners['b3'],Bunt=False,Pitch=pitch,Swing=swing)
    results,order,outcome = calcCode(game)
    response = formatResponse(game,results,order,outcome)
    return(response)
