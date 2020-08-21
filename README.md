# MLG_app
Major League Guessball website

## Installation
```
git clone https://github.com/dyslexda/MLG.git
cd MLG
python3 -m venv mlg-env
source mlg-env/bin/activate
pip3 install -r requirements.txt
gunicorn --bind 0.0.0.0:5000 flask_app.wsgi:app
```

## Configuration
The .env file must be configured for a local branch. Add it manually to /MLG.
```
FLASK_APP=app.py
FLASK_ENV=development
SESSION_COOKIE_SECURE=True
SECRET_KEY: '' #Random string of letters and numbers
LESS_BIN=/usr/local/bin/lessc
ASSETS_DEBUG=False
LESS_RUN_IN_DEBUG=False
COMPRESSOR_DEBUG=True
CLIENT_ID: '' #The client ID for a reddit bot. 
CLIENT_SECRET: '' #The client secret for a reddit bot.
REDIRECT_URI: '' #The redirect URL for a reddit bot. When running locally, should be 'http://127.0.0.1/auth/authorize_callback'
USER_AGENT: '' #A user agent string identifying the bot to Reddit's API. Something like "MLB bot by [user]"
REFRESH_TOKEN: '' #OAuth refresh token
WEBHOOK_ID = '' #Webhook for posting to a Discord channel in order to communicate between the website and a bot
WEBHOOK_TOKEN = '' #Webhook token
DISCORD_TOKEN = '' #Discord bot token
REQ_POSITIONS = P,C,1B,2B,3B,SS,RF,CF,LF,DH
LINEUP_SIZE = 9
GAME_LENGTH = 6
```
Local branches cannot use the same bot as the master branch due to only one redirect URI being allowed (which is the IP address of the droplet). Must make a separate bot for this.
