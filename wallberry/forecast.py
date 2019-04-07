from datetime import timedelta, datetime, timezone
from flask import Blueprint, request, render_template, make_response, jsonify
from flask import current_app as app
from wallberry.graphs import hourly_graph

bp = Blueprint('forecast', __name__, url_prefix='/forecast') 

@bp.route('/precipitation')
def precipChance():
    forecast = app.forecast.get_forecast()
    offset = timedelta(hours=forecast.offset()) 
    hours = app.config['GRAPH_HOURS']
    end = datetime.now() + timedelta(hours=hours)
    maxPrecipProb = 0
    hour = 0
    hf = forecast.hourly().data[hour]
    while hf.time + offset < end:
        if hasattr(hf, 'precipProbability'):
            maxPrecipProb = max(maxPrecipProb, hf.precipProbability)
        hour += 1
        hf = forecast.hourly().data[hour]
    return jsonify(maxPrecipProb)

@bp.route('/currently')
def currently():
    forecast = app.forecast.get_forecast()
    currently = forecast.currently()
    currently.summary = 'Currently ' + currently.summary.lower() + '.'
    now = datetime.now()
    if now > now.replace(minute=0, hour=20):
        daily = forecast.daily().data[1]
        daily.summary = 'Tomorrow, ' + daily.summary.lower()
    else:
        daily = forecast.daily().data[0]
    return render_template('currently.html',
        currently=currently,
        daily=daily)

@bp.route('/alerts')
def alerts():
    forecast = app.forecast.get_forecast()
    alerts = forecast.alerts()
    filtered = {}
    offset = timedelta(hours=forecast.offset())
    for a in alerts: # TODO sometimes alerts contains an empty alert
        a.time = datetime.utcfromtimestamp(a.time) + offset
        a.expires = datetime.utcfromtimestamp(a.expires) + offset
        filtered[a.title] = a # assume alerts are sorted by date?
    return render_template('alerts.html',
        alerts=filtered.values())

@bp.route('/hourly')
def hourly():
    forecast = app.forecast.get_forecast()
    start = datetime.now()
    margin = 60
    h = 69
    num = (int(request.args['h']) - margin)/h - 1
    offset = timedelta(hours=forecast.offset())
    day = 0
    hour = 0
    df = forecast.daily().data[day]
    hf = forecast.hourly().data[hour]
    data = []

    if df.sunriseTime + offset > start and \
        df.sunriseTime + offset < start + timedelta(hours=1) and \
        df.sunriseTime < hf.time:
        sr = {'icon' : 'sunrise',
            'summary' : 'Sunrise',
            'time' : df.sunriseTime}
        data.append(sr)
    elif df.sunsetTime + offset > start and \
        df.sunsetTime + offset < start + timedelta(hours=1) and \
        df.sunsetTime < hf.time:
        ss = {'icon' : 'sunset',
            'summary' : 'Sunset',
            'time' : df.sunsetTime}
        data.append(ss)
    
    items = 0
    while items < num:
        if hf.time + offset > start:
            data.append(hf)
            items += 1
            if  items < num and df.sunriseTime > hf.time and \
                df.sunriseTime < hf.time + timedelta(hours=1):
                sr = {'icon' : 'sunrise',
                    'summary' : 'Sunrise',
                    'time' : df.sunriseTime}
                data.append(sr)
                items += 1
            elif items < num and df.sunsetTime > hf.time and \
                df.sunsetTime < hf.time + timedelta(hours=1):
                ss = {'icon' : 'sunset',
                    'summary' : 'Sunset',
                    'time' : df.sunsetTime}
                data.append(ss)
                items += 1
        hour += 1
        hf = forecast.hourly().data[hour]
        if hf.time >= forecast.daily().data[day + 1].time:
            day += 1
            df = forecast.daily().data[day]
    return render_template('hourly.html',
        data=data,
        offset=offset)

@bp.route('/graph')
def graph():
    width = int(request.args['width'])
    start = datetime.now() - timedelta(hours=1)
    image = hourly_graph(app.forecast.get_forecast(), start, 
        app.config['GRAPH_HOURS'], width, 
        app.jinja_env.globals['TEMP_UNIT'])
    response = make_response(image.getvalue())
    response.mimetype = 'image/png'
    return response

@bp.route('/daily')
def daily():
    forecast = app.forecast.get_forecast()

    start = datetime.now()
    end = start + timedelta(days=app.config['FORECAST_DAYS'])
    offset = timedelta(hours=forecast.offset())
    day = 1
    df = forecast.daily().data[day]
    data = []

    while df.time + offset < end:
        data.append(df)
        day += 1
        df = forecast.daily().data[day]

    return render_template('daily.html',
        data=data,
        offset=offset)


