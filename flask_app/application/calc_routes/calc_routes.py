import random, time, sys
from os import environ, path
from flask import Blueprint, render_template, g, session, request, redirect, url_for, flash, jsonify
from flask import current_app as app
from shared.models import Teams, Players, Games, All_PAs, Lineups, db
from shared.forms import LineupBoxForm, GameStatusForm
import shared.calculator.calculator as calc
import shared.calculator.ranges_files.ranges_calc as ranges_calc
import shared.calculator.ranges_files.ranges_lookup as ranges_lookup
from peewee import *
from dotenv import load_dotenv
basedir = path.dirname(path.dirname(path.dirname(__file__)))
load_dotenv(path.join(basedir, '.env'))

calc_bp = Blueprint(
    'calc_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/calc_routes/static/'
)

class GameState():

    def __init__(self, **kwargs):
        self.Batter = kwargs['Batter']
        self.Pitcher = kwargs['Pitcher']
        self.Outs = kwargs['Outs']
        self.First_Base = kwargs['First_Base'] 
        self.Second_Base = kwargs['Second_Base'] 
        self.Third_Base = kwargs['Third_Base'] 

class PlayerCard():

    def __init__(self, Hand='R', Contact=0, Eye=0, Power=0, Speed=0, Movement=0, Command=0, Velocity=0, Awareness=0):
        self.Hand = Hand
        self.Contact = int(Contact)
        self.Eye = int(Eye)
        self.Power = int(Power)
        self.Speed = int(Speed)
        self.Movement = int(Movement)
        self.Command = int(Command)
        self.Velocity = int(Velocity)
        self.Awareness = int(Awareness)

def gen_ranges_html(results):
    return render_template(
           'ranges_table.html',
           results=results)

@calc_bp.route('/calculator', methods=['GET','POST'])
def calc_page():
    return render_template(
        'calculator.html')

@calc_bp.route('/calculator/api', methods=['GET','POST'])
def calc_api():
    if request.method == 'POST':
        firstb,secondb,thirdb = None,None,None
        if request.form['first_base'] != '':
            firstb = PlayerCard(Speed=request.form['first_base'])
        if request.form['second_base'] != '':
            secondb = PlayerCard(Speed=request.form['second_base'])
        if request.form['third_base'] != '':
            thirdb = PlayerCard(Speed=request.form['third_base'])
        pitcher = PlayerCard(Hand=request.form['p_hand'],Movement=request.form['p_mov'],Command=request.form['p_com'],Velocity=request.form['p_vel'],Awareness=request.form['p_awa'])
        batter = PlayerCard(Hand=request.form['b_hand'],Contact=request.form['b_con'],Eye=request.form['b_eye'],Power=request.form['b_pow'],Speed=request.form['b_spe'])
        game = GameState(Pitcher=pitcher,Batter=batter,Outs=int(request.form['outs']),First_Base=firstb,Second_Base=secondb,Third_Base=thirdb)
        handedness = calc.ranges_calc.calc_handedness(game.Pitcher,game.Batter)
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
        current = 0
        results = []
        for outcome in all_order:
            window = ranges[outcome]
            start = current
            end = current + window - 1
            line = {}
            line['Outcome'] = outcome
            line['Range'] = window
            line['Start'] = start
            line['End'] = end
            results.append(line)
            current = end + 1
        ranges_html = gen_ranges_html(results)
        return(ranges_html)


@calc_bp.route('/calculator/api/ump/<game_number>/ranges', methods=['GET','POST'])
def calc_api_ranges(game_number):
    if request.method == 'POST':
        game = Games.get(Games.Game_Number == game_number)
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
        current = 0
        results = []
        for outcome in all_order:
            window = ranges[outcome]
            start = current
            end = current + window - 1
            line = {}
            line['Outcome'] = outcome
            line['Range'] = window
            line['Start'] = start
            line['End'] = end
            results.append(line)
            current = end + 1
        ranges_html = gen_ranges_html(results)
        if request.form['pitch'] != '' and request.form['swing'] != '':
            diff = ranges_calc.calc_diff(int(request.form['pitch']),int(request.form['swing']))
            result = result_list[diff]
            ranges_html += "<br />"
            ranges_html += "<h5>Result</h5>"
            ranges_html += (f"<h6>{result}</h6>")
        return(ranges_html)