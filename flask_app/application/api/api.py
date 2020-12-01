"""General page routes."""
from flask import Blueprint, render_template, g
from flask import current_app as app
from shared.api_models import *
from decimal import Decimal
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

def schedules(Team=None):
    schedules = Schedules.select()
    if Team:
        schedules = schedules.where((Schedules.Away == Team) | (Schedules.Home == Team))
    dumped = SchedulesSchema(many=True).dump(schedules)
    return(dumped)

def standings():
    return(LeagueStandings().to_dict())

class TeamStanding():
    def __init__(self, team):
        self.team = team
        self.eNumber = '0'
        self.games = Schedules.select().where((Schedules.Home == team.Abbr) | (Schedules.Away == team.Abbr)).order_by(Schedules.Game_No.asc())
        self.record()
    def record(self):
        self.pos = 0
        self.wins = 0
        self.losses = 0
        self.div_wins = 0
        self.div_losses = 0
        self.lea_wins = 0
        self.lea_losses = 0
        self.runsScored = 0
        self.runsAgainst = 0
        self.gamesBehind = 0
        for game in self.games:
            if game.Win:
                if game.Win.Abbr == self.team.Abbr:
                    self.wins += 1
                    if game.Win.Division == game.Loss.Division: self.div_wins += 1
                    if game.Win.League == game.Loss.League: self.lea_wins += 1
                elif game.Loss.Abbr == self.team.Abbr:
                    self.losses += 1
                    if game.Win.Division == game.Loss.Division: self.div_losses += 1
                    if game.Win.League == game.Loss.League: self.lea_losses += 1
            if game.A_Score != None:
                if game.Away.Abbr == self.team.Abbr:
                    self.runsScored += game.A_Score
                    self.runsAgainst += game.H_Score
                else:
                    self.runsScored += game.H_Score
                    self.runsAgainst += game.A_Score
        self.pct = str(float(Decimal(self.wins/(self.wins+self.losses)).quantize(Decimal('.001'),rounding='ROUND_HALF_UP')))
        self.runDiff = (self.runsScored - self.runsAgainst)
        last7 = self.games.where(Schedules.Situation == 'FINAL').order_by(Schedules.Game_No.desc()).limit(7)
        l3_wins,l3_losses,l5_wins,l5_losses,l7_wins,l7_losses = 0,0,0,0,0,0
        idx = 1
        for game in last7:
            if game.Win.Abbr == self.team.Abbr:
                l7_wins += 1
                if idx < 6:
                    l5_wins += 1
                if idx < 4:
                    l3_wins += 1
            else:
                l7_losses += 1
                if idx < 6:
                    l5_losses += 1
                if idx < 4:
                    l3_losses += 1
            idx += 1
        self.last3 = (str(l3_wins) + "-" + str(l3_losses))
        self.last5 = (str(l5_wins) + "-" + str(l5_losses))
        self.last7 = (str(l7_wins) + "-" + str(l7_losses))
        counter = 0
        direction = None
        gamesFinal = self.games.where(Schedules.Situation == 'FINAL').order_by(Schedules.Game_No.desc())
        for game in gamesFinal:
            if not direction:
                if game.Win.Abbr == self.team.Abbr: direction = 'W'
                else: direction = 'L'
                counter = 1
            else:
                if game.Win.Abbr == self.team.Abbr: nextdir = 'W'
                else: nextdir = 'L'
                if direction == nextdir: counter += 1
                else: break
        self.streak = direction + str(counter)
    def to_dict(self):
        return {
            'pos': self.pos,
            'teamId': self.team.TID,
            'teamName': self.team.Name,
            'teamAbbr': self.team.Abbr,
            'wins': self.wins,
            'losses': self.losses,
            'pct': self.pct,
            'gamesBehind': self.gamesBehind,
            'runsScored': self.runsScored,
            'runsAgainst': self.runsAgainst,
            'runDiff': self.runDiff,
            'streak': self.streak,
            'last3': self.last3,
            'last5': self.last5,
            'last7': self.last7,
            'eNumber': self.eNumber}

class WildCard():
    def __init__(self,teams):
        self.teams = [team['teamAbbr'] for team in teams]
        self.members = [TeamStanding(team) for team in Teams.select().where(Teams.Abbr << self.teams)]
        self.records_todict = StandingsOrder(self.members).placement()
    def to_dict(self):
        return self.records_todict


class LeagueStandings():
    def __init__(self):
        conferences_q = Teams.select(Teams.League).distinct()
        self.conferences = dict()
        self.conferences_todict = list()
        for conference in conferences_q:
            self.conferences[conference.League] = ConferenceStandings(conference.League)
            self.conferences_todict.append(self.conferences[conference.League].to_dict())
    def to_dict(self):
        return {
            'season':5,
            'standings': self.conferences_todict}

class ConferenceStandings():
    def __init__(self,name):
        self.name = name
        divisions_q = Teams.select(Teams.Division).where(Teams.League == self.name).distinct()
        self.divisions = dict()
        self.divisions_todict = list()
        self.wild_card = list()
        for division in divisions_q:
            self.divisions[division.Division] = DivisionStandings(division.Division)
            self.divisions_todict.append(self.divisions[division.Division].to_dict())
            self.wild_card.extend(self.divisions[division.Division].to_dict()['records'][1:])
        self.wildcard = WildCard(self.wild_card).to_dict()
    def to_dict(self):
        return {
            'league': self.name,
            'divisions': self.divisions_todict,
            'wildcard': self.wildcard}

class DivisionStandings():
    def __init__(self,name):
        self.name = name
        self.records = list()
        self.members = [TeamStanding(team) for team in Teams.select().where(Teams.Division == name)]
        self.records_todict = StandingsOrder(self.members).placement()
    def to_dict(self):
        return {
            'name': self.name,
            'records': self.records_todict}

class StandingsOrder():
    def __init__(self,members):
        self.members = members
        self.member_dict = dict()
        for member in self.members:
            self.member_dict[member.team.Abbr] = member
        self.order = list()
    def placement(self):
        while len(self.order) != len(self.members):
            if not self.first_wins():
                if not self.second_h2h():
                    if not self.third_divrec():
                        if not self.fourth_learec():
                            if not self.fifth_rundiff():
                                self.sixth_random()
        records_todict = list()
        for record in self.order:
            record.pos = self.order.index(record) + 1
            record.gamesBehind = (((self.order[0].wins - record.wins)+(record.losses - self.order[0].losses))/2)
            record.eNumber = 15 - self.order[0].wins - record.losses
            records_todict.append(record.to_dict())
        return(records_todict)
    def first_wins(self):
        max_wins = max(self.member_dict.items(),key=lambda x:x[1].wins)
        win_lst = [self.member_dict[team].wins for team in self.member_dict]
        if win_lst.count(max_wins[1].wins) == 1: 
            self.order.append(max_wins[1])
            del self.member_dict[max_wins[1].team.Abbr]
            return(True)
        else: return(False)
    def second_h2h(self):
        self.tied = [self.member_dict[team] for team in self.member_dict if self.member_dict[team].wins == max(self.member_dict.items(),key=lambda x:x[1].wins)[1].wins]
        tied_abbr = [team.team.Abbr for team in self.tied]
        for team in self.tied:
            final_games = [game for game in team.games if game.Win]
            team.h2h_wins = len([game for game in final_games if game.Loss.Abbr in tied_abbr if game.Win.Abbr == team.team.Abbr])
            team.h2h_losses = len([game for game in final_games if game.Win.Abbr in tied_abbr if game.Loss.Abbr == team.team.Abbr])
            try: team.h2h_perc = team.h2h_wins/(team.h2h_wins + team.h2h_losses)
            except ZeroDivisionError: 
                team.h2h_perc = 0
        max_perc = max(self.tied,key=lambda team:team.h2h_perc)
        h2h_perc_lst = [team.h2h_perc for team in self.tied]
        if h2h_perc_lst.count(max(h2h_perc_lst)) == 1:
            self.order.append(max_perc)
            del self.member_dict[max_perc.team.Abbr]
            return(True)
        else:
            self.tied = [self.member_dict[team] for team in tied_abbr if self.member_dict[team].h2h_perc == max_perc.h2h_perc]
            return(False)
    def third_divrec(self):
        max_div_wins = max(self.tied,key=lambda team:team.div_wins)
        div_win_lst = [team.div_wins for team in self.tied]
        if div_win_lst.count(max(div_win_lst)) == 1:
            self.order.append(max_div_wins)
            del self.member_dict[max_div_wins.team.Abbr]
            return(True)
        else:
            self.tied = [self.member_dict[team] for team in self.member_dict if self.member_dict[team].div_wins == max(self.member_dict.items(),key=lambda x:x[1].div_wins)[1].div_wins]
            return(False)
    def fourth_learec(self):
        max_lea_wins = max(self.tied,key=lambda team:team.lea_wins)
        lea_win_lst = [team.lea_wins for team in self.tied]
        if lea_win_lst.count(max(lea_win_lst)) == 1:
            self.order.append(max_lea_wins)
            del self.member_dict[max_lea_wins.team.Abbr]
            return(True)
        else:
            self.tied = [self.member_dict[team] for team in self.member_dict if self.member_dict[team].lea_wins == max(self.member_dict.items(),key=lambda x:x[1].lea_wins)[1].lea_wins]
            return(False)
    def fifth_rundiff(self):
        max_rundiff = max(self.tied,key=lambda team:team.runDiff)
        run_diff_lst = [team.runDiff for team in self.tied]
        if run_diff_lst.count(max(run_diff_lst)) == 1:
            self.order.append(max_rundiff)
            del self.member_dict[max_rundiff.team.Abbr]
            return(True)
        else:
            self.tied = [self.member_dict[team] for team in self.member_dict if self.member_dict[team].runDiff == max(self.member_dict.items(),key=lambda x:x[1].runDiff)[1].runDiff]
            return(False)
    def sixth_random(self):
        team = random.choice(self.tied)
        self.order.append(team)
        del self.member_dict[team.team.Abbr]