from datetime import datetime
from flask import Blueprint, request, render_template, jsonify
from flask import current_app as app
from wallberry.db import get_db

bp = Blueprint('thermostat', __name__, url_prefix='/thermostat') 

@bp.route('', methods=['GET', 'POST'])
def thermostat():
    db = get_db()
    if request.method == 'POST':
        status = request.form['status']
        settemp = request.form['settemp']
        db.execute(
        'REPLACE INTO thermostat (setting, value) VALUES (?, ?)', ('status', int(status)))
        db.execute(
        'REPLACE INTO thermostat (setting, value) VALUES (?, ?)', ('settemp', int(settemp)))
        db.commit()

    status = db.execute('SELECT value FROM thermostat WHERE setting = "status"').fetchone()
    settemp = \
        db.execute('SELECT value FROM thermostat WHERE setting = "settemp"').fetchone()
    if status == None:
        status = 0
    else:
        status = int(status['value'])
    if settemp == None:
        settemp = 65
    else:
        settemp = int(settemp['value'])
    if 'json' in request.args:
        return jsonify(time=datetime.now(),status=status,settemp=settemp)
    return render_template('thermostat.html',
        settemp=settemp, status=status, updateFreq=app.config['REFRESH_PERIOD'])

