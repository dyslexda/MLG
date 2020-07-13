# MLG_app
Major League Guessball website

## Installation
```
git clone https://github.com/dyslexda/MLG_app.git
cd MLG_app
python3 -m venv mlg-env
source mlg-env/bin/activate
pip3 install -r requirements.txt
```

## Configuration
The .env file must be configured for a local branch.
```
'SECRET_KEY': Random string of letters and numbers
'CLIENT_ID': The client ID for a reddit bot. 
'CLIENT_SECRET': The client secret for a reddit bot.
'REDIRECT_URI': The redirect URL for a reddit bot. When running locally, should be 'http://127.0.0.1/auth/authorize_callback'
'USER_AGENT': A user agent string identifying the bot to Reddit's API. Something like "MLB bot by [user]"
```
Local branches cannot use the same bot as the master branch due to only one redirect URI being allowed (which is the IP address of the droplet). Must make a separate bot for this.
