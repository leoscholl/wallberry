from datetime import timedelta, datetime, timezone
from flask import Blueprint, request, render_template, make_response, jsonify
from flask import current_app as app
from wallberry.db import get_db
from wallberry.graphs import history_graph

bp = Blueprint('sensors', __name__, url_prefix='/log')

@bp.route('', methods=['GET', 'POST'])
def log_measurement():
    if request.method == 'GET':
        return render_template('log.html')    
    db = get_db()
    name = request.form['name']
    row = db.execute(
        'SELECT id FROM sensor WHERE name = ?', (name,)
    ).fetchone() 
    if row is None:
        db.execute(
        'INSERT INTO sensor (name) VALUES (?)', (name,))
        row = db.execute(
            'SELECT id FROM sensor WHERE name = ?', (name,)
        ).fetchone()
    id = row['id']
    if 'temperature' in request.form:
        db.execute(
            'INSERT INTO temperature (sensor_id, value) VALUES (?, ?)',
            (int(id), float(request.form['temperature'])))
    if 'humidity' in request.form:
        db.execute(
            'INSERT INTO humidity (sensor_id, value) VALUES (?, ?)',
            (int(id), float(request.form['humidity'])))
    if 'pressure' in request.form:
        db.execute(
            'INSERT INTO pressure (sensor_id, value) VALUES (?, ?)',
            (int(id), float(request.form['pressure'])))
    db.commit()
    return 'ok\r\n'

@bp.route('/temperature')
def temperature():
    db = get_db()
    readings = latestReadings(db, 'temperature')
    if 'json' in request.args:
        return jsonify(readings)
    return render_template('sensors.html',
        readings=readings)

@bp.route('/humidity')
def humidity():
    db = get_db()
    readings = latestReadings(db, 'humidity')
    if 'json' in request.args:
        return jsonify(readings)
    return render_template('sensors.html',
        readings=readings)

@bp.route('/pressure')
def pressure():
    db = get_db()
    readings = latestReadings(db, 'pressure')
    if 'json' in request.args:
        return jsonify(readings)
    return render_template('sensors.html',
        readings=readings)

@bp.route('/graph')
def graph():
    db = get_db()
    width = 800
    start = None
    end = None
    average = False
    if 'width' in request.args:
        width = int(request.args['width'])
    if 'start' in request.args:
        start = datetime.fromtimestamp(int(request.args['start']))
    if 'end' in request.args:
        end = datetime.fromtimestamp(int(request.args['end']))
    if 'average' in request.args:
        average = request.args['average'] == 'true'
    log = allReadings(db, 'temperature', average, start=start, end=end)
    if len(log) == 0:
        return ('', 204)
    image = history_graph(log, width, app.jinja_env.globals['TEMP_UNIT'])
    response = make_response(image.getvalue())
    response.mimetype = 'image/png'
    return response

def allReadings(db, table, average, start=None, end=None):
    if start == None or end == None:
        end = datetime.now()
        start = end - timedelta(hours=24)
    sensors = db.execute(
        'SELECT name, id FROM sensor'
    ).fetchall()
    readings = {}
    for i in range(len(sensors)):
        if average:
            rows = db.execute(
                'SELECT sensor_id, AVG(value) as value, DATE(time, "localtime") as date, name'
                ' FROM ' + table + ' t'
                ' JOIN sensor s ON t.sensor_id = s.id'
                ' WHERE name = ?'
                ' AND DATETIME(time, "localtime") BETWEEN ? AND ?'
                ' GROUP BY date'
                ' ORDER BY date DESC', 
                (sensors[i]['name'],start,end)
            ).fetchall()
        else:
            rows = db.execute(
                'SELECT sensor_id, value, DATETIME(time, "localtime") as time, name'
                ' FROM ' + table + ' t'
                ' JOIN sensor s ON t.sensor_id = s.id'
                ' WHERE name = ?'
                ' AND DATETIME(time, "localtime") BETWEEN ? AND ?'
                ' ORDER BY time DESC', 
                (sensors[i]['name'],start,end)
            ).fetchall()
        if len(rows) == 0:
            continue
        readings[sensors[i]['name']] = {}
        readings[sensors[i]['name']]['time'] = []
        readings[sensors[i]['name']]['value'] = []
        for j in range(len(rows)):
            if average:
                time = datetime.strptime(rows[j]['date'], '%Y-%m-%d')
            else:
                time = datetime.strptime(rows[j]['time'], '%Y-%m-%d %H:%M:%S')
            value = rows[j]['value']
            readings[sensors[i]['name']]['time'].append(time)
            readings[sensors[i]['name']]['value'].append(value)
    return readings

def latestReadings(db, table, minutes=None):
    if minutes == None:
        minutes = app.config['SENSOR_BLIND_MINUTES']
    sensors = db.execute(
        'SELECT name, id FROM sensor'
    ).fetchall()
    readings = []
    for i in range(len(sensors)):
        rows = db.execute(
            'SELECT value, name, DATETIME(time, "localtime") as time'
            ' FROM ' + table + ' t'
            ' JOIN sensor s ON t.sensor_id = s.id'
            ' WHERE name = ?'
            ' AND time > ?'
            ' ORDER BY time DESC LIMIT 1', 
            (sensors[i]['name'],datetime.now() - timedelta(minutes=minutes))
        ).fetchall()
        if not (rows == None or len(rows) == 0):
            reading = {}
            reading['name'] = sensors[i]['name']
            reading['value'] = rows[0]['value']
            reading['time'] = datetime.strptime(rows[0]['time'], '%Y-%m-%d %H:%M:%S')
            readings.append(reading)

    return readings
