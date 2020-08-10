import random, time, sys, json, os, asyncio, aiohttp
from decimal import Decimal
from os import path
from flask import current_app as app
from peewee import *
from models import *

async def routing(received):
    commands_dict = {'pitch':pitch,'swing':swing}
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
        batter = (Lineups
         .select(Lineups,Players,Games).join(Games).switch(Lineups).join(Players).join(Users)
         .where((Users.Reddit_Name == reddit_name) & 
                (Lineups.Game_Number.Status == 'Started') & 
                (Lineups.Order != 0)
                )).objects()
    elif received['Discord']:
        discord_name = received['Discord']
        batter = (Lineups
         .select(Lineups,Players,Games).join(Games).switch(Lineups).join(Players).join(Users)
         .where((Users.Discord_Name == discord_name) & 
                (Lineups.Game_Number.Status == 'Started') & 
                (Lineups.Order != 0)
                )).objects()
    if len(batter) > 0:
        for entry in batter:
            if ((entry.Game_Number.Inning[0] == 'T' and entry.Game_Number.Away.Team_Abbr == entry.Player.Team.Team_Abbr and entry.Game_Number.A_Bat_Pos == entry.Order) or
                (entry.Game_Number.Inning[0] == 'B' and entry.Game_Number.Home.Team_Abbr == entry.Player.Team.Team_Abbr and entry.Game_Number.H_Bat_Pos == entry.Order)):
                max_box = (Lineups
                 .select(fn.MAX(Lineups.Box))
                 .where((Lineups.Game_Number == entry.Game_Number.Game_Number) & 
                        (Lineups.Team == entry.Player.Team.Team_Abbr) & 
                        (Lineups.Position == entry.Position)
                        )).scalar()
                if entry.Box == max_box:
                    entry.Game_Number.Swing = int(received['Number'])
                    entry.Game_Number.save()
                    await gamestatus_check(entry.Game_Number)
                    msg = (f"Your swing of {int(received['Number'])} has been submitted in {entry.Game_Number.Game_ID}.")
                    return(msg)
        msg = (f"You've been benched in {entry.Game_Number.Game_ID} and can't submit numbers!")
        return(msg)
    else:
        msg = (f"You aren't up to bat in any games right now.")
        return(msg)

async def pitch(received):
    print(received)
    if received['Redditor']:
        reddit_name = received['Redditor']
        pitcher = (Lineups
         .select(Lineups,Players,Games).join(Games).switch(Lineups).join(Players).join(Users)
         .where((Users.Reddit_Name == reddit_name) & 
                (Lineups.Game_Number.Status == 'Started') & 
                (Lineups.Position == 'P')
                )).objects()
    elif received['Discord']:
        discord_name = received['Discord']
        pitcher = (Lineups
         .select(Lineups,Players,Games).join(Games).switch(Lineups).join(Players).join(Users)
         .where((Users.Discord_Name == discord_name) & 
                (Lineups.Game_Number.Status == 'Started') & 
                (Lineups.Position == 'P')
                )).objects()
    if len(pitcher) > 0:
        for entry in pitcher:
            if ((entry.Game_Number.Inning[0] == 'T' and entry.Game_Number.Home.Team_Abbr == entry.Player.Team.Team_Abbr) or
                (entry.Game_Number.Inning[0] == 'B' and entry.Game_Number.Away.Team_Abbr == entry.Player.Team.Team_Abbr)):
                max_box = (Lineups
                 .select(fn.MAX(Lineups.Box))
                 .where((Lineups.Game_Number == entry.Game_Number.Game_Number) & 
                        (Lineups.Team == entry.Player.Team.Team_Abbr) & 
                        (Lineups.Position == entry.Position)
                        )).scalar()
                if entry.Box == max_box:
                    entry.Game_Number.Pitch = int(received['Number'])
                    entry.Game_Number.save()
                    await gamestatus_check(entry.Game_Number)
                    msg = (f"Your pitch of {int(received['Number'])} has been submitted in {entry.Game_Number.Game_ID}.")
                    return(msg)
        msg = (f"You've been benched in {entry.Game_Number.Game_ID} and can't submit numbers!")
        return(msg)
    else:
        msg = (f"You aren't on the mound in any games right now.")
        return(msg)