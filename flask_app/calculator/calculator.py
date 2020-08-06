import random, time, sys, json, os
from decimal import Decimal
from os import path
from flask import current_app as app
import calculator.ranges_files.ranges_calc as ranges_calc
import calculator.ranges_files.ranges_lookup as ranges_lookup
import webhook_functions as webhook_functions
from calculator.ranges_files.play_outcomes import play_outcomes
from MLG_reddit.sender import reddit_scorebug, reddit_resultbug, reddit_stealresultbug, reddit_boxscore_gen, edit_thread
from games import games
from peewee import *
from models import *

def play_check(game):
    if game.C_Throw and game.R_Steal:
        brc = ranges_calc.brc_calc(game)
        result,runner = resulting_steal(game)
        lookup_play = (f"{str(brc)}_{str(game.Outs)}_{result}")
        new_outcome = {}
        if play_outcomes[lookup_play][0] not in ["", "0", "b4"]:
            new_outcome[play_outcomes[lookup_play][0]] = game.Batter
        if play_outcomes[lookup_play][1] not in ["", "0", "b4"]:
            new_outcome[play_outcomes[lookup_play][1]] = game.First_Base
        if play_outcomes[lookup_play][2] not in ["", "0", "b4"]:
            new_outcome[play_outcomes[lookup_play][2]] = game.Second_Base
        if play_outcomes[lookup_play][3] not in ["", "0", "b4"]:
            new_outcome[play_outcomes[lookup_play][3]] = game.Third_Base
        result_msg = [game.Inning, game.Outs, brc, "Steal", game.Catcher.Player_Name,
                      runner.Player_Name, game.C_Throw, game.R_Steal, result]
        runs_scored = 0
        outs = 0
        index_base_map = {0:game.Batter,1:game.First_Base,2:game.Second_Base,3:game.Third_Base}
        runners_scored = []
        with db.atomic():
            for base,outcome in enumerate(play_outcomes[lookup_play][0:4]):
                if outcome == 'b4':
                    runners_scored.append(index_base_map[base])
                    runs_scored += 1
                    if game.Inning[0] == 'T':
                        game.A_Score += 1
                    else:
                        game.H_Score += 1
                elif outcome == '0':
                    outs += 1
                    game.Outs += 1
            game.save()
        result_msg.append(runs_scored)
        msg = steal_result_bug(game,result_msg)
        reddit_stealresultbug(game,result_msg)
        webhook_functions.steal_result(game,runner,msg)
        scorebook_line = save_play_result(game,result_msg,runs_scored,outs,result,runners_scored,runner)
        next_PA(game,new_outcome)
        return([result_msg,msg])
    elif game.Pitch and game.Swing and game.Runner == None:
        brc = ranges_calc.brc_calc(game)
        result = resulting_swing(game)
        lookup_play = (f"{str(brc)}_{str(game.Outs)}_{result}")
        new_outcome = {}
        if play_outcomes[lookup_play][0] not in ["", "0", "b4"]:
            new_outcome[play_outcomes[lookup_play][0]] = game.Batter
        if play_outcomes[lookup_play][1] not in ["", "0", "b4"]:
            new_outcome[play_outcomes[lookup_play][1]] = game.First_Base
        if play_outcomes[lookup_play][2] not in ["", "0", "b4"]:
            new_outcome[play_outcomes[lookup_play][2]] = game.Second_Base
        if play_outcomes[lookup_play][3] not in ["", "0", "b4"]:
            new_outcome[play_outcomes[lookup_play][3]] = game.Third_Base
        result_msg = [game.Inning, game.Outs, brc, "Swing", game.Pitcher.Player_Name,
                      game.Batter.Player_Name, game.Pitch, game.Swing, result]
        runs_scored = 0
        outs = 0
        index_base_map = {0:game.Batter,1:game.First_Base,2:game.Second_Base,3:game.Third_Base}
        runners_scored = []
        with db.atomic():
            for base,outcome in enumerate(play_outcomes[lookup_play][0:4]):
                if outcome == 'b4':
                    runners_scored.append(index_base_map[base])
                    runs_scored += 1
                    if game.Inning[0] == 'T':
                        game.A_Score += 1
                    else:
                        game.H_Score += 1
                elif outcome == '0':
                    outs += 1
                    game.Outs += 1
            game.save()
        result_msg.append(runs_scored)
        msg = swing_result_bug(game,result_msg)
        reddit_resultbug(game,result_msg)
        webhook_functions.swing_result(game,msg)
        scorebook_line = save_play_result(game,result_msg,runs_scored,outs,result,runners_scored)
        next_PA(game,new_outcome)
        return([result_msg,msg])
    else:
        return([['','','','',game.Pitch,game.Swing,type(game.Runner)]])

def save_play_result(game,result_msg,runs_scored,outs,result,runners_scored,runner=None):
    data = {}
    last_play = All_PAs.select(fn.MAX(All_PAs.Play_No)).where(All_PAs.Play_No ** (str(game.Game_Number)+"%")).scalar()
    rbi_plays = ['HR','3B','2B','1B','IF1B','1BWH','1BWH2','2BWH','BB','DFO','DSacF','SacF']
    try:
        data['Play_No'] = last_play+1
    except:
        data['Play_No'] = str(game.Game_Number)+'001'
    data['Inning'] = result_msg[0]
    data['Outs'] = result_msg[1]
    data['BRC'] = result_msg[2]
    data['Play_Type'] = result_msg[3]
    if data['Play_Type'] == 'Swing':
        data['Pitcher'] = result_msg[4]
        data['Pitch_No'] = result_msg[6]
        data['Batter'] = result_msg[5]
        data['Swing_No'] = result_msg[7]
        data['Diff'] = ranges_calc.calc_diff(game.Pitch,game.Swing)
        data['Pitcher_ID'] = game.Pitcher.Player_ID
        data['Batter_ID'] = game.Batter.Player_ID
    elif data['Play_Type'] == 'Steal':
        data['Catcher'] = result_msg[4]
        data['Throw_No'] = result_msg[6]
        data['Runner'] = result_msg[5]
        data['Steal_No'] = result_msg[7]
        data['Diff'] = ranges_calc.calc_diff(game.C_Throw,game.R_Steal)
        data['Pitcher_ID'] = game.Pitcher.Player_ID
        data['Catcher_ID'] = game.Catcher.Player_ID
        data['Runner_ID'] = runner.Player_ID
    if result == 'HR' or result == 'SB4':
        data['Run_Scored'] = 1
    if result in rbi_plays:
        data['RBIs'] = runs_scored
    else:
        data['RBIs'] = 0
    data['Runs_Scored_On_Play'] = runs_scored
    data['Result'] = result
    if data['Inning'][0] == "T":
        data['Off_Team'] = game.Away.Team_Abbr
        data['Def_Team'] = game.Home.Team_Abbr
    else:
        data['Off_Team'] = game.Home.Team_Abbr
        data['Def_Team'] = game.Away.Team_Abbr
    data['Game_No'] = game.Game_Number
    data['Session_No'] = game.Session
    data['Inning_No'] = game.Inning[1:]
    with db.atomic():
        All_PAs.insert(data).execute()
        for r_scored in runners_scored:
            All_PAs.update(Run_Scored = 1).where((All_PAs.Batter_ID == r_scored.Player_ID) & (All_PAs.Play_Type == 'Swing')).order_by(All_PAs.Play_No.desc()).limit(1).execute()
    return data

def next_PA(game,new_outcome=None):
    steal,frame = None,None
    with db.atomic():
        lineup_size = int(app.config['LINEUP_SIZE'])
#        lineup_size = 4
        try:
            game.First_Base = new_outcome['first_base']
        except:
            game.First_Base = None
        try:
            game.Second_Base = new_outcome['second_base']
        except:
            game.Second_Base = None
        try:
            game.Third_Base = new_outcome['third_base']
        except:
            game.Third_Base = None
        if game.R_Steal:
            steal = True
            game.C_Throw = None
            game.R_Steal = None
            game.Runner = None
        else:
            if game.Inning[0] == 'T':
                if game.A_Bat_Pos == lineup_size:
                    game.A_Bat_Pos = 1
                else:
                    game.A_Bat_Pos += 1
            else:
                if game.H_Bat_Pos == lineup_size:
                    game.H_Bat_Pos = 1
                else:
                    game.H_Bat_Pos += 1
            game.Pitch = None
            game.Swing = None
        if game.Outs == 3:
            game.Outs = 0
            if game.Inning[0] == 'T':
                frame = 'B'
                inning_no = int(game.Inning[1:])
            else:
                frame = 'T'
                inning_no = int(game.Inning[1:]) + 1
            game.Inning = frame + str(inning_no)
            game.Pitch = None
            game.Swing = None
        game.save()
        active_players(game)
    if frame or not steal:
        msg = reddit_scorebug(game)
    lineups = Lineups.select().where(Lineups.Game_Number == game.Game_Number).order_by(Lineups.Team, Lineups.Order.asc(), Lineups.Box.asc())
    game_pas = All_PAs.select().where(All_PAs.Game_No == game.Game_Number).order_by(All_PAs.Play_No.desc())
    gamestats = games.stat_generator(game,lineups,game_pas)
    boxscore = reddit_boxscore_gen(game,lineups,game_pas,gamestats)
    edit_thread(game.Reddit_Thread,boxscore)
    webhook_functions.next_PA(game)

# Pulls currently active players in a given game based upon inning (T or B), then saves them in the gamestate
def active_players(game):
    if game.Inning[0] == 'T':
        off_team = game.Away.Team_Abbr
        def_team = game.Home.Team_Abbr
        bat_pos = game.A_Bat_Pos
    else:
        off_team = game.Home.Team_Abbr
        def_team = game.Away.Team_Abbr
        bat_pos = game.H_Bat_Pos
    with db.atomic():
        max_p_box = (Lineups
         .select(fn.MAX(Lineups.Box))
         .where((Lineups.Game_Number == game.Game_Number) & 
                (Lineups.Team == def_team) & 
                (Lineups.Position == 'P')
                )).scalar()
        max_c_box = (Lineups
         .select(fn.MAX(Lineups.Box))
         .where((Lineups.Game_Number == game.Game_Number) & 
                (Lineups.Team == def_team) & 
                (Lineups.Position == 'C')
                )).scalar()
        max_b_box = (Lineups
         .select(fn.MAX(Lineups.Box))
         .where((Lineups.Game_Number == game.Game_Number) & 
                (Lineups.Team == off_team) & 
                (Lineups.Order == bat_pos)
                )).scalar()
        pitcher = (Lineups
         .select(Lineups,Players,Games).join(Games).switch(Lineups).join(Players)
         .where((Lineups.Game_Number == game.Game_Number) & 
                (Lineups.Team == def_team) & 
                (Lineups.Position == 'P') & 
                (Lineups.Box == max_p_box)
                )).objects()[0]
        catcher = (Lineups
         .select(Lineups,Players,Games).join(Games).switch(Lineups).join(Players)
         .where((Lineups.Game_Number == game.Game_Number) & 
                (Lineups.Team == def_team) & 
                (Lineups.Position == 'C') & 
                (Lineups.Box == max_c_box)
                )).objects()[0]
        batter = (Lineups
         .select(Lineups,Players,Games).join(Games).switch(Lineups).join(Players)
         .where((Lineups.Game_Number == game.Game_Number) & 
                (Lineups.Team == off_team) & 
                (Lineups.Order == bat_pos) & 
                (Lineups.Box == max_b_box)
                )).objects()[0]
        game.Pitcher = pitcher.Player_ID
        game.Catcher = catcher.Player_ID
        game.Batter = batter.Player_ID
        game.save()

def resulting_steal(game):
    diff = ranges_calc.calc_diff(game.C_Throw,game.R_Steal)
    result,runner = ranges_calc.calc_steal(game,ranges_lookup.steal_dict,diff)
    return(result,runner)

def resulting_swing(game):
    handedness = ranges_calc.calc_handedness(game.Pitcher,game.Batter)
    ranges = ranges_calc.calc_ranges(ranges_lookup.obr_dict, ranges_lookup.modifiers_dict, game.Pitcher,
                                    game.Batter, handedness)
    if game.Outs != 2 and (game.First_Base != None or game.Second_Base != None):
        ranges, obr_ordering = ranges_calc.wh_calc(game, ranges)
    else:
        obr_ordering = ['HR', '3B', '2B', '1B', 'IF1B', 'BB']
    ranges = ranges_calc.go_calc(game, ranges, ranges_lookup.go_order_dict)
    if game.Outs != 2 and (game.Second_Base != None or game.Third_Base != None):
        ranges, fo_ordering = ranges_calc.dfo_calc(game, ranges)
    else:
        fo_ordering = ['FO']
    brc = ranges_calc.brc_calc(game)
    outs_ordering = ranges_lookup.go_order_dict[str(brc) + '_' + str(game.Outs)]
    all_order = obr_ordering + fo_ordering + outs_ordering
    result_list = []
    for result in all_order:
        for _ in range(ranges[result]):
            result_list.append(result)
    diff = ranges_calc.calc_diff(game.Pitch,game.Swing)
    try:
        result = result_list[diff]
    except:
        if game.First_Base != None:
            firstb = game.First_Base.Player_Name
        else:
            firstb = None
        if game.Second_Base != None:
            secondb = game.Second_Base.Player_Name
        else:
            secondb = None
        if game.Third_Base != None:
            thirdb = game.Third_Base.Player_Name
        else:
            thirdb = None
        print(game.Outs, game.Pitcher.Player_Name, game.Batter.Player_Name, firstb, secondb, thirdb, ranges)
    return result

def steal_result_bug(game,result_msg):
    throw_line = (f"Throw:  {game.C_Throw}\n")
    steal_line = (f"Steal:  {game.R_Steal}\n")
    diff_line = (f"Diff:   {ranges_calc.calc_diff(game.C_Throw, game.R_Steal)}\n")
    result_line = (f"Result: {result_msg[8]}\n")
    outs_line = (f"Outs:   {game.Outs}\n")
    score_line = (f"{game.Away.Team_Abbr} {game.A_Score} {game.Home.Team_Abbr} {game.H_Score}")
    msg = "```" + throw_line + steal_line + diff_line + result_line + outs_line + score_line + "```"
    return msg

def swing_result_bug(game,result_msg):
    pitch_line = (f"Pitch:  {game.Pitch}\n")
    swing_line = (f"Swing:  {game.Swing}\n")
    diff_line = (f"Diff:   {ranges_calc.calc_diff(game.Pitch, game.Swing)}\n")
    result_line = (f"Result: {result_msg[8]}\n")
    outs_line = (f"Outs:   {game.Outs}\n")
    score_line = (f"{game.Away.Team_Abbr} {game.A_Score} {game.Home.Team_Abbr} {game.H_Score}")
    msg = "```" + pitch_line + swing_line + diff_line + result_line + outs_line + score_line + "```"
    return msg