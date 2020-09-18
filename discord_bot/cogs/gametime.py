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

async def ump_ping(self,message,payload):
    game = Games.get(Games.Game_Number == payload['Game_Number'])
    umpires = game.Umpires
    for ump in umpires:
        ump_q = (Users
            .select()
            .where(Users.Reddit_Name == ump)
            ).objects()
        umpire = self.bot.get_user(int(ump_q[0].Discord_ID))
        await createDM(umpire)
        await umpire.dm_channel.send(payload['Message'])

async def game_start(self,message,payload):
    game = Games.get(Games.Game_Number == payload['Game_Number'])
    msg,pitcher,batter = await pitcher_batter_DMs(self,game)
    a_catcher,h_catcher = await catchers_DM(self,game,payload['A_Catcher'],payload['H_Catcher'])
    await pitcher.dm_channel.send(f"{game.Game_ID} has started, and you are on the mound! Please send a pitch using 'm!pitch [num]', with a number from 1 to 1000.\n {msg}")
    await batter.dm_channel.send(f"{game.Game_ID} has started, and you are up to bat! Please send a swing using 'm!swing [num]', with a number from 1 to 1000.\n {msg}")
    catcher_msg = (f"{game.Game_ID} has started and you are a starting catcher. Please send a list of numbers to be used on any steal attemps, in the format 'm!list submit;C;<num>,<num>,<num>'. Use 'm!help list' for more information.")
    await a_catcher.dm_channel.send(catcher_msg)
    await h_catcher.dm_channel.send(catcher_msg)

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
    try:
        catcher_list = List_Nums.get((List_Nums.Game_Number == game.Game_Number) &
                                    (List_Nums.Player_ID == game.Catcher.Player_ID) &
                                    (List_Nums.Position == 'C'))
    except:
        catcher_list = None
    if catcher_list:
        await catcher.send(f"{runner_name} is stealing {to_steal} in {game.Game_ID}. You have 30 minutes to submit a number. If you don't, your first list number of {catcher_list.List[0]} will be used.")
    else:
        await catcher.send(f"{runner_name} is stealing {to_steal} in {game.Game_ID}. Please submit a throw in the format 'm!throw [num]' between 1 and 1000. You do not have a list submitted, so if you do not submit a number now, an auto-steal will result.")

async def catcher_list(self,game):
    catcher = (Players
                .get(Players.Player_ID == game.Catcher.Player_ID)
                ).objects()[0]

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

async def catchers_DM(self,game,a_catcher_id,h_catcher_id):
    a_catcher = self.bot.get_user(int(a_catcher_id))
    h_catcher = self.bot.get_user(int(h_catcher_id))
    await createDM(a_catcher)
    await createDM(h_catcher)
    return(a_catcher,h_catcher)

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
#    url = (f"http://167.71.181.99:5000/games/manage/check")
    url = (f"https://majorleagueguessball.com/games/manage/check")
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
            commands_dict = {'game_start':game_start,'swing_result':swing_result,'steal_result':steal_result,'next_PA':next_PA,'steal_start':steal_start,'ump_ping':ump_ping}
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
    async def swing(self, ctx, number: int = None, *, arg=None):
        snowflake = ctx.author.id
        if number > 0 and number < 1001:
            payload = {'Command':'swing','Number':number,'Redditor':None,'Discord':snowflake,'Flavor':arg}
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

    @commands.command(name='list')
    @commands.dm_only()
    async def list(self, ctx, *, arg):
        """Example commands:
            m!list submit;50102;P;250,750
            m!list submit;C;780,992,800,311,80
            m!list reset;B
        
        To manage lists, use:
            m!list submit;<player_id>;<game>;<position>;<num1>,<num2>,<num3> - Submits numbers for list
            m!list show;<player_id>;<game>;<position> - Returns numbers in list
            m!list reset;<player_id>;<game>;<position> - Empties list
        
        <position> is required, and the following are acceptable:
            p,P,pitcher,Pitcher
            c,C,catcher,Catcher
            b,B,batter,Batter
        
        <game> is optional, as the bot will search for any active game you are in.
        However, if you are in multiple games, without designating the correct game
        it will simply set the list for the first retrieved game. Additionally, if the game
        you are submitting for has not yet started, it will not be able to store the list properly.
        Set the game number using the ID code, most easily found on the website (e.g., '50201').
        
        <player_id> is optional and likely should never be used outside of testing.
        
        Up to five numbers are accepted at the end of the submit command. Any invalid numbers
        will be discarded and the rest of the list used. Please separate numbers using commas.
        """
        arg_list = arg.split(';')
        if arg_list[0] not in ['submit','show','reset']:
            await ctx.send("Please use the 'submit', 'show', or 'reset' subcommands. Use 'm!help list' for detailed help.")
        else:
            try:
                player_id = int(arg_list[1])
                player = Players.get(Players.Player_ID == player_id)
                arg_list.pop(1)
            except:
                player_id = None
            try:
                game_number = int(arg_list[1])
                game = Games.get(Games.Game_Number == game_number)
                arg_list.pop(1)
            except:
                game_number = None
            if arg_list[1].upper() in ['P','PITCHER']:
                position = 'P'
                arg_list.pop(1)
            elif arg_list[1].upper() in ['C','CATCHER']:
                position = 'C'
                arg_list.pop(1)
            elif arg_list[1].upper() in ['B','BATTER']:
                position = 'B'
                arg_list.pop(1)
            else:
                position = None
                await ctx.send("I didn't recognize the position; please use 'm!help list' for detailed help.")
            snowflake = ctx.author.id
            if position:
                if arg_list[0] == 'submit':
                    payload = {'Command':'lists','Subcommand':'submit','Redditor':None,'Discord':snowflake,
                               'Game_Number':game_number,'Position':position,'Player_ID':player_id,'Numbers':arg_list[1]}
                    msg = await tree.routing(payload)
                    await ctx.send(msg)
                elif arg_list[0] == 'show':
                    payload = {'Command':'lists','Subcommand':'show','Redditor':None,'Discord':snowflake,
                               'Game_Number':game_number,'Position':position,'Player_ID':player_id}
                    msg = await tree.routing(payload)
                    await ctx.send(msg)
                elif arg_list[0] == 'reset':
                    payload = {'Command':'lists','Subcommand':'reset','Redditor':None,'Discord':snowflake,
                               'Game_Number':game_number,'Position':position,'Player_ID':player_id}
                    msg = await tree.routing(payload)
                    await ctx.send(msg)

    @commands.command(name='test')
    async def test(self,ctx,number: int = None,*,arg=None):
        """Test help???"""
#        print(type(arg))
        await ctx.send(number)
        await ctx.send(arg)

def setup(bot):
    bot.add_cog(GametimeCog(bot))
