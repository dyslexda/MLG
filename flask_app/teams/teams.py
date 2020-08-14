"""General page routes."""
from flask import Blueprint, render_template, g
from flask import current_app as app
from shared.models import Teams, Players


# Blueprint Configuration
teams_bp = Blueprint(
    'teams_bp', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/teams/static/'
)



@teams_bp.route('/teams', methods=['GET'])
def teams():
    team_list = Teams.select()
    return render_template(
        'teams.html',
        team_list=team_list
    )

@teams_bp.route('/teams/<team_abbr>', methods=['GET'])
def team_page(team_abbr):
    team = Teams.get(Teams.Team_Abbr == team_abbr)
    roster = Players.select(Players,Teams).join(Teams).where(Players.Team == team_abbr)
    return render_template(
        'team_page.html',
        team = team,
        roster = roster
    )