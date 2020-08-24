# MLG_app
Major League Guessball demonstration website

www.majorleagueguessball.com

**Table of Contents**

 - [Key Features](#key-features)
 - [Usage](#usage)
 - [Installation](#installation)
 - [Configuration](#configuration)
 - [Launching Site](#launching-site)

## Key Features

 - Combination of Flask backend, Discord bot for pinging and receiving input, and Reddit bot for managing game threads and receiving input
 - Simultaneous pinging of both pitcher and batter, resulting in much faster play times
 - Numbers can be input through Discord DM, Reddit DM, or directly on the website (for umpires)
 - Reddit logins on the website avoid any account creation or password management
 - Both automatic and manual modes for running games, depending on umpire discretion
 - Optional writeup flavor, both for pings and results
 - Support for steals, storing and using lists (pitcher, catcher, and batter), and timers

## Usage

![Game Screen](https://i.imgur.com/NkqVBlB.png)

The basic game screen, showing teams, score, inning, game state, box score, and all plays

![Discord Ping](https://i.imgur.com/E5j0VM3.png)

Numbers can be submitted through Discord DM using the "m!" prefix.

![Reddit Ping](https://i.imgur.com/MjgWLO3.png)

![Reddit Swing](https://i.imgur.com/GMtYB8s.png)

Numbers can also be submitted through Reddit DM.

![Reddit Play](https://i.imgur.com/EqJbxME.png)

All plays are posted to Reddit and locked by the ump account (to prevent users from accidentally replying in the thread). Results are then posted as replies to that top level comment. Umps can add flavorful writeups to both pings and results.

![Umpire View](https://i.imgur.com/EricgXp.png)

One of the umpire views after numbers have come in. A Preview button shows the ranges for the matchup, and if numbers have been submitted, shows the result to aid in flavor writeups. 

![Lineup Management](https://i.imgur.com/zgex29Q.png)

Umpires can easily manage lineups, which are then reflected in the box score. 

## Installation
```
sudo apt-get -y install python3.8 python3.8-venv python3.8-dev supervisor nginx git
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 1
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 2
git clone https://github.com/dyslexda/MLG.git
cd MLG
python3 -m venv mlg-env
source mlg-env/bin/activate
pip3 install -r requirements.txt
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

## Launching Site

Depending on the hosting situation and production vs development, there are multiple ways to launch the website.

Development:
 - Directly launch from Python file for easy debugging: ```python3 flask_app/wsgi.py```
 - Launch from Gunicorn: ```gunicorn -b localhost:8000 -w 4 flask_app.wsgi:app```

Production:
Create a supervisorctl file using the following format:
```
[group:baseball]
programs=flask,reddit,discord,timers

[program:flask]
command=/home/[user]/MLG/mlg-env/bin/gunicorn -b localhost:8000 -w 4 flask_app.wsgi:app
directory=/home/[user]/MLG
user=[user]
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true

[program:reddit]
command=/home/[user]/MLG/mlg-env/bin/python3 reddit_bot/listener.py
directory=/home/[user]/MLG
user=[user]
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true

[program:discord]
command=/home/[user]/MLG/mlg-env/bin/python3 discord_bot/discord_bot.py
directory=/home/[user]/MLG
user=[user]
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true

[program:timers]
command=/home/[user]/MLG/mlg-env/bin/python3 shared/timers.py
directory=/home/[user]/MLG
user=[user]
autostart=true
autorestart=true
sopasgroup=true
killasgroup=true
```

Create an nginx configuration file in /etc/nginx/sites-available and link to sites-enabled:

```
server {
    # listen on port 80 (http)
    listen 80;
    server_name majorleagueguessball.com;
    location ~ /.well-known {
        root /home/[user]/MLG/flask_app/auth/certs;
    }
    location / {
        # redirect any requests to the same URL but on https
        return 301 https://$host$request_uri;
    }

}
server {
    # listen on port 443 (https)
    listen 443 ssl;
    server_name _;
    # location of the self-signed SSL certificate
    ssl_certificate /etc/letsencrypt/live/majorleagueguessball.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/majorleagueguessball.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
    # write access and error logs to /var/log
    access_log /var/log/baseball_access.log;
    error_log /var/log/baseball_error.log;
    location / {
        # forward application requests to the gunicorn server
        proxy_pass http://localhost:8000;
        proxy_redirect off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Launch with "sudo supervisorctl reload".
