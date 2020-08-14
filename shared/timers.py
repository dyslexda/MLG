import time, asyncio, sys
from os import path
basedir = path.dirname(path.abspath(path.dirname(__file__)))
sys.path.insert(0,basedir)
from datetime import timezone
from shared.calculator.calculator import play_check
from shared.models import *
from peewee import *

async def main():
    while True:
        now = time.time()
        games = Games.select().where(Games.Status == 'Started').objects()
        for game in games:
            if game.Steal_Timer:
                print('steal',game.Game_ID)
                timer_exp = game.PA_Timer.replace(tzinfo=timezone.utc).timestamp() + (60*60*10)
                if timer_exp < now:
                    msg = play_check(game,auto='Catcher10h')
            elif game.PA_Timer:
                timer_exp = game.PA_Timer.replace(tzinfo=timezone.utc).timestamp() + (60*60*12)
                if timer_exp < now:
                    if not game.Pitch:
                        print('pitcher',game.Game_ID)
                        msg = play_check(game,auto='Pitcher')
                    elif not game.Swing:
                        print('batter',game.Game_ID)
                        msg = play_check(game,auto='Batter')
        await asyncio.sleep(60*2)

if __name__ == "__main__":
    asyncio.run(main())