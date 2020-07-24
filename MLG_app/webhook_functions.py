import json, requests
from flask import current_app as app
from discord import Webhook, RequestsWebhookAdapter
from models import Lineups, Players, Users
from peewee import *

def game_start(game):
    pitcher = get_pitcher(game)
    batter = get_batter(game)
    payload = {'Command':'game_start','Game_Number':game.Game_Number,'Pitcher':pitcher,'Batter':batter}
    webhook_send(json.dumps(payload))

def get_batter(game):
    if game.Inning[0] == 'T':
        team_abbr = game.Away.Team_Abbr
        bat_pos = game.A_Bat_Pos
    else:
        team_abbr = game.Home.Team_Abbr
        bat_pos = game.H_Bat_Pos
    max_box = Lineups.select(fn.MAX(Lineups.Box)).where((Lineups.Game_Number == game.Game_Number) & (Lineups.Order == bat_pos) & (Lineups.Team == team_abbr)).scalar()
    batter = (Players
             .select(Players.Player_ID).join(Users).switch(Players).join(Lineups)
             .where((Lineups.Game_Number == game.Game_Number) & (Lineups.Team == team_abbr) & (Lineups.Order == bat_pos) & (Lineups.Box == max_box))).objects()[0]
    return(batter.Player_ID)

def get_pitcher(game):
    if game.Inning[0] == 'T':
        team_abbr = game.Home.Team_Abbr
    else:
        team_abbr = game.Away.Team_Abbr
    max_box = Lineups.select(fn.MAX(Lineups.Box)).where((Lineups.Game_Number == game.Game_Number) & (Lineups.Position == 'P') & (Lineups.Team == team_abbr)).scalar()
    pitcher = (Players
             .select(Players.Player_ID).join(Users).switch(Players).join(Lineups)
             .where((Lineups.Game_Number == game.Game_Number) & (Lineups.Team == team_abbr) & (Lineups.Position == 'P') & (Lineups.Box == max_box))).objects()[0]
    return(pitcher.Player_ID)

def webhook_send(message):
    with requests.Session() as s:
        webhook = Webhook.partial(app.config['WEBHOOK_ID'], app.config['WEBHOOK_TOKEN'], adapter=RequestsWebhookAdapter(s))
        webhook.send(message)