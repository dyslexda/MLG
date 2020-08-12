import discord, random, time, sys, json, datetime, os, inspect, aiohttp
from discord.ext import commands
from os import path
from peewee import *
from shared.models import *
from shared.calculator.ranges_files.ranges_calc import brc_calc
import shared.calculator.decision_tree as tree


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

async def steal_start(self,message,payload):
    print('1')
    game = Games.get(Games.Game_Number == payload['Game_Number'])
    base = int(payload['Base'])
    if base == 1:
        runner_name = game.First_Base.Player_Name
        to_steal = 'second base'
    elif base == 2:
        runner_name = game.Second_Base.Player_Name
        to_steal = 'third base'
    elif base == 3:
        runner_name = game.Third_Base.Player_Name
        to_steal = 'home plate'
    catcher = await catcher_DM(self,game)
    print([base,runner_name,to_steal])
    await catcher.send(f"{runner_name} is stealing {to_steal} in {game.Game_ID}. Please submit a throw in the format 'm!throw [num]' between 1 and 1000.")

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
            commands_dict = {'game_start':game_start,'swing_result':swing_result,'steal_result':steal_result,'next_PA':next_PA,'steal_start':steal_start}
            payload = json.loads(message.content)
            await commands_dict[payload['Command']](self,message,payload)


# Pitch and Swing commands assume only one active spot in a game at a time. Won't work if pitching/batting in multiple games. 
    @commands.command(name='pitch')
    @commands.dm_only()
    async def pitch(self, ctx, number: int = None):
        snowflake = ctx.author.id
        if number > 0 and number < 1001:
            payload = {'Command':'pitch','Number':number,'Redditor':None,'Discord':snowflake}
            msg = await tree.routing(payload)
            await ctx.send(msg)
        else:
            await ctx.send("Please send a number between 1 and 1000.")

    @commands.command(name='swing')
    @commands.dm_only()
    async def swing(self, ctx, number: int = None):
        snowflake = ctx.author.id
        if number > 0 and number < 1001:
            payload = {'Command':'swing','Number':number,'Redditor':None,'Discord':snowflake}
            msg = await tree.routing(payload)
            await ctx.send(msg)
        else:
            await ctx.send("Please send a number between 1 and 1000.")

    @commands.command(name='steal')
    @commands.dm_only()
    async def steal(self, ctx, number: int = None):
        snowflake = ctx.author.id
        if number > 0 and number < 1001:
            payload = {'Command':'steal','Number':number,'Redditor':None,'Discord':snowflake}
            msg = await tree.routing(payload)
            if type(msg) == list:
                catcher = await catcher_DM(self,msg[1])
                await catcher.send(f"{msg[2]} is stealing {msg[3]} in {msg[1].Game_ID}. Please submit a throw in the format 'm!throw [num]' between 1 and 1000.")
                await ctx.send(msg[0])
            else:
                await ctx.send(msg) 
        else:
            await ctx.send("Please send a number between 1 and 1000.")

    @commands.command(name='throw')
    @commands.dm_only()
    async def throw(self, ctx, number: int = None):
        snowflake = ctx.author.id
        if number > 0 and number < 1001:
            payload = {'Command':'throw','Number':number,'Redditor':None,'Discord':snowflake}
            msg = await tree.routing(payload)
            await ctx.send(msg)
        else:
            await ctx.send("Please send a number between 1 and 1000.")

    @commands.command(name='test')
    async def test(self,ctx):
        await ctx.send('yep')

def setup(bot):
    bot.add_cog(GametimeCog(bot))
