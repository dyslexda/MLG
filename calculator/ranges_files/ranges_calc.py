from decimal import Decimal
import numpy as np

def brc_calc(game):
    b1, b2, b3 = 0, 0, 0
    if game.First_Base is not None: b1 = 1
    if game.Second_Base is not None: b2 = 1
    if game.Third_Base is not None: b3 = 1
    concat_code = str(b1) + str(b2) + str(b3)
    if concat_code == '000':
        brc = 0
    elif concat_code == '100':
        brc = 1
    elif concat_code == '010':
        brc = 2
    elif concat_code == '001':
        brc = 3
    elif concat_code == '110':
        brc = 4
    elif concat_code == '101':
        brc = 5
    elif concat_code == '011':
        brc = 6
    elif concat_code == '111':
        brc = 7
    return brc

def calc_diff(pitch,swing):
    diff = abs(pitch - swing)
    if (diff > 500):
        diff = 1000 - diff
    return diff

def calc_handedness(pitcher,batter):
    if batter.Hand == pitcher.Hand:
        handedness = "SAME"
    else:
        handedness = "DIFF"
    return handedness

def stat_checker(b,p):
    stat_diff = (b - p)
    if(stat_diff > 5):
        stat_diff = 5
    elif(stat_diff < -5):
        stat_diff = -5
    return stat_diff

def avg_speed(game):
    avg_spe, runners = 0, 0
    for runner in [game.First_Base, game.Second_Base, game.Third_Base]:
        if runner is not None:
            avg_spe += runner.Speed
            runners += 1
    avg_spe = int(Decimal(avg_spe / runners).quantize(Decimal('1.'), rounding='ROUND_DOWN'))
    return avg_spe

def calc_steal(game,steal_dict,diff):
    if game.Runner == 1:
        base = '2'
        runner_speed = game.First_Base.Speed
    elif game.Runner == 2:
        base = '3'
        runner_speed = game.Second_Base.Speed
    elif game.Runner == 3:
        base = '4'
        runner_speed = game.Third_Base.Speed
    battery = int(Decimal((game.Pitcher.Awareness + game.Catcher.Eye)/2).quantize(Decimal('1.'), rounding='ROUND_DOWN'))
    matchup = runner_speed - battery
    steal_range = steal_dict[base][matchup]
    if int(diff) <= int(steal_range):
        result = 'SB'+base
    else:
        result = 'CS'+base
    return(result)

def calc_ranges(obr_dict,modifiers_dict,pitcher,batter,handedness):
    raw_base_hit = obr_dict['HIT'][handedness][stat_checker(batter.Contact,pitcher.Movement)]
    mod_SvA = modifiers_dict['SvA'][stat_checker(batter.Speed,pitcher.Awareness)]
    mod_PitAwa = modifiers_dict['PitAwa'][pitcher.Awareness]
    final_base_hit = raw_base_hit + mod_SvA + mod_PitAwa
    range_hr = obr_dict['HR'][handedness][stat_checker(batter.Power,pitcher.Velocity)]
    range_3b = obr_dict['3B'][handedness][stat_checker(batter.Speed,pitcher.Awareness)]
    range_2b = obr_dict['2B'][handedness][stat_checker(batter.Speed,pitcher.Awareness)]
    range_if1b = obr_dict['IF1B'][handedness][stat_checker(batter.Speed,pitcher.Awareness)]
    range_bb = obr_dict['BB'][handedness][stat_checker(batter.Eye,pitcher.Command)]
    range_1b = (final_base_hit - range_hr - range_3b - range_2b) + 5
    range_on_base = range_hr + range_3b + range_2b + range_if1b + range_bb + range_1b - 1
    range_po = int(Decimal(((500 - range_on_base) * obr_dict['FO'][handedness][stat_checker(batter.Power,pitcher.Velocity)]) * obr_dict['PO'][handedness][stat_checker(batter.Power,pitcher.Velocity)]).quantize(Decimal('1.'),rounding='ROUND_HALF_UP') + 1)
    range_fo = int(Decimal(((500 - range_on_base) * obr_dict['FO'][handedness][stat_checker(batter.Power,pitcher.Velocity)]) - range_po).quantize(Decimal('1.'),rounding='ROUND_HALF_UP'))
    range_k = obr_dict['K'][handedness][stat_checker(batter.Contact,pitcher.Movement)]
    range_go = 500 - (range_on_base + range_po + range_fo + range_k)
    result_dict = {}
    result_dict['On Base'] = int(range_on_base)
    result_dict['HR'] = int(range_hr)
    result_dict['3B'] = int(range_3b)
    result_dict['2B'] = int(range_2b)
    result_dict['IF1B'] = int(range_if1b)
    result_dict['BB'] = int(range_bb)
    result_dict['1B'] = int(range_1b)
    result_dict['FO'] = int(range_fo)
    result_dict['PO'] = int(range_po)
    result_dict['GO'] = int(range_go)
    result_dict['K'] = int(range_k)
    return result_dict

def wh_calc(game,result_dict):
    brc = brc_calc(game)
    if brc in [4,7]:
        if game.Second_Base.Speed > game.First_Base.Speed:
            lead_speed = game.Second_Base.Speed
            lagg_speed = game.First_Base.Speed
            lead_multiplier = wh_multiplier(lead_speed)
            lagg_multiplier = wh_multiplier(lagg_speed)
            range_1bwh = int(Decimal(lagg_multiplier * result_dict['1B']).quantize(Decimal('1.'),rounding='ROUND_DOWN')) + 1
            range_1bwh2 = int(Decimal(lead_multiplier * result_dict['1B']).quantize(Decimal('1.'),rounding='ROUND_DOWN')) + 1 - range_1bwh
            range_2bwh = int(Decimal(lagg_multiplier * result_dict['2B']).quantize(Decimal('1.'),rounding='ROUND_DOWN')) + 1
            result_dict['1BWH'] = int(range_1bwh)
            result_dict['1BWH2'] = int(range_1bwh2)
            result_dict['2BWH'] = int(range_2bwh)
            result_dict['1B'] = result_dict['1B'] - result_dict['1BWH'] - result_dict['1BWH2']
            result_dict['2B'] = result_dict['2B'] - result_dict['2BWH']
            ordering = ['HR','3B','2BWH','2B','1BWH','1BWH2','1B','IF1B','BB']
        else:
            lead_speed = game.First_Base.Speed
            lead_multiplier = wh_multiplier(lead_speed)
            range_1bwh = int(Decimal(lead_multiplier * result_dict['1B']).quantize(Decimal('1.'),rounding='ROUND_DOWN')) + 1
            range_2bwh = int(Decimal(lead_multiplier * result_dict['2B']).quantize(Decimal('1.'),rounding='ROUND_DOWN')) + 1
            result_dict['1BWH'] = int(range_1bwh)
            result_dict['2BWH'] = int(range_2bwh)
            result_dict['2B'] = result_dict['2B'] - result_dict['2BWH']
            result_dict['1B'] = result_dict['1B'] - result_dict['1BWH']
            ordering = ['HR','3B','2BWH','2B','1BWH','1B','IF1B','BB']
    elif brc in [2,6]:
        lead_speed = game.Second_Base.Speed
        lead_multiplier = wh_multiplier(lead_speed)
        range_1bwh = int(Decimal(lead_multiplier * result_dict['1B']).quantize(Decimal('1.'),rounding='ROUND_DOWN')) + 1
        result_dict['1BWH'] = int(range_1bwh)
        result_dict['1B'] = result_dict['1B'] - result_dict['1BWH']
        ordering = ['HR','3B','2B','1BWH','1B','IF1B','BB']
    else:
        if game.Second_Base != None:
            lead_speed = game.Second_Base.Speed
        else:
            lead_speed = game.First_Base.Speed
        lead_multiplier = wh_multiplier(lead_speed)
        range_1bwh = int(Decimal(lead_multiplier * result_dict['1B']).quantize(Decimal('1.'),rounding='ROUND_DOWN')) + 1
        range_2bwh = int(Decimal(lead_multiplier * result_dict['2B']).quantize(Decimal('1.'),rounding='ROUND_DOWN')) + 1
        result_dict['2BWH'] = int(range_2bwh)
        result_dict['1BWH'] = int(range_1bwh)
        result_dict['2B'] = result_dict['2B'] - result_dict['2BWH']
        result_dict['1B'] = result_dict['1B'] - result_dict['1BWH']
        ordering = ['HR','3B','2BWH','2B','1BWH','1B','IF1B','BB']
    return result_dict,ordering

def wh_multiplier(speed):
    if speed > 2:
        multiplier = -0.06 + (speed * 0.07)
    else:
        multiplier = 0.045 + (speed * 0.035)
    return(multiplier)

def dfo_calc(game,result_dict):
    brc = brc_calc(game)
    bat_pow = (game.Batter.Power * 1.5)
    try:
        run_spe = (game.Second_Base.Speed * 1.5)
    except:
        run_spe = -1
    combined = int(Decimal(bat_pow + run_spe).quantize(Decimal('1.'),rounding='ROUND_HALF_UP'))
    multiplier = dfo_multiplier(combined)
    if brc in [3, 5, 6, 7]:
        result_dict['DSacF'] = int(Decimal(result_dict['FO'] * multiplier).quantize(Decimal('1.'),rounding='ROUND_DOWN')) + 1
        result_dict['SacF'] = result_dict['FO'] - result_dict['DSacF']
        result_dict['FO'] = 0
        ordering = ['DSacF','SacF']
    elif brc in [2, 4]:
        result_dict['DFO'] = int(Decimal(result_dict['FO'] * multiplier).quantize(Decimal('1.'),rounding='ROUND_DOWN')) + 1
        result_dict['FO'] = result_dict['FO'] - result_dict['DFO']
        ordering = ['DFO','FO']
    return result_dict,ordering

def dfo_multiplier(combined):
    if combined < 10:
        multiplier = (0.08 + (combined * 0.01))
    else:
        multiplier = (-0.01 + (combined * 0.02))
    return multiplier

def go_calc(game,result_dict,go_order_dict):
    go_range = result_dict['GO']
    brc = brc_calc(game)
    lookup_val = str(brc)+'_'+str(game.Outs)
    out_dict = {}
    if go_order_dict[lookup_val] == ['FO','PO','GO','K']:
        pass
    elif brc == 1:
        if game.First_Base.Speed < 4:
            result_dict['GORA'] = int(Decimal(((0.02*game.First_Base.Speed)+0.02)*go_range).quantize(Decimal('1.'),rounding='ROUND_HALF_UP'))
        else:
            result_dict['GORA'] = int(Decimal(((0.02*game.First_Base.Speed)+0.04)*go_range).quantize(Decimal('1.'),rounding='ROUND_HALF_UP'))
        result_dict['DP'] = int(Decimal(((-0.1*game.Batter.Speed)+0.8)*go_range).quantize(Decimal('1.'),rounding='ROUND_HALF_UP'))
        result_dict['FC'] = (go_range - result_dict['GORA'] - result_dict['DP'])
    elif brc == 2 or brc == 3:
        result_dict['GORA'] = int(Decimal(((0.05*avg_speed(game))+0.1)*go_range).quantize(Decimal('1.'),rounding='ROUND_HALF_UP'))
        result_dict['GO'] = result_dict['GO'] - result_dict['GORA']
    elif brc == 4:
        # GORA
        firstb_contri = (0.02*game.First_Base.Speed)+0.02
        seconb_contri = (0.02*game.Second_Base.Speed)+0.02
        if game.First_Base.Speed > 3:
            firstb_contri += 0.02
        if game.Second_Base.Speed > 3:
            seconb_contri += 0.02
        gora_fraction = (firstb_contri + seconb_contri)/2
        result_dict['GORA'] = int(Decimal(gora_fraction * go_range).quantize(Decimal('1.'),rounding='ROUND_HALF_UP'))
        # DP
        dp_fraction = ((-0.1*game.Batter.Speed)+0.8)*1.15
        result_dict['DP21'] = int(Decimal(dp_fraction/2 * go_range).quantize(Decimal('1.'),rounding='ROUND_HALF_UP'))
        result_dict['DP31'] = result_dict['DP21']
        # FC
        result_dict['FC'] = int((result_dict['GO']-result_dict['GORA']-result_dict['DP21']*2)/2)
        result_dict['FC3rd'] = result_dict['FC']
        if game.Outs == 0:
            result_dict['DP31'] = result_dict['DP31'] - 3
            result_dict['TP'] = 3
    elif brc == 5:
        # GORA
        firstb_contri = (0.02*game.First_Base.Speed)+0.02
        thirdb_contri = (0.02*game.Third_Base.Speed)+0.02
        if game.First_Base.Speed > 3:
            firstb_contri += 0.02
        if game.Third_Base.Speed > 3:
            thirdb_contri += 0.02
        gora_fraction = (firstb_contri + thirdb_contri)/2
        result_dict['GORA'] = int(Decimal(gora_fraction * go_range).quantize(Decimal('1.'),rounding='ROUND_HALF_UP'))
        # FCH, DP21
        fchdp_fraction = ((-0.1*game.Batter.Speed)+0.8)*1.15
        result_dict['FCH'] = int(Decimal(fchdp_fraction/2 * go_range).quantize(Decimal('1.'),rounding='ROUND_HALF_UP'))
        result_dict['DP21'] = result_dict['FCH']
        # DPRun, FC
        result_dict['FC'] = int((result_dict['GO']-result_dict['GORA']-result_dict['FCH']*2)/2)
        result_dict['DPRun'] = result_dict['FC']
        if game.Outs == 1:
            result_dict['DP21'] = result_dict['DP21'] + result_dict['DPRun']
            result_dict.pop('DPRun')
    elif brc == 6:
        # GORA
        result_dict['GORA'] = int(Decimal(((0.05*avg_speed(game))+0.2)*go_range).quantize(Decimal('1.'),rounding='ROUND_DOWN'))
        result_dict['GO'] = result_dict['GO'] - result_dict['GORA']
    elif brc == 7:
        # GORA
        result_dict['GORA'] = int(Decimal(0.2*go_range).quantize(Decimal('1.'),rounding='ROUND_DOWN'))
        # FCH
        result_dict['FCH'] = int(Decimal(((-0.025*avg_speed(game))+0.225)*go_range).quantize(Decimal('1.'),rounding='ROUND_DOWN'))
        # DP
        dp_fraction = Decimal((Decimal(0.8-((-0.025*avg_speed(game))+0.225)).quantize(Decimal('1.000'),rounding='ROUND_HALF_UP'))/3).quantize(Decimal('1.00'),rounding='ROUND_HALF_UP')
        result_dict['DP21'] = int(Decimal(dp_fraction*go_range).quantize(Decimal('1.'),rounding='ROUND_HALF_UP'))
        result_dict['DP31'] = result_dict['DP21']
        result_dict['DPH1'] = result_dict['GO']-(result_dict['DP21']*2)-result_dict['GORA']-result_dict['FCH']
        if game.Outs == 0:
            result_dict['DPH1'] = result_dict['DPH1'] - 3
            result_dict['TP'] = 3

    return(result_dict)