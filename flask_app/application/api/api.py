"""General page routes."""
from flask import Blueprint, render_template, g
from flask import current_app as app
from shared.api_models import *
from decimal import Decimal
import flask_app.application.api.standings as calc_standings
import random

# Blueprint Configuration
api_bp = Blueprint(
    'api_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

def get_person(person_id):
    person = Persons.get(Persons.PersonID == person_id)
    dumped = PersonsSchema().dump(person)
    return(dumped)

def get_persons():
    people = Persons.select()
    dumped = PersonsSchema(many=True).dump(people)
    return(dumped)

def get_some_persons(**kwargs):
    people = Persons.select()
    for kwarg in kwargs:
        people = people.where(getattr(Persons,kwarg) == kwargs[kwarg])
    dumped = PersonsSchema(many=True).dump(people)
    return(dumped)

def schedules(Team=None):
    schedules = Schedules.select()
    if Team:
        schedules = schedules.where((Schedules.Away == Team) | (Schedules.Home == Team))
    dumped = SchedulesSchema(many=True).dump(schedules)
    return(dumped)

def standings():
    return(calc_standings.LeagueStandings().to_dict())

def teams():
    teams = Teams.select().order_by(Teams.Abbr.asc())
    dumped = TeamsSchema(many=True).dump(teams)
    return(dumped)

def plays(limit,offset,**kwargs):
    plays = PAs.select()
    for kwarg in kwargs:
        if kwarg == 'Season':
            if kwargs[kwarg] == 1:
                plays = plays.where(PAs.Play_No < 15000)
            else:
                low = kwargs[kwarg] * 10000000
                high = (kwargs[kwarg]+1) * 10000000
                plays = plays.where(PAs.Play_No.between(low,high))
        else:
            plays = plays.where(getattr(PAs,kwarg) == kwargs[kwarg])
    totalRecords = plays.count()
    plays = plays.limit(limit).offset(offset)
    dumped = PlaysSchema(many=True).dump(plays)
    response = {}
    response['plays'] = dumped
    response['limit'] = limit
    response['offset'] = offset
    response['totalRecords'] = totalRecords
    response['totalReturned'] = plays.count()
    return(response)