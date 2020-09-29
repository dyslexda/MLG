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
    stat_diff = (int(b) - int(p))
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
        runner = game.First_Base
    elif game.Runner == 2:
        base = '3'
        runner = game.Second_Base
    elif game.Runner == 3:
        base = '4'
        runner = game.Third_Base
    battery = int(Decimal((game.Pitcher.Awareness + game.Catcher.Eye)/2).quantize(Decimal('1.'), rounding='ROUND_DOWN'))
    matchup = runner.Speed - battery
    steal_range = steal_dict[base][matchup]
    if int(diff) <= int(steal_range):
        result = 'SB'+base
    else:
        result = 'CS'+base
    return(result,runner)

def calc_ranges(obr_dict,modifiers_dict,pitcher,batter,handedness):
    # First get overall raw base hit range from Contact vs Movement
    raw_base_hit = obr_dict['HIT'][handedness][stat_checker(batter.Contact,pitcher.Movement)]
    # There is a Speed vs Awareness modifier to help make the two attributes more valuable
    mod_SvA = modifiers_dict['SvA'][stat_checker(batter.Speed,pitcher.Awareness)]
    # There is a small, flat Awareness modifier to make Awareness more valuable
    mod_PitAwa = modifiers_dict['PitAwa'][pitcher.Awareness]
    final_base_hit = raw_base_hit + mod_SvA + mod_PitAwa
    # Get individual ranges for HR, 3B, 2B, IF1B, BB
    range_hr = obr_dict['HR'][handedness][stat_checker(batter.Power,pitcher.Velocity)]
    range_3b = obr_dict['3B'][handedness][stat_checker(batter.Speed,pitcher.Awareness)]
    range_2b = obr_dict['2B'][handedness][stat_checker(batter.Speed,pitcher.Awareness)]
    range_if1b = obr_dict['IF1B'][handedness][stat_checker(batter.Speed,pitcher.Awareness)]
    range_bb = obr_dict['BB'][handedness][stat_checker(batter.Eye,pitcher.Command)]
    # 1B range is the remainder of the final base hit range (plus five)
    range_1b = (final_base_hit - range_hr - range_3b - range_2b) + 5
    range_on_base = range_hr + range_3b + range_2b + range_if1b + range_bb + range_1b - 1
    # Complicated formulas for PO and FO, but basically it's a percentage of the remaining range based on Power vs Velocity
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

def bunt_calc(game,result_dict,bunt_dict):
    brc = brc_calc(game)
    bunt_result_dict = {}
    contact_range = result_dict['On Base'] - result_dict['BB']
    in_play_out_range = 500 - result_dict['On Base'] - result_dict['K']
    bunt_result_dict['1BWH'] = 10
    bunt_multiplier = bunt_dict['B1B'][int(game.Batter.Speed - game.Pitcher.Movement)]
    bunt_result_dict['B1B'] = int(Decimal(contact_range * bunt_multiplier).quantize(Decimal('1.'),rounding='ROUND_HALF_UP')) - 9
    bunt_result_dict['BB'] = result_dict['BB']
    bunt_result_dict['K'] = result_dict['K']
    ordering = ['1BWH','B1B','BB','SacB','BFC','K','BDP']
    if brc == 0:
        ordering = ['1BWH','B1B','BB','BGO','K']
        bunt_result_dict['BGO'] = in_play_out_range
        return(bunt_result_dict,ordering)
    elif brc == 1:
        runner_matchup = int((game.First_Base.Speed - game.Pitcher.Awareness))
        base = '2'
    elif brc in [2,4]:
        runner_matchup = int((game.Second_Base.Speed - game.Pitcher.Awareness))
        base = '3'
    elif brc in [3,5,7]:
        runner_matchup = int((game.Third_Base.Speed - game.Pitcher.Awareness))
        base = 'H'
    lead_multiplier = bunt_dict[base][runner_matchup]
    dp_multiplier = bunt_dict['DP'][runner_matchup]
    bunt_result_dict['SacB'] = int(Decimal(in_play_out_range * lead_multiplier).quantize(Decimal('1.'),rounding='ROUND_HALF_UP'))
    bunt_result_dict['BDP'] = int(Decimal(in_play_out_range * dp_multiplier).quantize(Decimal('1.'),rounding='ROUND_HALF_UP'))
    bunt_result_dict['BFC'] = in_play_out_range - bunt_result_dict['SacB'] - bunt_result_dict['BDP']
    return(bunt_result_dict,ordering)

#def bunt_calc(game,result_dict,bunt_dict):
#    brc = brc_calc(game)
#    bunt_result_dict = {}
#    contact_range = result_dict['On Base'] - result_dict['BB']
#    in_play_out_range = 500 - result_dict['On Base'] - result_dict['K']
#    bunt_result_dict['BBOY'] = 10
#    bunt_result_dict['IF1B'] = contact_range - bunt_result_dict['BBOY']
#    bunt_result_dict['BB'] = result_dict['BB']
#    bunt_result_dict['K'] = result_dict['K']
#    if brc == 0:
#        ordering = ['BBOY','IF1B','BB','GO','K']
#    elif brc == 1:
#        first_matchup = int((game.First_Base.Speed - game.Pitcher.Awareness))
#        ordering = ['BBOY','IF1B','BB','SacB','FC','K','DP']
#        bunt_result_dict['SacB'] = int(Decimal(bunt_dict['2'][first_matchup] * in_play_out_range).quantize(Decimal('1.'),rounding='ROUND_HALF_UP')) + 1
#        bunt_result_dict['DP'] = int(Decimal(bunt_dict['DP'][first_matchup] * in_play_out_range).quantize(Decimal('1.'),rounding='ROUND_HALF_UP')) + 1
#        bunt_result_dict['FC'] = in_play_out_range - bunt_result_dict['SacB'] - bunt_result_dict['DP']
#    elif brc == 2:
#        second_matchup = int((game.Second_Base.Speed - game.Pitcher.Awareness))
#        ordering = ['BBOY','IF1B','BB','SacB','FC3rd','K']
#        bunt_result_dict['SacB'] = int(Decimal(bunt_dict['3'][second_matchup] * in_play_out_range).quantize(Decimal('1.'),rounding='ROUND_HALF_UP')) + 1
#        bunt_result_dict['FC3rd'] = in_play_out_range - bunt_result_dict['SacB']
#    elif brc == 3:
#        third_matchup = int((game.Third_Base.Speed - game.Pitcher.Awareness))
#        ordering = ['BBOY','IF1B','BB','SacB','FCH','K']
#        bunt_result_dict['SacB'] = int(Decimal(bunt_dict['H'][third_matchup] * in_play_out_range).quantize(Decimal('1.'),rounding='ROUND_HALF_UP')) + 1
#        bunt_result_dict['FCH'] = in_play_out_range - bunt_result_dict['SacB']
#    elif brc == 4:
#        first_matchup = int((game.First_Base.Speed - game.Pitcher.Awareness))
#        second_matchup = int((game.Second_Base.Speed - game.Pitcher.Awareness))
#        second_safe = int(Decimal(bunt_dict['2'][first_matchup] * in_play_out_range).quantize(Decimal('1.'),rounding='ROUND_HALF_UP')) + 1
#        third_safe = int(Decimal(bunt_dict['3'][second_matchup] * in_play_out_range).quantize(Decimal('1.'),rounding='ROUND_HALF_UP')) + 1
#        if second_safe > third_safe:
#            ordering = ['BBOY','IF1B','BB','SacB','FC3rd','K','DP31']
#            bunt_result_dict['SacB'] = third_safe
#            bunt_result_dict['DP31'] = int(Decimal(bunt_dict['DP'][second_matchup] * in_play_out_range).quantize(Decimal('1.'),rounding='ROUND_HALF_UP')) + 1
#            bunt_result_dict['FC3rd'] = in_play_out_range - bunt_result_dict['SacB'] - bunt_result_dict['DP31']
#        else:
#            ordering = ['BBOY','IF1B','BB','SacB','FC','K','DP21']
#            bunt_result_dict['SacB'] = second_safe
#            bunt_result_dict['DP21'] = int(Decimal(bunt_dict['DP'][first_matchup] * in_play_out_range).quantize(Decimal('1.'),rounding='ROUND_HALF_UP')) + 1
#            bunt_result_dict['FC'] = in_play_out_range - bunt_result_dict['SacB'] - bunt_result_dict['DP21']
#    elif brc == 5:
#        first_matchup = int((game.First_Base.Speed - game.Pitcher.Awareness))
#        third_matchup = int((game.Third_Base.Speed - game.Pitcher.Awareness))
#        second_safe = int(Decimal(bunt_dict['2'][first_matchup] * in_play_out_range).quantize(Decimal('1.'),rounding='ROUND_HALF_UP')) + 1
#        home_safe = int(Decimal(bunt_dict['H'][third_matchup] * in_play_out_range).quantize(Decimal('1.'),rounding='ROUND_HALF_UP')) + 1
#        if second_safe > home_safe:
#            ordering = ['BBOY','IF1B','BB','SacB','FCH','K','DP21']
#            bunt_result_dict['SacB'] = second_safe
#            bunt_result_dict['DP21'] = int(Decimal(bunt_dict['DP'][first_matchup] * in_play_out_range).quantize(Decimal('1.'),rounding='ROUND_HALF_UP')) + 1
#            bunt_result_dict['FCH'] = in_play_out_range - bunt_result_dict['SacB'] - bunt_result_dict['DP31']



def wh_calc(game,result_dict):
    brc = brc_calc(game)
    if brc in [4,7]:
        if game.Second_Base.Speed > game.First_Base.Speed:
            lead_speed = game.Second_Base.Speed
            lagg_speed = game.First_Base.Speed
            lead_multiplier = wh_multiplier(lead_speed,game)
            lagg_multiplier = wh_multiplier(lagg_speed,game)
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
            lead_multiplier = wh_multiplier(lead_speed,game)
            range_1bwh = int(Decimal(lead_multiplier * result_dict['1B']).quantize(Decimal('1.'),rounding='ROUND_DOWN')) + 1
            range_2bwh = int(Decimal(lead_multiplier * result_dict['2B']).quantize(Decimal('1.'),rounding='ROUND_DOWN')) + 1
            result_dict['1BWH'] = int(range_1bwh)
            result_dict['2BWH'] = int(range_2bwh)
            result_dict['2B'] = result_dict['2B'] - result_dict['2BWH']
            result_dict['1B'] = result_dict['1B'] - result_dict['1BWH']
            ordering = ['HR','3B','2BWH','2B','1BWH','1B','IF1B','BB']
    elif brc in [2,6]:
        lead_speed = game.Second_Base.Speed
        lead_multiplier = wh_multiplier(lead_speed,game)
        range_1bwh = int(Decimal(lead_multiplier * result_dict['1B']).quantize(Decimal('1.'),rounding='ROUND_DOWN')) + 1
        result_dict['1BWH'] = int(range_1bwh)
        result_dict['1B'] = result_dict['1B'] - result_dict['1BWH']
        ordering = ['HR','3B','2B','1BWH','1B','IF1B','BB']
    else:
        if game.Second_Base != None:
            lead_speed = game.Second_Base.Speed
        else:
            lead_speed = game.First_Base.Speed
        lead_multiplier = wh_multiplier(lead_speed,game)
        range_1bwh = int(Decimal(lead_multiplier * result_dict['1B']).quantize(Decimal('1.'),rounding='ROUND_DOWN')) + 1
        range_2bwh = int(Decimal(lead_multiplier * result_dict['2B']).quantize(Decimal('1.'),rounding='ROUND_DOWN')) + 1
        result_dict['2BWH'] = int(range_2bwh)
        result_dict['1BWH'] = int(range_1bwh)
        result_dict['2B'] = result_dict['2B'] - result_dict['2BWH']
        result_dict['1B'] = result_dict['1B'] - result_dict['1BWH']
        ordering = ['HR','3B','2BWH','2B','1BWH','1B','IF1B','BB']
    return result_dict,ordering

def wh_multiplier(speed,game):
    if speed > 2:
        multiplier = -0.06 + (speed * 0.07)
    else:
        multiplier = 0.045 + (speed * 0.035)
    if game.Outs == 2:
        multiplier = multiplier * 3
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
#        result_dict['DP31'] = result_dict['DP21']
        # FC
        result_dict['FC'] = int((result_dict['GO']-result_dict['GORA']-result_dict['DP21']*2)/2)
        result_dict['FC3rd'] = result_dict['FC']
        # DP31 takes any remaining numbers after rounding
        result_dict['DP31'] = int(result_dict['GO']-result_dict['GORA']-result_dict['DP21']-result_dict['FC']*2)
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