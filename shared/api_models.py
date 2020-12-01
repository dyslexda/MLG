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