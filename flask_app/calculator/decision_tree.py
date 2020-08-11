import random, time, sys, json, os, asyncio, aiohttp
from decimal import Decimal
from os import path
from flask import current_app as app
from peewee import *
from shared.models import *
from flask_app.calculator.ranges_files.ranges_calc import brc_calc

async def routing(received):
    commands_dict = {'pitch':pitch,'swing':swing,'steal':steal,'throw':throw}
    msg = await commands_dict[received['Command']](received)
    return(msg)

async def gamestatus_check(game):
    payload = {'Game_Number':game.Game_Number}
    url = (f"http://167.71.181.99:5000/games/manage/check")
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

# Old pitcher select code based on max box score
#    elif received['Discord']:
#        snowflake = received['Discord']
#        pitcher = (Lineups
#         .select(Lineups,Players,Games).join(Games).switch(Lineups).join(Players).join(Users)
#         .where((Users.Discord_ID == snowflake) & 
#                (Lineups.Game_Number.Status == 'Started') & 
#                (Lineups.Position == 'P')
#                )).objects()
#    if len(pitcher) > 0:
#        for entry in pitcher:
#            if ((entry.Game_Number.Inning[0] == 'T' and entry.Game_Number.Home.Team_Abbr == entry.Player.Team.Team_Abbr) or
#                (entry.Game_Number.Inning[0] == 'B' and entry.Game_Number.Away.Team_Abbr == entry.Player.Team.Team_Abbr)):
#                max_box = (Lineups
#                 .select(fn.MAX(Lineups.Box))
#                 .where((Lineups.Game_Number == entry.Game_Number.Game_Number) & 
#                        (Lineups.Team == entry.Player.Team.Team_Abbr) & 
#                        (Lineups.Position == entry.Position)
#                        )).scalar()
#                if entry.Box == max_box:
#                    entry.Game_Number.Pitch = int(received['Number'])
#                    entry.Game_Number.save()
#                    await gamestatus_check(entry.Game_Number)
#                    msg = (f"Your pitch of {int(received['Number'])} has been submitted in {entry.Game_Number.Game_ID}.")
#                    return(msg)
#        msg = (f"You've been benched in {entry.Game_Number.Game_ID} and can't submit numbers!")
#        return(msg)
#    else:
#        msg = (f"You aren't on the mound in any games right now.")
#        return(msg)

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
                    runner_name = entry.First_Base.Player_Name
                    game_no = entry.Game_Number
                    break
                elif (brc == 2 or brc == 4) and entry.Second_Base.Player_ID == entry.Player_ID:
                    runner_num = 2
                    runner_name = entry.Second_Base.Player_Name
                    game_no = entry.Game_Number
                    break
                elif entry.Third_Base.Player_ID == entry.Player_ID:
                    runner_num = 3
                    runner_name = entry.Third_Base.Player_Name
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
                game.Runner = runner_num
                game.R_Steal = int(received['Number'])
                game.Steal_Timer = time.time()
                game.save()
                msg = (f"You are stealing {to_steal} with {int(received['Number'])}.")
                return([msg,game,runner_name,to_steal])
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