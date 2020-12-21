import deepdiff, json, asyncio
from peewee import *
from os import environ, path
from dotenv import load_dotenv
from api_models import *
from playhouse.shortcuts import model_to_dict


secret_path = basedir + '/shared/client_secret.json'


# Keys for zipping dicts for entering to database
all_pas_keys = ['Play_No','Inning','Outs','BRC','Play_Type','Pitcher','Pitch_No','Batter','Swing_No','Catcher','Throw_No','Runner','Steal_No','Result','Run_Scored','Ghost_Scored','RBIs','Stolen_Base','Diff','Runs_Scored_On_Play','Off_Team','Def_Team','Game_No','Session_No','Inning_No','Pitcher_ID','Batter_ID','Catcher_ID','Runner_ID']

persons_keys = ['PersonID','Current_Name','Stats_Name','Reddit','Discord','Discord_ID','Team','Player','Captain','GM','Retired','Hiatus','Rookie','Primary','Backup','Hand','CON','EYE','PWR','SPD','MOV','CMD','VEL','AWR']

teams_keys = ['TID','Abbr','Name','Stadium','League','Division','Logo_URL','Location','Mascot']

schedules_keys = ['Session','Game_No','Away','Home','Game_ID','A_Score','H_Score','Inning','Situation','Win','Loss','WP','LP','SV','POTG','Umpire','Reddit','Log','Duration','Total_Plays','Plays_Per_Day']

def access_sheets():
    gSheet = pygsheets.authorize(service_file=secret_path)
    global prev_pas_sh, s5_pas_sh, persons_sh, teams_sh, schedules_sh
    p_master_log = gSheet.open_by_key(environ.get('P_MASTER_LOG'))
    prev_pas_sh = p_master_log.worksheet_by_title("All_PAs_1-4")
    s5_pas_sh = p_master_log.worksheet_by_title("All_PAs_5")
    persons_sh = p_master_log.worksheet_by_title("Persons")
    teams_sh = p_master_log.worksheet_by_title("Teams")
    schedules_sh = p_master_log.worksheet_by_title("Schedule")

def build_plays_s5():
    pas = []
#    s5_pas_val = s5_pas_sh.get_values(start="A2",end="AC1920",include_tailing_empty_rows=False)
    s5_pas_val = s5_pas_sh.get_all_values(include_tailing_empty_rows=False)
    for p in s5_pas_val:
        pa = dict(zip(all_pas_keys,p))
        for cat in pa:
            if pa[cat] == '': pa[cat] = None
        pas.append(pa)
    with db.atomic():
        PAs.insert_many(pas).execute()

def build_plays_old():
    ranges = (("A2","AC5000"),("A5001","AC10000"),("A10001","AC15000"),("A15001","AC20000"),("A20001","AC22287"))
    for range in ranges:
        pas = []
        prev_pas_val = prev_pas_sh.get_values(start=range[0],end=range[1],include_tailing_empty_rows=False)
        for p in prev_pas_val:
            pa = dict(zip(all_pas_keys,p))
            for cat in pa:
                if pa[cat] == '': pa[cat] = None
            pas.append(pa)
    #    all_pas.pop(0)
        with db.atomic():
            PAs.insert_many(pas).execute()

def build_persons():
    defaults = { 'Reddit':None,
                 'Discord':None,
                 'Discord_ID':None,
                 'Team':'',
                 'Player':0,
                 'Captain':0,
                 'GM':0,
                 'Retired':0,
                 'Hiatus':0,
                 'Rookie':0,
                 'Primary':'',
                 'Backup':'',
                 'Hand':'R',
                 'CON':0,
                 'EYE':0,
                 'PWR':0,
                 'SPD':0,
                 'MOV':0,
                 'CMD':0,
                 'VEL':0,
                 'AWR':0
               }
    persons = []
    persons_data = persons_sh.get_all_values(include_tailing_empty_rows=False)
    for p in persons_data:
        person = dict(zip(persons_keys,p))
        for cat in person:
            if person[cat] == '' or person[cat] == 'N': person[cat] = defaults[cat]
        persons.append(person)
    persons.pop(0) #header row
    ref_person = []
    for person in persons:
        if person['Discord_ID'] == '202278109708419072': ref_person.append(person)
    try:
        assert len(ref_person) == 1
        assert ref_person[0]['PersonID'] == '2069'
        assert ref_person[0]['Stats_Name'] == 'Tygen Shinybeard'
        return(persons)
    except AssertionError:
        return(None)

def build_teams():
    teams = []
    teams_data = teams_sh.get_all_values(include_tailing_empty_rows=False)
    for t in teams_data:
        team = dict(zip(teams_keys,t))
        teams.append(team)
    teams.pop(0)
    ref_team = []
    for team in teams:
        if team['TID'] == 'T2001': ref_team.append(team)
    try:
        assert len(ref_team) == 1
        assert ref_team[0]['Abbr'] == 'POR'
        return(teams)
    except AssertionError:
        return(None)

def build_schedules():
    schedules = []
    schedules_data = schedules_sh.get_all_values(include_tailing_empty_rows=False)
    for s in schedules_data:
        schedule = dict(zip(schedules_keys,s))
        if schedule['Session'] != 'Session':
            if int(schedule['Session']) != 0 and int(schedule['Session']) < 15:
                for entry in schedule:
                    if schedule[entry] == '':
                        schedule[entry] = None
                schedules.append(schedule)
    ref_sched = []
    for sched in schedules:
        if sched['Game_No'] == '50101': ref_sched.append(sched)
    try:
        assert len(ref_sched) == 1
        assert ref_sched[0]['Game_ID'] == 'GRZACP1'
        return(schedules)
    except AssertionError:
        return(None)

def update_pas():
    pas_list = s5_pas_sh.get_all_values(include_tailing_empty_rows=False)
    cur_session = pas_list[-1][0][0:3]
    int_list = ['Play_No','Outs','BRC','Pitch_No','Swing_No','Throw_No','Steal_No','Run_Scored','Ghost_Scored','RBIs','Stolen_Base','Diff','Runs_Scored_On_Play','Game_No','Session_No','Inning_No','Pitcher_ID','Batter_ID','Catcher_ID','Runner_ID']
    for i in pas_list:
        if i[0].startswith(cur_session):
            sheet_pa_dict = dict(zip(all_pas_keys,i))
            for cat in sheet_pa_dict: 
                if sheet_pa_dict[cat] == '': sheet_pa_dict[cat] = None
                elif cat in int_list: sheet_pa_dict[cat] = int(sheet_pa_dict[cat])
            pa, created = PAs.get_or_create(Play_No=i[0],defaults=sheet_pa_dict)
            if not created:
                diff = deepdiff.DeepDiff(pa.sheets_compare_int(),sheet_pa_dict)
                if bool(diff):
                    changed = {}
                    print(diff)
                    for diff_type in ['values_changed','type_changes']:
                        if diff_type in diff:
                            for val in diff[diff_type]: changed[val[6:-2]] = diff[diff_type][val]['new_value']
                    PAs.update(changed).where(PAs.Play_No == pa.Play_No).execute()

def generate_db():
    access_sheets()
    db.connect(reuse_if_open=True)
    db.drop_tables([PAs])
    db.create_tables([PAs])
    build_plays_old()
    build_plays_s5()
    persons = build_persons()
    teams = build_teams()
    schedules = build_schedules()
    with db.atomic():
        if persons and teams and schedules:
            db.drop_tables([Persons,Teams,Schedules])
            db.create_tables([Persons,Teams,Schedules])
            Persons.insert_many(persons).execute()
            Teams.insert_many(teams).execute()
            Schedules.insert_many(schedules).execute()
        update_pas()
    db.close()

async def main():
    access_sheets()
    while True:
        persons = build_persons()
        teams = build_teams()
        schedules = build_schedules()
        db.connect(reuse_if_open=True)
        with db.atomic():
            if persons and teams and schedules:
                db.drop_tables([Persons,Teams,Schedules])
                db.create_tables([Persons,Teams,Schedules])
                Persons.insert_many(persons).execute()
                Teams.insert_many(teams).execute()
                Schedules.insert_many(schedules).execute()
            update_pas()
        db.close()
        await asyncio.sleep(60*15)

if __name__ == "__main__":
    generate_db()
#    asyncio.run(main())
