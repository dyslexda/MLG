from shared.api_models import *
import shared.calculator.ranges_files.ranges_calc as ranges_calc
import shared.calculator.ranges_files.ranges_lookup as ranges_lookup


class GameState():

    def __init__(self, **kwargs):
        self.Batter = kwargs['Batter']
        self.Pitcher = kwargs['Pitcher']
        self.Outs = kwargs['Outs']
        self.First_Base = kwargs['First_Base'] 
        self.Second_Base = kwargs['Second_Base'] 
        self.Third_Base = kwargs['Third_Base'] 
        self.Bunt = kwargs['Bunt']
        self.Pitch = kwargs['Pitch']
        self.Swing = kwargs['Swing']

    def outcome(self):
        pitcher = {'Name':self.Pitcher.Name,'Attr':(str(self.Hand)+str(self.Movement)+str(self.Command)+str(self.Velocity)+str(self.Awareness))}
        batter = {'Name':self.Batter.Name,'Attr':(str(self.Hand)+str(self.Contact)+str(self.Eye)+str(self.Power)+str(self.Speed))}
        pitch = self.Pitch
        swing = self.Swing
        if pitch and swing:
            outcome = [ranges_calc.calc_diff(pitch,swing)]

class PlayerCard():

    def __init__(self, Name=None, Hand='R', Contact=0, Eye=0, Power=0, Speed=0, Movement=0, Command=0, Velocity=0, Awareness=0):
        self.Name = Name
        self.Hand = Hand
        self.Contact = int(Contact)
        self.Eye = int(Eye)
        self.Power = int(Power)
        self.Speed = int(Speed)
        self.Movement = int(Movement)
        self.Command = int(Command)
        self.Velocity = int(Velocity)
        self.Awareness = int(Awareness)

    def attr(self):
        return({'P':(str(self.Hand)+str(self.Movement)+str(self.Command)+str(self.Velocity)+str(self.Awareness)),'B':(str(self.Hand)+str(self.Contact)+str(self.Eye)+str(self.Power)+str(self.Speed))})

    def p_attr(self):
        return(str(self.Hand)+str(self.Movement)+str(self.Command)+str(self.Velocity)+str(self.Awareness))

    def b_attr(self):
        return(str(self.Hand)+str(self.Contact)+str(self.Eye)+str(self.Power)+str(self.Speed))

def genPlayerCard(input,pos=None):
    if pos == 'p':
        player = PlayerCard(Hand=input[0],Movement=input[1],Command=input[2],Velocity=input[3],Awareness=input[4])
    elif pos == 'b':
        player = PlayerCard(Hand=input[0],Contact=input[1],Eye=input[2],Power=input[3],Speed=input[4])
    else:
        player = PlayerCard(Name=input.Stats_Name,Hand=input.Hand,Contact=input.CON,Eye=input.EYE,Power=input.PWR,Speed=input.SPD,Movement=input.MOV,Command=input.CMD,Velocity=input.VEL,Awareness=input.AWR)
    return(player)

def playerValidation(kwargs,prefix,errors):
    player,model = None,None
    if (prefix + '_id') in kwargs: model = Persons.get_or_none(Persons.PersonID == kwargs[(prefix + '_id')])
    elif (prefix + '_name') in kwargs: model = Persons.get_or_none(Persons.Stats_Name == kwargs[(prefix + '_name')])
    elif (prefix + '_attr') in kwargs:
        if kwargs[(prefix + '_attr')][0].upper() in ['L','R'] and kwargs[(prefix + '_attr')][1:].isdigit() and len(kwargs[(prefix + '_attr')]) == 5:
            player = genPlayerCard(kwargs[(prefix + '_attr')],prefix)
        else: errors.append(f"{prefix} attributes not correctly formatted, please use e.g. R5511")
    if model: player = genPlayerCard(model)
    if not player: errors.append(f"{prefix} not found in database")
    return(player,errors)

def runnerValidation(kwargs,errors):
    firstb,secondb,thirdb = None,None,None
    runners = {'b1':firstb,'b2':secondb,'b3':thirdb}
    for base in runners:
        runner = None
        if base in kwargs:
            if kwargs[base].isdigit(): runners[base] = PlayerCard(Speed=kwargs[base])
            else:
                runner = Persons.get_or_none(Persons.Stats_Name == kwargs[base])
                if runner: runners[base] = genPlayerCard(runner)
                else: errors.append(f'Runner at {base} not found in database')
    return(runners,errors)

def argValidation(kwargs):
    errors = []
    pitch,swing = None,None
    pitcher,errors = playerValidation(kwargs,'p',errors)
    batter,errors = playerValidation(kwargs,'b',errors)
    runners,errors = runnerValidation(kwargs,errors)
    if 'pitch' in kwargs: pitch = kwargs['pitch']
    if 'swing' in kwargs: swing = kwargs['swing']
    return(pitcher,pitch,batter,swing,runners,errors)

def calcCode(game):
    handedness = ranges_calc.calc_handedness(game.Pitcher,game.Batter)
    ranges = ranges_calc.calc_ranges(ranges_lookup.obr_dict, ranges_lookup.modifiers_dict, game.Pitcher,
                                     game.Batter, handedness)
    if game.Bunt:
        ranges, all_order = ranges_calc.bunt_calc(game, ranges, ranges_lookup.bunt_dict)
    else:
        if (game.First_Base != None or game.Second_Base != None):
            ranges, obr_ordering = ranges_calc.wh_calc(game, ranges)
        else:
            obr_ordering = ['HR', '3B', '2B', '1B', 'IF1B', 'BB']
        ranges = ranges_calc.go_calc(game, ranges, ranges_lookup.go_order_dict)
        if game.Outs != 2 and (game.Second_Base != None or game.Third_Base != None):
            ranges, fo_ordering = ranges_calc.dfo_calc(game, ranges)
        else:
            fo_ordering = ['FO']
        brc = ranges_calc.brc_calc(game)
        outs_ordering = list(ranges_lookup.go_order_dict[str(brc) + '_' + str(game.Outs)])
        if 'GORA' in outs_ordering:
            outs_ordering.remove('GORA')
            fo_ordering = ['GORA'] + fo_ordering
        all_order = obr_ordering + fo_ordering + outs_ordering
    result_list = []
    for result in all_order:
        for _ in range(ranges[result]):
            result_list.append(result)
    if game.Pitch and game.Swing:
        outcome = result_list[ranges_calc.calc_diff(game.Pitch,game.Swing)]
    else: outcome = None
    current = 0
    results = {}
    for result in all_order:
        end = current + ranges[result] - 1
        results[result] = {}
        results[result]['Range'] = ranges[result]
        results[result]['Start'] = current
        results[result]['End'] = end
        current = end + 1
#    results = []
#    for result in all_order:
#        window = ranges[result]
#        start = current
#        end = current + window - 1
#        line = {}
#        line['Result'] = result
#        line['Range'] = window
#        line['Start'] = start
#        line['End'] = end
#        results.append(line)
#        current = end + 1
    return(results,all_order,outcome)

def formatResponse(game,results,order,outcome):
    pitcher = {'Name':game.Pitcher.Name,'Attr':game.Pitcher.p_attr()}
    batter = {'Name':game.Batter.Name,'Attr':game.Batter.b_attr()}
    diff = None
    if game.Pitch and game.Swing: diff = ranges_calc.calc_diff(game.Pitch,game.Swing)
    swing_bug = {'Pitch':game.Pitch,'Swing':game.Swing,'Diff':diff,'Result':outcome}
    response = {}
    response['pitcher'] = {'Name':game.Pitcher.Name,'Attr':game.Pitcher.p_attr()}
    response['batter'] = {'Name':game.Batter.Name,'Attr':game.Batter.b_attr()}
    response['order'] = order
    response['swingBug'] = {'Pitch':game.Pitch,'Swing':game.Swing,'Diff':diff,'Result':outcome}
    response['ranges'] = results
    return(response)