"""General page routes."""
from flask import Blueprint, render_template, g
from flask import current_app as app
from shared.api_models import *

# Blueprint Configuration
api_bp = Blueprint(
    'api_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

def get_person(person_id):
    person = Persons.get(Persons.PersonID == person_id)
    dumped = PersonsSchema().dump(person)
    return dumped

def get_persons():
    people = Persons.select()
    dumped = PersonsSchema(many=True).dump(people)
    return dumped

def get_some_persons(**kwargs):
    people = Persons.select()
    for kwarg in kwargs:
        people = people.where(getattr(Persons,kwarg) == kwargs[kwarg])
    dumped = PersonsSchema(many=True).dump(people)
    return dumped