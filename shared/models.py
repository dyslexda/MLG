from peewee import *
from playhouse.pool import PooledSqliteExtDatabase
from playhouse.migrate import *
from wtfpeewee.orm import model_form
import wtforms, os, inspect, csv, json
from flask_wtf import FlaskForm
from wtforms import Form, FieldList, FormField, SelectField, HiddenField, validators

# Builds absolute path relative to this models.py file so other directories (like bots) can find the same database when importing
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'mlg.s')
#db = SqliteDatabase(db_path, check_same_thread=False, pragmas={'foreign_keys': 1})
db = PooledSqliteExtDatabase(db_path, check_same_thread=False, pragmas={'foreign_keys': 1},max_connections=30,stale_timeout=500)

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

class BoxOrderPosForm(Form):
    box_choices = []
    for i in range(0,10): box_choices.append((i,i))
    order_choices = []
    for i in range(0,10): order_choices.append((i,i))
    pos_choices = [('-','-')]
    for i in ['P','C','1B','2B','3B','SS','LF','CF','RF','DH']: pos_choices.append((i,i))
    player_id = HiddenField()
    box = SelectField(coerce=int,choices = box_choices)
    order = SelectField(coerce=int,choices = order_choices)
    pos = SelectField(choices = pos_choices)

class LineupBoxForm(FlaskForm):
    bop = FieldList(FormField(BoxOrderPosForm))

class GameStatusForm(FlaskForm):
    choices = ['Staged','Init','Started','Final']
    status_choices = []
    for i in choices: status_choices.append((i,i))
    game_id = HiddenField()
    status = SelectField(choices = status_choices)

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

if __name__ == "__main__":
#    db.connect()
#    db.create_tables([List_Nums])
#    db.close()
#    migration()
    db_init()
    populate_test_data()