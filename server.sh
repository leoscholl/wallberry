export FLASK_APP=wallberry
export WALLBERRY_CONFIG=$HOME/wallberry/config.py
cd $HOME/wallberry
. venv/bin/activate
flask run --host=0.0.0.0
