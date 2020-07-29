# start.sh
export FLASK_APP=MLG_flask
export FLASK_DEBUG=1
export APP_CONFIG_FILE=config.py
pip3 install -e .
flask run --host=0.0.0.0
