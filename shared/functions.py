from shared.models import *
from peewee import *


def stat_generator(game,lineups,game_pas):
    gamestats = {}
    hits = ['HR','3B','2B','1B','IF1B','1BWH','1BWH2','2BWH']
    one_outs = ['FO','PO','GO','K','GORA','FC','FC3rd','DPRun','FCH','K','DFO','DSacF','SacF','CS2','CS3','CS4']
    two_outs = ['DP21','DP31','DPH1','DP']
    with db.atomic():
        for entry in lineups:
            test = '3'
            gamestats[entry.Player.Player_ID] = {}
            gamestats[entry.Player.Player_ID]['Pitching'] = {}
            gamestats[entry.Player.Player_ID]['Pitching']['IP'] = ip_calc(
                (game_pas.select().where((All_PAs.Result << one_outs) & (All_PAs.Pitcher_ID == entry.Player.Player_ID)).count()) + 
                (game_pas.select().where((All_PAs.Result << two_outs) & (All_PAs.Pitcher_ID == entry.Player.Player_ID)).count()*2) +
                (game_pas.select().where((All_PAs.Result == 'TP') & (All_PAs.Pitcher_ID == entry.Player.Player_ID)).count()*3))
            gamestats[entry.Player.Player_ID]['Pitching']['ER'] = none_to_zero(game_pas.select(fn.SUM(All_PAs.Run_Scored)).where(All_PAs.Pitcher_ID == entry.Player.Player_ID).scalar())
            gamestats[entry.Player.Player_ID]['Pitching']['H'] = game_pas.select().where((All_PAs.Result << hits) & (All_PAs.Pitcher_ID == entry.Player.Player_ID)).count()
            gamestats[entry.Player.Player_ID]['Pitching']['BB'] = game_pas.select().where((All_PAs.Result == 'BB') & (All_PAs.Pitcher_ID == entry.Player.Player_ID)).count()
            gamestats[entry.Player.Player_ID]['Pitching']['K'] = game_pas.select().where((All_PAs.Result == 'K') & (All_PAs.Pitcher_ID == entry.Player.Player_ID)).count()
            gamestats[entry.Player.Player_ID]['Pitching']['ERA'] = ''
            gamestats[entry.Player.Player_ID]['Batting'] = {}
            gamestats[entry.Player.Player_ID]['Batting']['AB'] = game_pas.select().where((All_PAs.Result != 'BB') & (All_PAs.Batter_ID == entry.Player.Player_ID)).count()
            gamestats[entry.Player.Player_ID]['Batting']['R'] = game_pas.select().where((All_PAs.Batter_ID == entry.Player.Player_ID) & (All_PAs.Run_Scored == 1)).count()
            gamestats[entry.Player.Player_ID]['Batting']['H'] = game_pas.select().where((All_PAs.Result << hits) & (All_PAs.Batter_ID == entry.Player.Player_ID)).count()
            gamestats[entry.Player.Player_ID]['Batting']['RBI'] = none_to_zero(game_pas.select(fn.SUM(All_PAs.RBIs)).where(All_PAs.Batter_ID == entry.Player.Player_ID).scalar())
            gamestats[entry.Player.Player_ID]['Batting']['BB'] = game_pas.select().where((All_PAs.Result == 'BB') & (All_PAs.Batter_ID == entry.Player.Player_ID)).count()
            gamestats[entry.Player.Player_ID]['Batting']['K'] = game_pas.select().where((All_PAs.Result == 'K') & (All_PAs.Batter_ID == entry.Player.Player_ID)).count()
            gamestats[entry.Player.Player_ID]['Batting']['BA'] = ''
    return gamestats

def ip_calc(outs):
    full = outs // 3
    partial = outs % 3
    ip = (f"{full}.{partial}")
    return(ip)

def none_to_zero(data):
    if data == None:
        data = 0
    return(data)