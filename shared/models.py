from peewee import *
from playhouse.pool import PooledSqliteExtDatabase
from playhouse.migrate import *
from wtfpeewee.orm import model_form
import wtforms, os, inspect, csv, json, pygsheets, time
from os import environ, path
from dotenv import load_dotenv
from flask_wtf import FlaskForm
from wtforms import Form, FieldList, FormField, SelectField, HiddenField, validators

basedir = path.abspath(path.dirname(path.dirname(__file__)))
load_dotenv(path.join(basedir, '.env'))

# Builds absolute path relative to this models.py file so other directories (like bots) can find the same database when importing
db_path = path.join(basedir+'/shared/','mlg.s')
db = PooledSqliteExtDatabase(db_path, check_same_thread=False, pragmas={'foreign_keys': 1},max_connections=30,stale_timeout=500)

# Access Google Sheets for updates
secret_path = basedir + '/shared/client_secret.json'
gSheet = pygsheets.authorize(service_file=secret_path)
p_master_log = gSheet.open_by_key(environ.get('P_MASTER_LOG'))
prev_pas_sh = p_master_log.worksheet_by_title("All_PAs_1-4")
s5_pas_sh = p_master_log.worksheet_by_title("All_PAs_5")
persons_sh = p_master_log.worksheet_by_title("Persons")
#test_sh = p_master_log.worksheet_by_title("Test")

def main():
    while True:
        s5_plays = s5_pas_sh.get_values(start="A100",end="AC106",include_tailing_empty_rows=False)
        for play in s5_plays:
            p_dict = dict(zip(all_pas_keys,play))
            play_record, created = PAs.get_or_create(Play_No=play[0],defaults=p_dict)
            if not created:
                got = PAs.get(PAs.Play_No==play[0])
                got_dict = got.__data__
                got_dict.pop('id')
                for i in got_dict:
                    print(i,got_dict[i] == p_dict[i],got_dict[i],p_dict[i])
#                print(got_dict,p_dict)
#            except:
#                print(play[0])
        time.sleep(10)

class ListField(Field):
    field_type = 'list'

    def db_value(self,value):
        return json.dumps(value)

    def python_value(self,value):
        return json.loads(value)

class BaseModel(Model):
    class Meta:
        database = db

class Users(BaseModel):
    id = AutoField(primary_key=True)
    Reddit_Name = CharField(unique=True)
    Discord_Name = CharField(null=True)
    Discord_ID = CharField(null=True)
    Player = BooleanField(default=True)
    Umpire = BooleanField(default=False)
    Commissioner = BooleanField(default=False)
#    Roles = CharField(default='Player')

class Teams(BaseModel):
    id = AutoField(primary_key=True)
    Team_Name = CharField(unique=True)
    Team_Abbr = CharField(unique=True)

class Players(BaseModel):
    id = AutoField(primary_key=True)
    User_ID = ForeignKeyField(Users,backref='uid')
    Player_ID = IntegerField(unique=True)
    Player_Name = CharField()
    PPos = CharField()
    SPos = CharField(null=True)
    Hand = CharField()
    Team = ForeignKeyField(Teams,field='Team_Abbr',null=True)
    Contact = IntegerField(default=0)
    Eye  = IntegerField(default=0)
    Power = IntegerField(default=0)
    Speed = IntegerField(default=0)
    Movement = IntegerField(default=0)
    Command = IntegerField(default=0)
    Velocity = IntegerField(default=0)
    Awareness = IntegerField(default=0)

class Games(BaseModel):
    id = AutoField(primary_key=True)
    Game_Number = IntegerField(unique=True)
    Game_ID = CharField()
    Status = CharField(default='Staged') # 'Staged' is created; 'Init' means lineups are populated; 'Started' has been started, and sent messages to players; 'Paused' means timers don't progress; 'Final' means game has ended.
    Step = IntegerField(default=1) # Step 1 is pinging players; step 2 is reviewing and processing results, step 3 is ending the PA and routing back to step 1 or 2, and step 4 is game over
    Ump_Mode = CharField(default='Manual') # 'Manual' or 'Automatic' to determine how game progresses
    Umpires = ListField(null=True)
    Season = IntegerField(null=True)
    Session = IntegerField(null=True)
    Away = ForeignKeyField(Teams,field='Team_Abbr',null=True)
    Home = ForeignKeyField(Teams,field='Team_Abbr',null=True)
    A_Score = IntegerField(default=0)
    H_Score = IntegerField(default=0)
    A_Bat_Pos = IntegerField(default=1)
    H_Bat_Pos = IntegerField(default=1)
    Inning = CharField(default='T1')
    Outs = IntegerField(default=0)
    Situation = CharField(null=True)
    Pitcher = ForeignKeyField(Players,field='Player_ID',null=True)
    Batter = ForeignKeyField(Players,field='Player_ID',null=True)
    Catcher = ForeignKeyField(Players,field='Player_ID',null=True)
    First_Base = ForeignKeyField(Players,field='Player_ID',null=True)
    Second_Base = ForeignKeyField(Players,field='Player_ID',null=True)
    Third_Base = ForeignKeyField(Players,field='Player_ID',null=True)
    Runner = IntegerField(null=True)
    PA_Timer = TimestampField(utc=True,default=None,null=True)
    Steal_Timer = TimestampField(utc=True,default=None,null=True)
    Pitch = IntegerField(null=True)
    Swing = IntegerField(null=True)
    C_Throw = IntegerField(null=True)
    R_Steal = IntegerField(null=True)
    Bunt = BooleanField(default=False)
    Infield_In = BooleanField(default=False)
    Ump_Flavor = TextField(null=True)
    B_Flavor = TextField(null=True)
    P_Flavor = TextField(null=True)
    Win = ForeignKeyField(Teams,field='Team_Abbr',null=True)
    Loss = ForeignKeyField(Teams,field='Team_Abbr',null=True)
    WP = ForeignKeyField(Players,field='Player_ID',null=True)
    LP = ForeignKeyField(Players,field='Player_ID',null=True)
    SV = ForeignKeyField(Players,field='Player_ID',null=True)
    POTG = ForeignKeyField(Players,field='Player_ID',null=True)
    HM1 = ForeignKeyField(Players,field='Player_ID',null=True)
    HM2 = ForeignKeyField(Players,field='Player_ID',null=True)
    HM3 = ForeignKeyField(Players,field='Player_ID',null=True)
    Reddit_Thread = CharField(null=True)
    Notes = CharField(null=True)

class Umpires(BaseModel):
    id = AutoField(primary_key=True)
    Crew_Name = CharField()
    Ump1 = ForeignKeyField(Users)
    Ump2 = ForeignKeyField(Users,null=True)
    Ump3 = ForeignKeyField(Users,null=True)
    Ump4 = ForeignKeyField(Users,null=True)

class Lineups(BaseModel):
    id = AutoField(primary_key=True)
    Game_Number = ForeignKeyField(Games,field='Game_Number',null=True)
    Team = ForeignKeyField(Teams,field='Team_Abbr',null=True)
    Player = ForeignKeyField(Players,field='Player_ID',null=True)
    Box = IntegerField(null=True)
    Order = IntegerField(null=True)
    Position = CharField(null=True)

class Persons(BaseModel):
    id = AutoField(primary_key=True)
    PersonID = IntegerField(unique=True)
    Current_Name = CharField()
    Stats_Name = CharField(unique=True)
    Reddit = CharField(default=None)
    Discord = CharField()
    Discord_ID = CharField(null=True)
    Team = CharField()
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

class PAs(BaseModel):
    id = AutoField(primary_key=True)
    Play_No = IntegerField()
    Inning = CharField()
    Outs = IntegerField()
    BRC = IntegerField()
    Play_Type = CharField()
    Pitcher = CharField(null=True)
    Pitch_No = IntegerField(null=True)
    Batter = CharField(null=True)
    Swing_No = IntegerField(null=True)
    Catcher = CharField(null=True)
    Throw_No = IntegerField(null=True)
    Runner = CharField(null=True)
    Steal_No = IntegerField(null=True)
    Result = CharField()
    Run_Scored = IntegerField(null=True)
    Ghost_Scored = IntegerField(null=True)
    RBIs = IntegerField(null=True)
    Stolen_Base = IntegerField(null=True)
    Diff = IntegerField()
    Runs_Scored_On_Play = IntegerField(null=True)
    Off_Team = CharField()
    Def_Team = CharField()
    Game_No = IntegerField()
    Session_No = IntegerField()
    Inning_No = IntegerField()
    Pitcher_ID = CharField(null=True)
    Batter_ID = CharField(null=True)
    Catcher_ID = CharField(null=True)
    Runner_ID = CharField(null=True)

class All_PAs(BaseModel):
    id = AutoField(primary_key=True)
    Play_No = IntegerField()
    Inning = CharField()
    Outs = IntegerField()
    BRC = IntegerField()
    Play_Type = CharField()
    Pitcher = CharField(null=True)
    Pitch_No = IntegerField(null=True)
    Batter = CharField(null=True)
    Swing_No = IntegerField(null=True)
    Catcher = CharField(null=True)
    Throw_No = IntegerField(null=True)
    Runner = CharField(null=True)
    Steal_No = IntegerField(null=True)
    Result = CharField()
    Run_Scored = IntegerField(null=True)
    Ghost_Scored = IntegerField(null=True)
    RBIs = IntegerField(null=True)
    Stolen_Base = IntegerField(null=True)
    Diff = IntegerField()
    Runs_Scored_On_Play = IntegerField(null=True)
    Off_Team = CharField()
    Def_Team = CharField()
    Game_No = IntegerField()
    Session_No = IntegerField()
    Inning_No = IntegerField()
    Pitcher_ID = ForeignKeyField(Players,field='Player_ID',null=True)
    Batter_ID = ForeignKeyField(Players,field='Player_ID',null=True)
    Catcher_ID = ForeignKeyField(Players,field='Player_ID',null=True)
    Runner_ID = ForeignKeyField(Players,field='Player_ID',null=True)

class List_Nums(BaseModel):
    id = AutoField(primary_key=True)
    Player_ID = ForeignKeyField(Players,field='Player_ID')
    Game_Number = ForeignKeyField(Games,field='Game_Number')
    Position = CharField() # P, C, or B (batter)
    List = ListField()

def db_init():
    db.connect(reuse_if_open=True)
    db.drop_tables([Users,Teams,Players,All_PAs,Games,Lineups,All_PAs,List_Nums,Umpires])
    db.create_tables([Users,Teams,Players,All_PAs,Games,Lineups,All_PAs,List_Nums,Umpires])
    db.close()

def populate_test_data():
#    test_teams = [{'Team_Name':'Lonestar Pumpjacks','Team_Abbr':'LPJ','Logo':'/home/RLB_app/RLB_app/teams/static/LPJ_Logo'},
#                  {'Team_Name':'Sleepy Hollow Horsemen','Team_Abbr':'SHH','Logo':'/home/RLB_app/RLB_app/teams/static/SHH_Logo'},
#                  {'Team_Name':'TestTeam1','Team_Abbr':'TT1','Logo':'/home/RLB_app/RLB_app/teams/static/SHH_Logo'},
#                  {'Team_Name':'TestTeam2','Team_Abbr':'TT2','Logo':'/home/RLB_app/RLB_app/teams/static/SHH_Logo'}

    demo_teams = [{'Team_Name':'Curacao Couriers','Team_Abbr':'CUR'},
                  {'Team_Name':'Jamaica Jammers','Team_Abbr':'JAM'},
                  {'Team_Name':'St. Lucia Sharks','Team_Abbr':'STL'},
                  {'Team_Name':'Trinidad Tridents','Team_Abbr':'TRI'}]

    scrim_teams = [{'Team_Name':'Buffalo Buffalo','Team_Abbr':'BUF'},
                   {'Team_Name':'Portland Pioneers','Team_Abbr':'POR'}]


    test_umpires = [
    {'Crew_Name':'FT_Blasit','Ump1':15},
    {'Crew_Name':'BUFPOR','Ump1':11,'Ump2':12,'Ump3':30}]

    with open('league_users.csv') as file:
        league_users = []
        keys = ['Reddit_Name','Discord_Name','Discord_ID','Player','Umpire','Commissioner']
        reader = csv.reader(file)
        for row in reader:
            user = dict(zip(keys,row))
            league_users.append(user)
    with open('league_players.csv') as file:
        league_players = []
        keys = ['User_ID','Player_ID','Player_Name','PPos','SPos','Hand','Team','Contact','Eye','Power','Speed','Movement','Command','Velocity','Awareness']
        reader = csv.reader(file)
        for row in reader:
            player = dict(zip(keys,row))
            league_players.append(player)
    with open('league_teams.csv') as file:
        league_teams = []
        keys = ['Team_Name','Team_Abbr']
        reader = csv.reader(file)
        for row in reader:
            team = dict(zip(keys,row))
            league_teams.append(team)


#    demo_games = [{'Game_Number':50101,'Game_ID':'JAMTRI1','Season':5,'Session':1,'Away':'JAM','Home':'TRI','Umpires':['dyslexda','FT_Blasit']}]
#    test_games = [{'Game_Number':50101,'Game_ID':'CURJAM1','Season':5,'Session':1,'Away':'CUR','Home':'JAM','Umpires':['dyslexda','FT_Blasit']},
#                  {'Game_Number':50102,'Game_ID':'STLTRI1','Season':5,'Session':1,'Away':'STL','Home':'TRI','Umpires':['dyslexda','FT_Blasit']},
#                  {'Game_Number':50201,'Game_ID':'JAMSTL2','Season':5,'Session':2,'Away':'JAM','Home':'STL','Umpires':['dyslexda','FT_Blasit']},
#                  {'Game_Number':50202,'Game_ID':'TRICUR2','Season':5,'Session':2,'Away':'TRI','Home':'CUR','Umpires':['dyslexda','FT_Blasit']}]

    with db.atomic():
        Teams.insert_many(league_teams).execute()
        Users.insert_many(league_users).execute()
        Players.insert_many(league_players).execute()
#        Games.insert_many(test_games).execute()
        Umpires.insert_many(test_umpires).execute()

all_pas_keys = ['Play_No','Inning','Outs','BRC','Play_Type','Pitcher','Pitch_No','Batter','Swing_No','Catcher','Throw_No','Runner','Steal_No','Result','Run_Scored','Ghost_Scored','RBIs','Stolen_Base','Diff','Runs_Scored_On_Play','Off_Team','Def_Team','Game_No','Session_No','Inning_No','Pitcher_ID','Batter_ID','Catcher_ID','Runner_ID']

persons_keys = ['PersonID','Current_Name','Stats_Name','Reddit','Discord','Discord_ID','Team','Player','Captain','GM','Retired','Hiatus','Rookie','Primary','Backup','Hand','CON','EYE','PWR','SPD','MOV','CMD','VEL','AWR']

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
    db.connect(reuse_if_open=True)
    db.drop_tables([Persons])
    db.create_tables([Persons])
    persons = []
    persons_data = persons_sh.get_all_values(include_tailing_empty_rows=False)
    for p in persons_data:
        person = dict(zip(persons_keys,p))
        persons.append(person)
    persons.pop(0) #header row
    with db.atomic():
        Persons.insert_many(persons).execute()
    db.close()

if __name__ == "__main__":
    main()
#    db.connect()
#    db.create_tables([List_Nums])
#    db.close()
#    migration()
#    db_init()
#    populate_test_data()