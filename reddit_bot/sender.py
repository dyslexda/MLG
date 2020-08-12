import praw, random, logging
import shared.calculator.ranges_files.ranges_calc as ranges_calc
from os import environ, path
from dotenv import load_dotenv
from shared.models import All_PAs,Lineups,Players
from peewee import *

basedir = path.dirname(path.abspath(path.dirname(__file__)))
load_dotenv(path.join(basedir, '.env'))


def reddit_connect():
    r = praw.Reddit(client_id = environ.get('CLIENT_ID'),
                    client_secret = environ.get('CLIENT_SECRET'),
                    redirect_uri = environ.get('REDIRECT_URI'),
                    user_agent = environ.get('USER_AGENT'),
                    refresh_token = environ.get('REFRESH_TOKEN'))
    return(r)

#r = reddit_connect()
#print(r.auth.scopes())
#state = str(random.randint(0, 65000))
#url = r.auth.url(["*"], state, "permanent")
#print(url)
#print(r.auth.authorize('3PwDDPTsloYyHa7x1o61LkkM2E4'))
#print(environ.get('REFRESH_TOKEN')


def reddit_threadURL(game):
    r = reddit_connect()
    thread = r.submission(id=game.Reddit_Thread)
    return(thread.url)

def reddit_scorebug(game):
    r = reddit_connect()
    thread = r.submission(id=game.Reddit_Thread)
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
    line1 = "    " + game.Away.Team_Abbr + ((5 - len(game.Away.Team_Abbr)) * " ") + str(game.A_Score) + ((7 - len(str(game.A_Score))) * " ") + second + "      " + inning + "\n"
    line2 = "    " + game.Home.Team_Abbr + ((5 - len(game.Home.Team_Abbr)) * " ") + str(game.H_Score) + ((5 - len(str(game.H_Score))) * " ") + third + "   " + first + "    " + out_text + "\n"
    msg = line1
    msg += line2
    msg += (f"On the mound: [{pitcher.Player_Name}](/u/{pitcher.User_ID.Reddit_Name})\n\n")
    msg += (f"Up to bat:    [{batter.Player_Name}](/u/{batter.User_ID.Reddit_Name})")
    comment = thread.reply(msg)
    comment.mod.lock()
    return(msg)

def reddit_resultbug(game,result_msg):
    r = reddit_connect()
    thread = r.submission(id=game.Reddit_Thread)
    thread.comment_sort = "new"
    pitch_line = (f"    Pitch:  {game.Pitch}\n")
    swing_line = (f"    Swing:  {game.Swing}\n")
    diff_line = (f"    Diff:   {ranges_calc.calc_diff(game.Pitch, game.Swing)}\n")
    result_line = (f"    Result: {result_msg[9]}\n")
    outs_line = (f"    Outs:   {game.Outs}\n")
    score_line = (f"    {game.Away.Team_Abbr} {game.A_Score} {game.Home.Team_Abbr} {game.H_Score}")
    msg = pitch_line + swing_line + diff_line + result_line + outs_line + score_line
    for comment in thread.comments: 
        if comment.is_submitter:
            reply_comment = comment
            break
    reply_comment.reply(msg)

def reddit_stealresultbug(game,result_msg):
    r = reddit_connect()
    thread = r.submission(id=game.Reddit_Thread)
    thread.comment_sort = "new"
    throw_line = (f"    Throw:  {game.C_Throw}\n")
    steal_line = (f"    Steal:  {game.R_Steal}\n")
    diff_line = (f"    Diff:   {ranges_calc.calc_diff(game.C_Throw, game.R_Steal)}\n")
    result_line = (f"    Result: {result_msg[9]}\n")
    outs_line = (f"    Outs:   {game.Outs}\n")
    score_line = (f"    {game.Away.Team_Abbr} {game.A_Score} {game.Home.Team_Abbr} {game.H_Score}")
    msg = throw_line + steal_line + diff_line + result_line + outs_line + score_line
    for comment in thread.comments: 
        if comment.is_submitter:
            reply_comment = comment
            break
    reply_comment.reply(msg)

def reddit_autoresultbug(game,result_msg):
    r = reddit_connect()
    thread = r.submission(id=game.Reddit_Thread)
    thread.comment_sort = "new"
    pitch_line = (f"    Pitch:  -\n")
    swing_line = (f"    Swing:  -\n")
    diff_line = (f"    Diff:   -\n")
    result_line = (f"    Result: {result_msg[9]}\n")
    outs_line = (f"    Outs:   {game.Outs}\n")
    score_line = (f"    {game.Away.Team_Abbr} {game.A_Score} {game.Home.Team_Abbr} {game.H_Score}")
    msg = pitch_line + swing_line + diff_line + result_line + outs_line + score_line
    for comment in thread.comments: 
        if comment.is_submitter:
            reply_comment = comment
            break
    reply_comment.reply(msg)

def create_gamethread(game,msg):
    r = reddit_connect()
    subreddit = r.subreddit('MajorLeagueGuessball')
    title = (f"The {game.Away.Team_Name} visit the {game.Home.Team_Name}")
    thread = subreddit.submit(title,selftext=msg)
    return(thread.id)

def edit_thread(thread_id,msg):
    r = reddit_connect()
    thread = r.submission(id=thread_id)
    thread.edit(msg)

def linescore_gen(game,game_pas):
    line1 = (f"## **{game.Away.Team_Name} {game.A_Score} - {game.H_Score} {game.Home.Team_Name}**\n\n")
    line2 = "|**TEAM**|**1**|**2**|**3**|**4**|**5**|**6**|"
    line3 = "|:-|:-|:-|:-|:-|:-|:-|:-|:-"
    inning_no = int(game.Inning[1:])
    if inning_no > 6:
        for inning in range(7,inning_no+1):
            extension = (f"**{inning}**|")
            line2 = line2 + extension
            line3 = line3 + "|:-"
    line2 = line2 + "**R**|**H**|\n"
    line3 = line3 + "|\n"
    line4 = (f"|**{game.Away.Team_Abbr}**|")
    line5 = (f"|**{game.Away.Team_Abbr}**|")
    for inning in range(1,inning_no+1):
        away_runs = 0
        home_runs = 0
        away_runs_q = game_pas.select(All_PAs.Runs_Scored_On_Play).where((All_PAs.Inning_No == inning) & (All_PAs.Off_Team == game.Away.Team_Abbr))
        home_runs_q = game_pas.select(All_PAs.Runs_Scored_On_Play).where((All_PAs.Inning_No == inning) & (All_PAs.Off_Team == game.Home.Team_Abbr))
        for row in away_runs_q:
            away_runs += row.Runs_Scored_On_Play
        for row in home_runs_q:
            home_runs += row.Runs_Scored_On_Play
        line4 = line4 + (f"{away_runs}|")
        line5 = line5 + (f"{home_runs}|")
    if inning_no < 6:
        extension = (6 - inning_no) * "|"
        line4 = line4 + extension
        line5 = line5 + extension
    line4 = line4 + (f"**{game.A_Score}**|**0**|\n")
    line5 = line5 + (f"**{game.H_Score}**|**0**|\n")
    game_line = line1 + line2 + line3 + line4 + line5 + "\n"
    return game_line

def playerscore_gen(game,lineups,game_pas,gamestats):
    line1 = "## **Box**\n"
    line2 = (f"|**#**|**{game.Away.Team_Abbr}**|**Pos**|**AB**|**R**|**H**|**RBI**|**BB**|**K**|**BA**|**#**|**{game.Home.Team_Abbr}**|**Pos**|**AB**|**R**|**H**|**RBI**|**BB**|**K**|**BA**|\n")
    line3 = "|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|\n"
    line4 = "## **Pitchers**\n"
    line5 = (f"|**{game.Away.Team_Abbr}**|**IP**|**H**|**ER**|**BB**|**K**|**ERA**|**{game.Home.Team_Abbr}**|**IP**|**H**|**ER**|**BB**|**K**|**ERA**|\n")
    line6 = "|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|\n"
    batter_lines = {}
    batter_lines[game.Away.Team_Abbr] = []
    batter_lines[game.Home.Team_Abbr] = []
    pitcher_lines = {}
    pitcher_lines[game.Away.Team_Abbr] = []
    pitcher_lines[game.Home.Team_Abbr] = []
    for entry in lineups:
        if entry.Position != 'P' and entry.Box != 0:
            status = boxscore_active(lineups,entry)
            if status == 'inactive':
                name = '~~' + entry.Player.Player_Name + '~~'
            else:
                name = entry.Player.Player_Name
            line = []
            line.extend([str(entry.Order),
                        name,
                        entry.Position,
                        str(gamestats[entry.Player.Player_ID]['Batting']['AB']),
                        str(gamestats[entry.Player.Player_ID]['Batting']['R']),
                        str(gamestats[entry.Player.Player_ID]['Batting']['H']),
                        str(gamestats[entry.Player.Player_ID]['Batting']['RBI']),
                        str(gamestats[entry.Player.Player_ID]['Batting']['BB']),
                        str(gamestats[entry.Player.Player_ID]['Batting']['K']),
                        str(gamestats[entry.Player.Player_ID]['Batting']['BA'])
                        ])
            joined = '|'.join(line)
            final = '|' + joined
            batter_lines[entry.Team.Team_Abbr].append(final)
        elif entry.Position == 'P' and entry.Box != 0:
            status = boxscore_active(lineups,entry)
            if status == 'inactive':
                name = '~~' + entry.Player.Player_Name + '~~'
            else:
                name = entry.Player.Player_Name
            line = []
            line.extend([name,
                        str(gamestats[entry.Player.Player_ID]['Pitching']['IP']),
                        str(gamestats[entry.Player.Player_ID]['Pitching']['H']),
                        str(gamestats[entry.Player.Player_ID]['Pitching']['ER']),
                        str(gamestats[entry.Player.Player_ID]['Pitching']['BB']),
                        str(gamestats[entry.Player.Player_ID]['Pitching']['K']),
                        str(gamestats[entry.Player.Player_ID]['Pitching']['ERA'])
                        ])
            joined = '|'.join(line)
            final = '|' + joined
            pitcher_lines[entry.Team.Team_Abbr].append(final)
    a_len = len(batter_lines[game.Away.Team_Abbr])
    h_len = len(batter_lines[game.Home.Team_Abbr])
    if a_len != h_len:
        diff = abs(a_len - h_len)
        if a_len > h_len:
            batter_lines[game.Home.Team_Abbr].extend(['|||||||||'] * diff)
        else:
            batter_lines[game.Away.Team_Abbr].extend(['|||||||||'] * diff)
    a_len = len(pitcher_lines[game.Away.Team_Abbr])
    h_len = len(pitcher_lines[game.Home.Team_Abbr])
    if a_len != h_len:
        diff = abs(a_len - h_len)
        if a_len > h_len:
            pitcher_lines[game.Home.Team_Abbr].extend(['|||||||'] * diff)
        else:
            pitcher_lines[game.Away.Team_Abbr].extend(['|||||||'] * diff)
    msg = line1 + line2 + line3
    for i in range(len(batter_lines[game.Away.Team_Abbr])):
        msg = msg + batter_lines[game.Away.Team_Abbr][i] + batter_lines[game.Home.Team_Abbr][i] + '\n'
    msg = msg + line4 + line5 + line6
    for i in range(len(pitcher_lines[game.Away.Team_Abbr])):
        msg = msg + pitcher_lines[game.Away.Team_Abbr][i] + pitcher_lines[game.Home.Team_Abbr][i] + '\n'
    return msg

def boxscore_active(lineups,entry):
    max_box = lineups.select(fn.MAX(Lineups.Box)).where((Lineups.Game_Number == entry.Game_Number.Game_Number) & (Lineups.Position == entry.Position) & (Lineups.Team == entry.Team.Team_Abbr)).scalar()
    if entry.Box == max_box: 
        status = 'active'
    else: 
        status = 'inactive'
    return status

def reddit_boxscore_gen(game,lineups,game_pas,gamestats):
    linescore = linescore_gen(game,game_pas)
    playerscore = playerscore_gen(game,lineups,game_pas,gamestats)
    boxscore = linescore + playerscore
    return boxscore