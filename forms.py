from peewee import *
from flask_wtf import FlaskForm
from wtforms import Form, FieldList, FormField, SelectField, IntegerField, StringField, HiddenField, validators

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
    a_score = IntegerField()
    h_score = IntegerField()
    runner = SelectField(label='Runner',choices = [('',''),(1,1),(2,2),(3,3)], validators=[validators.optional()])
    pitch = IntegerField(validators=[validators.optional(),validators.NumberRange(min=1,max=1000)])
    swing = IntegerField(validators=[validators.optional(),validators.NumberRange(min=1,max=1000)])
    r_steal = IntegerField(label='Steal',validators=[validators.optional(),validators.NumberRange(min=1,max=1000)])
    c_throw = IntegerField(label='Throw',validators=[validators.optional(),validators.NumberRange(min=1,max=1000)])