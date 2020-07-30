import discord, random, time, sys, json, datetime, os, inspect, aiohttp
from discord.ext import commands
from os import path
from peewee import *
from models import *
from calculator.ranges_files.ranges_calc import brc_calc


async def createDM(user):
    if user.dm_channel:
       pass
    else:
        await user.create_dm()

async def game_start(self,message,payload):
    game = Games.get(Games.Game_Number == payload['Game_Number'])
    msg,pitcher,batter = await pitcher_batter_DMs(self,game)
    await pitcher.dm_channel.send(f"{game.Game_ID} has started, and you are on the mound! Please send a pitch using 'm!pitch [num]', with a number from 1 to 1000.\n {msg}")
    await batter.dm_channel.send(f"{game.Game_ID} has started, and you are up to bat! Please send a swing using 'm!swing [num]', with a number from 1 to 1000.\n {msg}")

async def swing_result(self,message,payload):
    msg = payload['msg']
    game = Games.get(Games.Game_Number == payload['Game_Number'])
    msg,pitcher,batter = await pitcher_batter_DMs(self,game,msg)
    await pitcher.dm_channel.send(msg)
    await batter.dm_channel.send(msg)

async def steal_result(self,message,payload):
    msg = payload['msg']
    game = Games.get(Games.Game_Number == payload['Game_Number'])
    msg,pitcher,batter = await pitcher_batter_DMs(self,game,msg)
    catcher = await catcher_DM(self,game)
    runner = await runner_DM(self,game,payload['Runner'])
    await pitcher.dm_channel.send(msg)
    await catcher.dm_channel.send(msg)
    await runner.dm_channel.send(msg)

async def next_PA(self,message,payload):
    game = Games.get(Games.Game_Number == payload['Game_Number'])
    msg,pitcher,batter = await pitcher_batter_DMs(self,game)
    await pitcher.dm_channel.send(msg)
    await batter.dm_channel.send(msg)

async def runner_DM(self,game,runner_id):
    runner_q = (Players
                .select(Players,Users).join(Users)
                .where(Players.Player_ID == runner_id)
                ).objects()
    runner = self.bot.get_user(int(runner_q[0].User_ID.Discord_ID))
    await createDM(runner)
    return(runner)

async def catcher_DM(self,game):
    catcher_q = (Players
                .select(Players,Users).join(Users)
                .where(Players.Player_ID == game.Catcher.Player_ID)
                ).objects()
    catcher = self.bot.get_user(int(catcher_q[0].User_ID.Discord_ID))
    await createDM(catcher)
    return(catcher)

async def pitcher_batter_DMs(self,game,msg=None):
    pitcher_q = (Players
                .select(Players,Users).join(Users)
                .where(Players.Player_ID == game.Pitcher.Player_ID)
                ).objects()
    batter_q = (Players
                .select(Players,Users).join(Users)
                .where(Players.Player_ID == game.Batter.Player_ID)
                ).objects()
    pitcher = self.bot.get_user(int(pitcher_q[0].User_ID.Discord_ID))
    batter = self.bot.get_user(int(batter_q[0].User_ID.Discord_ID))
    if msg:
        pass
    else:
        msg = score_bug(game)
    await createDM(pitcher)
    await createDM(batter)
    return(msg,pitcher,batter)

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
    msg = "```"
    line1 = game.Away.Team_Abbr + ((5 - len(game.Away.Team_Abbr)) * " ") + str(game.A_Score) + "      " + second + "      " + inning + "\n"
    line2 = game.Home.Team_Abbr + ((5 - len(game.Home.Team_Abbr)) * " ") + str(game.H_Score) + "    " + third + "   " + first + "    " + out_text + "\n"
    msg += line1
    msg += line2
    msg += (f"On the mound: {pitcher.Player_Name}\n")
    msg += (f"Up to bat:    {batter.Player_Name}")
    msg += "```"
    return(msg)

async def gamestatus_check(game):
    payload = {'Game_Number':game.Game_Number}
    url = (f"http://167.71.181.99:5000/games/manage/check")
    async with aiohttp.ClientSession() as session:
        async with session.post(url,json=payload) as resp:
            await resp.text()

class GametimeCog(commands.Cog, name="Gametime"):

    def __init__(self, bot):
        self.bot = bot
        self.scrim_chan = self.bot.get_channel(676966648883838997)

    @commands.Cog.listener()
    async def on_message(self,message):
        if message.webhook_id == 735342959943483403:
            commands_dict = {'game_start':game_start,'swing_result':swing_result,'steal_result':steal_result,'next_PA':next_PA}
            payload = json.loads(message.content)
            await commands_dict[payload['Command']](self,message,payload)


# Pitch and Swing commands assume only one active spot in a game at a time. Won't work if pitching/batting in multiple games. 
    @commands.command(name='pitch')
    @commands.dm_only()
    async def pitch(self, ctx, pitch: int = None):
        snowflake = ctx.author.id
        pitcher = (Lineups
         .select(Lineups,Players,Games).join(Games).switch(Lineups).join(Players).join(Users)
         .where((Users.Discord_ID == snowflake) & 
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
                        if pitch < 1 or pitch > 1000:
                            await ctx.send("Please submit a pitch between 1 and 1000.")
                        else:
                            entry.Game_Number.Pitch = pitch
                            entry.Game_Number.save()
                            await ctx.send(f"Your pitch, {pitch}, has been submitted.")
                            await gamestatus_check(entry.Game_Number)
                    break
#                else:
#                    await ctx.send("You aren't in the game anymore!")
#            else:
#                await ctx.send("The opposing team is on the mound, not yours!")
        elif len(pitcher) == 0:
            await ctx.send("You aren't pitching in any games currently.")
#        elif len(pitcher) > 1:
#            await ctx.send("You're in multiple games now, and you broke the bot. Congrats!")

    @commands.command(name='swing')
    @commands.dm_only()
    async def swing(self, ctx, swing: int = None):
        snowflake = ctx.author.id
        batter = (Lineups
         .select(Lineups,Players,Games).join(Games).switch(Lineups).join(Players).join(Users)
         .where((Users.Discord_ID == snowflake) & 
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
                        if swing < 1 or swing > 1000:
                            await ctx.send("Please submit a swing between 1 and 1000.")
                        else:
                            entry.Game_Number.Swing = swing
                            entry.Game_Number.save()
                            await ctx.send(f"Your swing, {swing}, has been submitted.")
                            await gamestatus_check(entry.Game_Number)
                    break
                #else:
                #    await ctx.send("You aren't in the game anymore!")
            #else:
            #    await ctx.send([batter[0].Game_Number.Inning[0],batter[0].Game_Number.Away.Team_Abbr,batter[0].Player.Team.Team_Abbr,batter[0].Game_Number.A_Bat_Pos,batter[0].Order])
#                await ctx.send("The opposing team is up to bat, not yours!")
        elif len(batter) == 0:
            await ctx.send("You aren't batting in any games currently.")
#        elif len(batter) > 1:
#            await ctx.send("You're in multiple games now, and you broke the bot. Congrats!")

    @commands.command(name='steal')
    @commands.dm_only()
    async def steal(self, ctx, steal: int = None):
        snowflake = ctx.author.id
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
                if game_no and (steal > 0 and steal < 1001):
                    if runner_num == 1:
                        to_steal = 'second base'
                    elif runner_num == 2:
                        to_steal = 'third base'
                    elif runner_num == 3:
                        to_steal = 'home plate'
                    game = Games.get(Games.Game_Number == game_no)
                    game.Runner = runner_num
                    game.R_Steal = steal
                    game.save()
                    catcher = await catcher_DM(self,game)
                    await catcher.send(f"{runner_name} is stealing {to_steal} in {game.Game_ID}. Please submit a throw in the format 'm!throw [num]' between 1 and 1000.")
#                    Games.update({Games.Runner:runner_num,Games.R_Steal:steal}).where(Games.Game_Number == game_no).execute()
                    msg = (f"You are stealing {to_steal} with {steal}.")
                elif game_no and (steal < 1 or steal > 1000):
                    msg = "Please submit a steal between 1 and 1000."
        else:
            msg = "You aren't in a stealing position in any games."
        await ctx.send(msg)

    @commands.command(name='throw')
    @commands.dm_only()
    async def throw(self, ctx, throw: int = None):
        snowflake = ctx.author.id
        catchers = (Games
         .select(Games,Players).join(Lineups).join(Players).join(Users)
         .where((Users.Discord_ID == snowflake) &
                (Games.Status == 'Started') &
                (Games.Runner) &
                (Games.Catcher == Players.Player_ID)
         )).objects()
        if len(catchers) > 0:
            if throw > 0 and throw < 1001:
                with db.atomic():
                    for entry in catchers:
                        game = Games.get(Games.Game_Number == entry.Game_Number)
                        game.C_Throw = throw
                        game.save()
                        await ctx.send(f"Your throw of {throw} has been submitted.")
                        break
                await gamestatus_check(entry)

    @commands.command(name='test')
    async def test(self,ctx):
        await ctx.send('yep')

def setup(bot):
    bot.add_cog(GametimeCog(bot))
