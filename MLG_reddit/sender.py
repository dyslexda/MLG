import praw, random
from os import environ, path
from dotenv import load_dotenv
from models import All_PAs,Lineups
from peewee import *

basedir = path.dirname(path.abspath(path.dirname(__file__)))
load_dotenv(path.join(basedir, '.env'))

r = praw.Reddit(client_id = environ.get('CLIENT_ID'),
                client_secret = environ.get('CLIENT_SECRET'),
                redirect_uri = environ.get('REDIRECT_URI'),
                user_agent = environ.get('USER_AGENT'),
                username = environ.get('USERNAME'),
                password = environ.get('PASSWORD'))

#state = str(random.randint(0, 65000))
#url = r.auth.url(["*"], state, "permanent")
#print(url)

#target_sub = 'MajorLeagueGuessball'
#subreddit = r.subreddit(target_sub)
#
##thread = subreddit.submit("Test post, please ignore2",selftext="This is a test post")
#thread = r.submission(id='i32ir4')
#thread.edit("this is edited text")
#print(thread.selftext)

def edit_thread(thread_id,msg):
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

def boxscore_gen(game,lineups,game_pas,gamestats):
    line1 = "## **Box**\n"
    line2 = (f"|**#**|**{game.Away.Team_Abbr}**|**Pos**|**AB**|**R**|**H**|**RBI**|**BB**|**K**|**BA**|**#**|**{game.Home.Team_Abbr}**|**Pos**|**AB**|**R**|**H**|**RBI**|**BB**|**K**|**BA**|\n")
    line3 = "|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|:-|\n"
    player_lines = {}
    player_lines[game.Away.Team_Abbr] = []
    player_lines[game.Home.Team_Abbr] = []
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
            final = '|' + joined + '|'
            player_lines[entry.Team.Team_Abbr].append(final)
    a_len = len(player_lines[game.Away.Team.Team_Abbr])
    return(player_lines)

def boxscore_active(lineups,entry):
    max_box = lineups.select(fn.MAX(Lineups.Box)).where((Lineups.Game_Number == entry.Game_Number.Game_Number) & (Lineups.Position == entry.Position) & (Lineups.Team == entry.Team.Team_Abbr)).scalar()
    if entry.Box == max_box: 
        status = 'active'
    else: 
        status = 'inactive'
    return status

def reddit_boxscore_gen(game,lineups,game_pas,gamestats):
    linescore = linescore_gen(game,game_pas)
    boxscore = boxscore_gen(game,lineups,game_pas,gamestats)
    print(boxscore)
    return linescore