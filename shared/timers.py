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
        games = Games.select().where((Games.Status == 'Started') & (Games.Situation == None)).objects()
        for game in games:
            if game.Step == 2:
                if game.Steal_Timer:
                    print('steal',game.Game_ID)
                    timer_exp = game.Steal_Timer.replace(tzinfo=timezone.utc).timestamp() + (60*30)
                    if timer_exp < now:
                        try:
                            catcher_list = List_Nums.get((List_Nums.Game_Number == game.Game_Number) &
                                                        (List_Nums.Player_ID == game.Catcher.Player_ID) &
                                                        (List_Nums.Position == 'C'))
                        except:
                            catcher_list = None
                        if catcher_list:
                            game.C_Throw = catcher_list.List[0]
                            game.save()
                            if len(catcher_list.List) > 1:
                                remaining = catcher_list.List[1:]
                                catcher_list.List = remaining
                                catcher_list.save()
                            else:
                                catcher_list.delete_instance()
                            msg = play_check(game)
                        else:
                            msg = play_check(game,auto='Catcher')
                elif game.PA_Timer and not game.Pitch and not game.Swing:
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