import random, time, sys, json, os, asyncio, aiohttp
from decimal import Decimal
from os import path
from flask import current_app as app
from peewee import *
from shared.models import *
from shared.calculator.ranges_files.ranges_calc import brc_calc
import flask_app.webhook_functions as webhook_functions


async def routing(received):
    commands_dict = {'pitch':pitch,'swing':swing,'steal':steal,'throw':throw,'lists':lists}
    msg = await commands_dict[received['Command']](received)
    return(msg)

async def gamestatus_check(game):
    payload = {'Game_Number':game.Game_Number}
#    url = (f"http://167.71.181.99:5000/games/manage/check")
    url = (f"https://majorleagueguessball.com/games/manage/check")
    async with aiohttp.ClientSession() as session:
        async with session.post(url,json=payload) as resp:
            await resp.text()

async def swing(received):
    if received['Redditor']:
        reddit_name = received['Redditor']
        batters = (Games
         .select(Games,Players).join(Lineups).join(Players).join(Users)
         .where((Users.Reddit_Name == reddit_name) &
                (Games.Status == 'Started') &
                (Games.Batter == Players.Player_ID)))
    elif received['Discord']:
        snowflake = received['Discord']
        batters = (Games
         .select(Games,Players).join(Lineups).join(Players).join(Users)
         .where((Users.Discord_ID == snowflake) &
                (Games.Status == 'Started') &
                (Games.Batter == Players.Player_ID)))
    if len(batters) > 0:
        for entry in batters:
            with db.atomic():
                entry.Swing = int(received['Number'])
                entry.B_Flavor = received['Flavor']
                entry.save()
            await gamestatus_check(entry)
            msg = (f"Your swing of {int(received['Number'])} has been submitted in {entry.Game_ID}.")
            return(msg)
    else:
        msg = (f"You aren't up to bat in any games right now.")
        return(msg)

# Old batter select code based on max box score instead of currently active batter
#    elif received['Discord']:
#        snowflake = received['Discord']
#        batter = (Lineups
#         .select(Lineups,Players,Games).join(Games).switch(Lineups).join(Players).join(Users)
#         .where((Users.Discord_ID == snowflake) & 
#                (Lineups.Game_Number.Status == 'Started') & 
#                (Lineups.Order != 0)
#                )).objects()
#    if len(batter) > 0:
#        for entry in batter:
#            if ((entry.Game_Number.Inning[0] == 'T' and entry.Game_Number.Away.Team_Abbr == entry.Player.Team.Team_Abbr and entry.Game_Number.A_Bat_Pos == entry.Order) or
#                (entry.Game_Number.Inning[0] == 'B' and entry.Game_Number.Home.Team_Abbr == entry.Player.Team.Team_Abbr and entry.Game_Number.H_Bat_Pos == entry.Order)):
#                max_box = (Lineups
#                 .select(fn.MAX(Lineups.Box))
#                 .where((Lineups.Game_Number == entry.Game_Number.Game_Number) & 
#                        (Lineups.Team == entry.Player.Team.Team_Abbr) & 
#                        (Lineups.Position == entry.Position)
#                        )).scalar()
#                if entry.Box == max_box:
#                    entry.Game_Number.Swing = int(received['Number'])
#                    entry.Game_Number.save()
#                    await gamestatus_check(entry.Game_Number)
#                    msg = (f"Your swing of {int(received['Number'])} has been submitted in {entry.Game_Number.Game_ID}.")
#                    return(msg)


async def pitch(received):
    if received['Redditor']:
        reddit_name = received['Redditor']
        pitchers = (Games
         .select(Games,Players).join(Lineups).join(Players).join(Users)
         .where((Users.Reddit_Name == reddit_name) &
                (Games.Status == 'Started') &
                (Games.Pitcher == Players.Player_ID)))
    elif received['Discord']:
        snowflake = received['Discord']
        pitchers = (Games
         .select(Games,Players).join(Lineups).join(Players).join(Users)
         .where((Users.Discord_ID == snowflake) &
                (Games.Status == 'Started') &
                (Games.Pitcher == Players.Player_ID)))
    if len(pitchers) > 0:
        for entry in pitchers:
            with db.atomic():
                entry.Pitch = int(received['Number'])
                entry.save()
            await gamestatus_check(entry)
            msg = (f"Your pitch of {int(received['Number'])} has been submitted in {entry.Game_ID}.")
            return(msg)
    else:
        msg = (f"You aren't on the mound in any games right now.")
        return(msg)

async def steal(received):
    if received['Redditor']:
        reddit_name = received['Redditor']
        runners = (Games
         .select(Games,Players).join(Lineups).join(Players).join(Users)
         .where((Users.Reddit_Name == reddit_name) &
                (Games.Status == 'Started') &
                (
                ((Games.First_Base == Players.Player_ID) &
                (Games.Second_Base.is_null(True))) |
                ((Games.Second_Base == Players.Player_ID) &
                (Games.Third_Base.is_null(True))) |
                ((Games.Third_Base == Players.Player_ID))
                )
         )).objects()
    elif received['Discord']:
        snowflake = received['Discord']
        runners = (Games
         .select(Games,Players).join(Lineups).join(Players).join(Users)
         .where((Users.Discord_ID == snowflake) &
                (Games.Status == 'Started') &
                (
                ((Games.First_Base == Players.Player_ID) &
                (Games.Second_Base.is_null(True))) |
                ((Games.Second_Base == Players.Player_ID) &
                (Games.Third_Base.is_null(True))) |
                ((Games.Third_Base == Players.Player_ID))
                )
         )).objects()
    if len(runners) > 0:
        with db.atomic():
            game_no = None
            for entry in runners:
                brc = brc_calc(entry) 
                if (brc == 1 or brc == 5) and entry.First_Base.Player_ID == entry.Player_ID:
                    runner_num = 1
                    game_no = entry.Game_Number
                    break
                elif (brc == 2 or brc == 4) and entry.Second_Base.Player_ID == entry.Player_ID:
                    runner_num = 2
                    game_no = entry.Game_Number
                    break
                elif entry.Third_Base.Player_ID == entry.Player_ID:
                    runner_num = 3
                    game_no = entry.Game_Number
                    break
            if game_no:
                if runner_num == 1:
                    to_steal = 'second base'
                elif runner_num == 2:
                    to_steal = 'third base'
                elif runner_num == 3:
                    to_steal = 'home plate'
                game = Games.get(Games.Game_Number == game_no)
                game.Steal_Timer = time.time()
                game.Runner = runner_num
                game.R_Steal = int(received['Number'])
                game.save()
                webhook_functions.steal_start(game,runner_num)
                msg = (f"You are stealing {to_steal} with {int(received['Number'])}.")
                return(msg)
            else:
                return("You are not in a position to steal currently.")

async def throw(received):
    if received['Redditor']:
        reddit_name = received['Redditor']
        catchers = (Games
         .select(Games,Players).join(Lineups).join(Players).join(Users)
         .where((Users.Reddit_Name == reddit_name) &
                (Games.Status == 'Started') &
                (Games.Runner) &
                (Games.Catcher == Players.Player_ID)
         )).objects()
    elif received['Discord']:
        snowflake = received['Discord']
        catchers = (Games
         .select(Games,Players).join(Lineups).join(Players).join(Users)
         .where((Users.Discord_ID == snowflake) &
                (Games.Status == 'Started') &
                (Games.Runner) &
                (Games.Catcher == Players.Player_ID)
         )).objects()
    if len(catchers) > 0:
        msg = (f"There isn't an active steal attempt in your game currently.")
        with db.atomic():
            for entry in catchers:
                if entry.R_Steal:
                    game = Games.get(Games.Game_Number == entry.Game_Number)
                    game.C_Throw = int(received['Number'])
                    game.save()
                    msg = (f"Your throw of {int(received['Number'])} has been submitted.")
                    break
        if msg.startswith('Your throw of'):
            await gamestatus_check(entry)
            return(msg)
        return(msg)
    else:
        return("You aren't catching in any games currently.")

async def lists(received):
# Can't just set them to None, because we have a couple folks that are either reddit-only or Discord-only
    if received['Redditor']:
        reddit_name = received['Redditor']
        snowflake = ''
    elif received['Discord']:
        reddit_name = ''
        snowflake = received['Discord']
    players = (Players
     .select(Players).join(Users)
     .where((Users.Discord_ID == snowflake) or (Users.Reddit_Name == reddit_name))).objects()
    if len(players) == 1:
        player_id = players[0].Player_ID
    elif len(players) > 1:
        send = []
        check = []
        for i in players:
            check.append(i.Player_ID)
            send.append([i.Player_ID,i.Player_Name])
        if received['Player_ID'] in check:
            player_id = received['Player_ID']
        else:
            msg = (f"You have multiple players tied to your account. Please specify which. {send}")
            return(msg)
    elif len(players) == 0:
        msg = "You don't seem to have any players linked to your account."
        return(msg)
    else:
        return("Not sure why this happened; contact Tygen")
    games = (Games
         .select(Games).join(Lineups).join(Players)
         .where((Players.Player_ID == player_id) &
                ((Games.Status == 'Started') or (Game.Status == 'Init'))
     ).distinct()).objects()
    if len(games) == 1:
        game_number = games[0].Game_Number
    elif len(games) > 1:
        game_list = []
        for game in games:
            game_list.append(game.Game_Number)
        if received['Game_Number'] in game_list:
            game_number = received['Game_Number']
        else:
            msg = (f"You are in multiple games currently. Please specify which game you're interested in. Games: {game_list}")
            return(msg)
    elif len(games) == 0:
        msg = (f"You aren't in any initialized or active games.")
        return(msg)
    else:
        return("Game number is broken; contact Tygen to fix.")
    if received['Subcommand'] == 'submit':
        msg = list_submit(received,game_number,player_id)
        return(msg)
    elif received['Subcommand'] == 'show':
        msg = list_show(received,game_number,player_id)
        return(msg)
    elif received['Subcommand'] == 'reset':
        msg = list_reset(received,game_number,player_id)
        return(msg)
    else:
        msg = "You broke it somehow."
        return(msg)

def list_show(received,game_number,player_id):
    lists = (List_Nums
            .select(List_Nums).join(Players)
            .where((List_Nums.Game_Number == game_number) &
                   (Players.Player_ID == player_id) &
                   (List_Nums.Position == received['Position']))).objects()
    if len(lists) > 1:
        msg = (f"You have multiple lists for this game submitted at this position! You broke it!")
        return(msg)
    elif len(lists) == 1:
        msg = (f"Game: {game_number}; Position: {lists[0].Position}; Current list: {lists[0].List}")
        return(msg)
    elif len(lists) == 0:
        msg = (f"You don't have any submitted lists for this game, {game_number}, yet.")
        return(msg)
    else:
        return("I don't know what happened")

def list_submit(received,game_number,player_id):
    processed_list = []
    raw_list = received['Numbers'].split(',')
    for input in raw_list:
        try:
            inp = int(input)
            if inp > 0 and inp < 1001:
                processed_list.append(inp)
        except:
            continue
    if len(processed_list) > 5:
        del processed_list[5:]
    if len(processed_list) > 0:
        data = {}
        data['Player_ID'] = player_id
        data['Game_Number'] = game_number
        data['Position'] = received['Position']
        data['List'] = processed_list
    with db.atomic():
        entry, created = List_Nums.get_or_create(Player_ID = data['Player_ID'],
                                                 Game_Number = data['Game_Number'],
                                                 Position = data['Position'],
                                                 defaults = {'List': data['List']})
        if not created:
            entry.List = data['List']
            entry.save()
    if created:
        msg = (f"Submitted the following {received['Position']} list in game {game_number}: {data['List']}.")
        return(msg)
    if not created:
        msg = (f"Replaced old {received['Position']} list in game {game_number} with new list: {data['List']}.")
        return(msg)

def list_reset(received,game_number,player_id):
    lists = (List_Nums
            .select(List_Nums).join(Players)
            .where((List_Nums.Game_Number == game_number) &
                   (Players.Player_ID == player_id) &
                   (List_Nums.Position == received['Position']))).objects()
    if len(lists) == 1:
        lists[0].delete_instance()
        msg = (f"Removed your list in {game_number} for {received['Position']}")
        return(msg)
    elif len(lists) > 1:
        msg = (f"Not sure how, but you have multiple lists set for this game and position. Contact Tygen.")
        return(msg)
    elif len(lists) == 0:
        msg = (f"No lists found in game {game_number} at {received['Position']}.")
        return(msg)
    else:
        return("This broke somehow. Contact Tygen.")