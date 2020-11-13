from peewee import *
from playhouse.pool import PooledSqliteExtDatabase
from playhouse.migrate import *
from wtfpeewee.orm import model_form
import wtforms, os, inspect, csv, json, pygsheets, time, connexion
#from flask_marshmallow import Marshmallow
from os import environ, path
from dotenv import load_dotenv
from flask_wtf import FlaskForm
from wtforms import Form, FieldList, FormField, SelectField, HiddenField, validators
from marshmallow_peewee import ModelSchema

basedir = path.abspath(path.dirname(path.dirname(__file__)))
load_dotenv(path.join(basedir, '.env'))

#connex_app = connexion.App(__name__, specification_dir=basedir)
#app = connex_app.app
#ma = Marshmallow(app)

# Builds absolute path relative to this models.py file so other directories (like bots) can find the same database when importing
db_path = path.join(basedir+'/shared/','mlg_api.s')
db = PooledSqliteExtDatabase(db_path, check_same_thread=False, pragmas={'foreign_keys': 1},max_connections=30,stale_timeout=500)

# Access Google Sheets for updates
secret_path = basedir + '/shared/client_secret.json'
gSheet = pygsheets.authorize(service_file=secret_path)
p_master_log = gSheet.open_by_key(environ.get('P_MASTER_LOG'))
prev_pas_sh = p_master_log.worksheet_by_title("All_PAs_1-4")
s5_pas_sh = p_master_log.worksheet_by_title("All_PAs_5")
persons_sh = p_master_log.worksheet_by_title("Persons")
teams_sh = p_master_log.worksheet_by_title("Teams")
schedules_sh = p_master_log.worksheet_by_title("Schedule")
#test_sh = p_master_log.worksheet_by_title("Test")

# Keys for zipping dicts for entering to database
all_pas_keys = ['Play_No','Inning','Outs','BRC','Play_Type','Pitcher','Pitch_No','Batter','Swing_No','Catcher','Throw_No','Runner','Steal_No','Result','Run_Scored','Ghost_Scored','RBIs','Stolen_Base','Diff','Runs_Scored_On_Play','Off_Team','Def_Team','Game_No','Session_No','Inning_No','Pitcher_ID','Batter_ID','Catcher_ID','Runner_ID']

persons_keys = ['PersonID','Current_Name','Stats_Name','Reddit','Discord','Discord_ID','Team','Player','Captain','GM','Retired','Hiatus','Rookie','Primary','Backup','Hand','CON','EYE','PWR','SPD','MOV','CMD','VEL','AWR']

teams_keys = ['TID','Abbr','Name','Stadium','League','Division','Logo_URL','Location','Mascot']

schedules_keys = ['Session','Game_No','Away','Home','Game_ID','A_Score','H_Score','Inning','Situation','Win','Loss','WP','LP','SV','POTG','Umpire','Reddit','Log','Duration','Total_Plays','Plays_Per_Day']

class BaseModel(Model):
    class Meta:
        database = db

class Teams(BaseModel):
    id = AutoField(primary_key=True)
    TID = CharField(unique=True)
    Abbr = CharField(unique=True)
    Name = CharField(unique=True)
    Stadium = CharField()
    League = CharField()
    Division = CharField()
    Logo_URL = CharField()
    Location = CharField()
    Mascot = CharField()

class Persons(BaseModel):
    id = AutoField(primary_key=True)
    PersonID = IntegerField(unique=True)
    Current_Name = CharField()
    Stats_Name = CharField(unique=True)
    Reddit = CharField(default='',null=True)
    Discord = CharField()
    Discord_ID = CharField(null=True)
    Team = CharField(default='')
    Player = BooleanField(default=True)
    Captain = BooleanField(default=False)
    GM = BooleanField(default=False)
    Retired = BooleanField(default=False)
    Hiatus = BooleanField(default=False)
    Rookie = BooleanField(default=False)
    Primary = CharField(null=True,default=None)
    Backup = CharField(null=True)
    Hand = CharField()
    CON = IntegerField(default=0)
    EYE = IntegerField(default=0)
    PWR = IntegerField(default=0)
    SPD = IntegerField(default=0)
    MOV = IntegerField(default=0)
    CMD = IntegerField(default=0)
    VEL = IntegerField(default=0)
    AWR = IntegerField(default=0)

class PersonsSchema(ModelSchema):
    class Meta:
        model = Persons
        dump_only_pk = False
        string_keys = False

class Schedules(BaseModel):
    id = AutoField(primary_key=True)
    Session = IntegerField()
    Game_No = IntegerField(unique=True)
    Away = ForeignKeyField(Teams,field='Abbr')
    Home = ForeignKeyField(Teams,field='Abbr')
    Game_ID = CharField()
    A_Score = IntegerField(null=True)
    H_Score = IntegerField(null=True)
    Inning = CharField(null=True)
    Situation = CharField(null=True)
    Win = ForeignKeyField(Teams,field='Abbr',null=True)
    Loss = ForeignKeyField(Teams,field='Abbr',null=True)
    WP = ForeignKeyField(Persons,field='Stats_Name',null=True)
    LP = ForeignKeyField(Persons,field='Stats_Name',null=True)
    SV = ForeignKeyField(Persons,field='Stats_Name',null=True)
#    POTG = ForeignKeyField(Persons,field='Stats_Name',null=True)
    POTG = CharField(null=True)
    Umpire = CharField(null=True)
    Reddit = CharField(null=True)
    Log = CharField(null=True)
    Duration = FloatField(null=True)
    Total_Plays = IntegerField(null=True)
    Plays_Per_Day = FloatField(null=True)

class SchedulesSchema(ModelSchema):
    class Meta:
        model = Schedules

def build_plays_s5():
    db.connect(reuse_if_open=True)
    pas = []
    s5_pas_val = s5_pas_sh.get_values(start="A2",end="AC106",include_tailing_empty_rows=False)
    for p in s5_pas_val:
        pa = dict(zip(all_pas_keys,p))
        pas.append(pa)
    with db.atomic():
        PAs.insert_many(pas).execute()
    db.close()

def build_plays_old():
    db.connect(reuse_if_open=True)
    db.drop_tables([PAs])
    db.create_tables([PAs])
    ranges = (("A2","AC5000"),("A5001","AC10000"),("A10001","AC15000"),("A15001","AC20000"),("A20001","AC22287"))
    for range in ranges:
        pas = []
        prev_pas_val = prev_pas_sh.get_values(start=range[0],end=range[1],include_tailing_empty_rows=False)
        for p in prev_pas_val:
            pa = dict(zip(all_pas_keys,p))
            pas.append(pa)
    #    all_pas.pop(0)
        with db.atomic():
            PAs.insert_many(pas).execute()
    db.close()

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
    db.connect(reuse_if_open=True)
    db.drop_tables([Persons,Teams,Schedules])
    db.create_tables([Persons])
    persons = []
    persons_data = persons_sh.get_all_values(include_tailing_empty_rows=False)
    for p in persons_data:
        person = dict(zip(persons_keys,p))
        for cat in person:
            if person[cat] == '' or person[cat] == 'N': person[cat] = defaults[cat]
        persons.append(person)
    persons.pop(0) #header row
    with db.atomic():
        Persons.insert_many(persons).execute()
    db.close()

def build_teams():
    db.connect(reuse_if_open=True)
    db.drop_tables([Teams])
    db.create_tables([Teams])
    teams = []
    teams_data = teams_sh.get_all_values(include_tailing_empty_rows=False)
    for t in teams_data:
        team = dict(zip(teams_keys,t))
        teams.append(team)
    teams.pop(0)
    with db.atomic():
        Teams.insert_many(teams).execute()

def build_schedules():
    db.connect(reuse_if_open=True)
    db.drop_tables([Schedules])
    db.create_tables([Schedules])
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
#    schedules.pop(0)
    with db.atomic():
        Schedules.insert_many(schedules).execute()

def main():
    build_persons()
    build_teams()
    build_schedules()

if __name__ == "__main__":
    main()