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

# Builds absolute path relative to this models.py file so other directories (like bots) can find the same database when importing
db_path = path.join(basedir+'/shared/','mlg_api.s')
db = PooledSqliteExtDatabase(db_path, check_same_thread=False, pragmas={'foreign_keys': 1},max_connections=30,stale_timeout=500)

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

    def sheets_compare(self):
        teams_dict = {
        'TID': self.TID,
        'Abbr': self.Abbr,
        'Name': self.Name,
        'Stadium': self.Stadium,
        'League': self.League,
        'Division': self.Division,
        'Logo_URL': self.Logo_URL,
        'Location': self.Location,
        'Mascot': self.Mascot}
        return(teams_dict)

class TeamsSchema(ModelSchema):
    class Meta:
        model = Teams

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

    def sheets_compare(self):
        persons_dict = {
        'PersonID': self.PersonID,
        'Current_Name': self.Current_Name,
        'Stats_Name': self.Stats_Name,
        'Reddit': self.Reddit,
        'Discord': self.Discord,
        'Discord_ID': self.Discord_ID,
        'Team': self.Team,
        'Player': self.Player,
        'Captain': self.Captain,
        'GM': self.GM,
        'Retired': self.Retired,
        'Hiatus': self.Hiatus,
        'Rookie': self.Rookie,
        'Primary': self.Primary,
        'Backup': self.Backup,
        'Hand': self.Hand,
        'CON': self.CON,
        'EYE': self.EYE,
        'PWR': self.PWR,
        'SPD': self.SPD,
        'MOV': self.MOV,
        'CMD': self.CMD,
        'VEL': self.VEL,
        'AWR': self.AWR}
        return(persons_dict)

class PersonsSchema(ModelSchema):
    class Meta:
        model = Persons
        dump_only_pk = False
        string_keys = False

class Schedules(BaseModel):
    id = AutoField(primary_key=True)
    Session = IntegerField()
    Game_No = IntegerField(unique=True)
    Away = ForeignKeyField(Teams,field='Abbr',null=True)
    Home = ForeignKeyField(Teams,field='Abbr',null=True)
    Game_ID = CharField(null=True)
    A_Score = IntegerField(null=True)
    H_Score = IntegerField(null=True)
    Inning = CharField(null=True)
    Situation = CharField(null=True)
    Win = ForeignKeyField(Teams,field='Abbr',null=True)
    Loss = ForeignKeyField(Teams,field='Abbr',null=True)
#    WP = ForeignKeyField(Persons,field='Stats_Name',null=True)
#    LP = ForeignKeyField(Persons,field='Stats_Name',null=True)
#    SV = ForeignKeyField(Persons,field='Stats_Name',null=True)
#    POTG = ForeignKeyField(Persons,field='Stats_Name',null=True)
    WP = CharField(null=True)
    LP = CharField(null=True)
    SV = CharField(null=True)
    POTG = CharField(null=True)
    Umpire = CharField(null=True)
    Reddit = CharField(null=True)
    Log = CharField(null=True)
    Duration = FloatField(null=True)
    Total_Plays = IntegerField(null=True)
    Plays_Per_Day = FloatField(null=True)

    def sheets_compare(self):
        schedules_dict = {
        'Session': self.Session,
        'Game_No': self.Game_No,
        'Away': self.Away.Abbr,
        'Home': self.Home.Abbr,
        'Game_ID': self.Game_ID,
        'A_Score': self.A_Score,
        'H_Score': self.H_Score,
        'Inning': self.Inning,
        'Situation': self.Situation,
        'Win': self.Win,
        'Loss': self.Loss,
        'WP': self.WP,
        'LP': self.LP,
        'SV': self.SV,
        'POTG': self.POTG,
        'Umpire': self.Umpire,
        'Reddit': self.Reddit,
        'Log': self.Log,
        'Duration': self.Duration,
        'Total_Plays': self.Total_Plays,
        'Plays_Per_Day': self.Plays_Per_Day}
        if schedules_dict['Win']: schedules_dict['Win'] = self.Win.Abbr
        if schedules_dict['Loss']: schedules_dict['Loss'] = self.Loss.Abbr
        return(schedules_dict)

class SchedulesSchema(ModelSchema):
    class Meta:
        model = Schedules

class Lineups(BaseModel):
    id = AutoField(primary_key=True)
    Game_No = ForeignKeyField(Schedules,field='Game_No',null=True)
    Team = ForeignKeyField(Teams,field='Abbr',null=True)
    Player = ForeignKeyField(Persons,field='PersonID',null=True)
    Play_Entrance = IntegerField(null=True)
    Position = CharField(null=True)
    Order = IntegerField(null=True)
    Pitcher_No = IntegerField(null=True)

    def sheets_compare(self):
        lineups_dict = {
        'Game_No': self.Game_No.Game_No,
        'Team': self.Team.Abbr,
        'Player': self.Player.PersonID,
        'Play_Entrance': self.Play_Entrance,
        'Position': self.Position,
        'Order': self.Order,
        'Pitcher_No': self.Pitcher_No}
        return(lineups_dict)

class LineupsSchema(ModelSchema):
    class Meta:
        model = Lineups

class PAs(BaseModel):
    id = AutoField(primary_key=True)
    Play_No = IntegerField(null=True)
    Inning = CharField()
    Outs = IntegerField()
    BRC = IntegerField()
    Play_Type = CharField(null=True)
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
    Diff = IntegerField(null=True)
    Runs_Scored_On_Play = IntegerField(null=True)
    Off_Team = CharField()
    Def_Team = CharField()
    Game_No = IntegerField()
    Session_No = IntegerField()
    Inning_No = IntegerField(null=True)
    Pitcher_ID = IntegerField(null=True)
    Batter_ID = IntegerField(null=True)
    Catcher_ID = IntegerField(null=True)
    Runner_ID = IntegerField(null=True)

    def sheets_compare(self):
        str_dict = {
        'Play_No': str(self.Play_No),
        'Inning': str(self.Inning),
        'Outs': str(self.Outs),
        'BRC': str(self.BRC),
        'Play_Type': str(self.Play_Type),
        'Pitcher': str(self.Pitcher),
        'Pitch_No': str(self.Pitch_No),
        'Batter': str(self.Batter),
        'Swing_No': str(self.Swing_No),
        'Catcher': str(self.Catcher),
        'Throw_No': str(self.Throw_No),
        'Runner': str(self.Runner),
        'Steal_No': str(self.Steal_No),
        'Result': str(self.Result),
        'Run_Scored': str(self.Run_Scored),
        'Ghost_Scored': str(self.Ghost_Scored),
        'RBIs': str(self.RBIs),
        'Stolen_Base': str(self.Stolen_Base),
        'Diff': str(self.Diff),
        'Runs_Scored_On_Play': str(self.Runs_Scored_On_Play),
        'Off_Team': str(self.Off_Team),
        'Def_Team': str(self.Def_Team),
        'Game_No': str(self.Game_No),
        'Session_No': str(self.Session_No),
        'Inning_No': str(self.Inning_No),
        'Pitcher_ID': str(self.Pitcher_ID),
        'Batter_ID': str(self.Batter_ID),
        'Catcher_ID': str(self.Catcher_ID),
        'Runner_ID': str(self.Runner_ID)}
        return(str_dict)

    def sheets_compare_int(self):
        int_dict = {
        'Play_No': self.Play_No,
        'Inning': self.Inning,
        'Outs': self.Outs,
        'BRC': self.BRC,
        'Play_Type': self.Play_Type,
        'Pitcher': self.Pitcher,
        'Pitch_No': self.Pitch_No,
        'Batter': self.Batter,
        'Swing_No': self.Swing_No,
        'Catcher': self.Catcher,
        'Throw_No': self.Throw_No,
        'Runner': self.Runner,
        'Steal_No': self.Steal_No,
        'Result': self.Result,
        'Run_Scored': self.Run_Scored,
        'Ghost_Scored': self.Ghost_Scored,
        'RBIs': self.RBIs,
        'Stolen_Base': self.Stolen_Base,
        'Diff': self.Diff,
        'Runs_Scored_On_Play': self.Runs_Scored_On_Play,
        'Off_Team': self.Off_Team,
        'Def_Team': self.Def_Team,
        'Game_No': self.Game_No,
        'Session_No': self.Session_No,
        'Inning_No': self.Inning_No,
        'Pitcher_ID': self.Pitcher_ID,
        'Batter_ID': self.Batter_ID,
        'Catcher_ID': self.Catcher_ID,
        'Runner_ID': self.Runner_ID}
        return(int_dict)

class PlaysSchema(ModelSchema):
    class Meta:
        model = PAs

def main():
    pass

if __name__ == "__main__":
    main()