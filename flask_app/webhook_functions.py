import json, requests
from flask import current_app as app
from discord import Webhook, RequestsWebhookAdapter
from shared.models import Lineups, Players, Users
from peewee import *

def game_start(game):
    pitcher = get_pitcher(game)
    batter = get_batter(game)
    payload = {'Command':'game_start','Game_Number':game.Game_Number,'Pitcher':pitcher,'Batter':batter}
    webhook_send(json.dumps(payload))

def swing_result(game,msg):
    payload = {'Command':'swing_result','Game_Number':game.Game_Number,'Pitcher':game.Pitcher.Player_ID,'Batter':game.Batter.Player_ID,'msg':msg}
    webhook_send(json.dumps(payload))

def steal_result(game,runner,msg):
    payload = {'Command':'steal_result','Game_Number':game.Game_Number,'Pitcher':game.Pitcher.Player_ID,'Catcher':game.Catcher.Player_ID,'Runner':runner.Player_ID,'msg':msg}
    webhook_send(json.dumps(payload))

def next_PA(game):
    payload = {'Command':'next_PA','Game_Number':game.Game_Number,'Pitcher':game.Pitcher.Player_ID,'Batter':game.Batter.Player_ID}
    webhook_send(json.dumps(payload))

def steal_start(game,base):
    payload = {'Command':'steal_start','Game_Number':game.Game_Number,'Base':base}
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