# sudo nohup python3 mlg_discord.py > mlg_discord.txt &
import asyncio, discord, os, sys, traceback
from os import environ, path
sys.path.insert(0,path.dirname(path.dirname(__file__)))
from dotenv import load_dotenv
from discord.ext import commands
from discord.utils import get
basedir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
load_dotenv(os.path.join(basedir, '.env'))
#Discord config
TOKEN = environ.get('DISCORD_TOKEN')

initial_extensions = [
                      'cogs.owner',
                      'cogs.dice',
                      'cogs.gametime'
                                   ]

bot = commands.Bot(command_prefix=('m!','M!'), description='MLG Discord Bot',owner_id=202278109708419072)

if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f'Failed to load extension {extension}.', file=sys.stderr)
            traceback.print_exc()

@bot.event
async def on_ready():
    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')

bot.run(TOKEN, bot=True, reconnect=True)