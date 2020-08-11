import time, asyncio, sys
from os import path
basedir = path.dirname(path.abspath(path.dirname(__file__)))
sys.path.insert(0,basedir)
sys.path.insert(1,path.join(basedir,"flask_app"))
from datetime import timezone
from flask_app.calculator.calculator import play_check
from models import *
from peewee import *

async def curtime():
    t = time.time()
    print(t)
    await asyncio.sleep(5)
    t2 = time.time()
    print(t2)

async def main():
    while True:
        now = time.time()
    #    PA_exp = now + (60*60*12)
        games = Games.select().where(Games.Status == 'Started').objects()
        for game in games:
            if game.PA_Timer:
                timer_exp = game.PA_Timer.replace(tzinfo=timezone.utc).timestamp() + 45
                if timer_exp < now:
                    msg = 's'
                    msg = play_check(game,auto='Pitcher')
                    print(msg)
                    print(path.dirname(__file__))
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
#    print(sys.path)
#    print(__file__)
#    print(path.dirname(__file__))
#    print(path.dirname(path.dirname(__file__)))
#    print(path.dirname(path.abspath(path.dirname(__file__))))