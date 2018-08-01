import forecastio
from datetime import timedelta, datetime, timezone
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import rcParams as defaults
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates
import configparser
import os
import time
import io
from flask import Flask, request, render_template, send_from_directory, make_response, jsonify
from threading import Thread

app = Flask(__name__)
configLoc = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.ini')
config = configparser.ConfigParser()
config.optionxform = str
config.read(configLoc)

defaults.update({'font.size':16,
    'font.family':'sans-serif',
    'font.sans-serif':'Verdana',
    'axes.linewidth':2,
    'lines.linewidth':3})

forecast = None
sensors = {}
if config['Sensors']:
    from w1thermsensor import W1ThermSensor        

def dispUnit(measurement):
    if measurement == 'temperature':
        if config['API']['units'] == 'us':
            return u'\u00b0' + 'F'
        else:
            return u'\u00b0' + 'C' 

def formatTime(value, format='small'):
    if format == 'small':
        format = "%H:%M"
    return datetime.strftime(value, format)

app.jinja_env.filters['time'] = formatTime

def updateForecast():
    global forecast
    if forecast == None or (forecast.currently().time + timedelta(hours=forecast.offset()) < \
        datetime.now() - timedelta(minutes=int(config['API']['update-freq']))):
        print('Updating forecast from DarkSky...')
        forecast = forecastio.load_forecast(
            config['API']['api-key'], 
            config['Location']['lat'], 
            config['Location']['lon'],
            units=config['API']['units'])

def read_sensors():
    # Remove any old sensor readings
    global sensors
    for s in sensors.keys():
        if 'time' in sensors[s] and sensors[s]['time'] < \
            datetime.now() - timedelta(minutes=int(config['API']['update-freq'])):
            sensors.pop(s, None)
    for hwid in config['Sensors']:
        sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, 
            config['Sensors'][hwid])
        sensors[hwid] = {}
        sensors[hwid]['time'] = datetime.now()
        if config['API']['units'] == 'us':
            sensors[hwid]['temperature'] = sensor.get_temperature(W1ThermSensor.DEGREES_F)
        else:
            sensors[hwid]['temperature'] = sensor.get_temperature(W1ThermSensor.DEGREES_C)

@app.route('/')
def wall_clock():
    return render_template('index.html',
        precipThreshold=float(config['Display']['graph-rain-threshold']),
	      updateFreq=int(config['Display']['display-freq']))

@app.route('/precipitation')
def precipChance():
    updateForecast()
    offset = timedelta(hours=forecast.offset()) 
    hours = max(int(config['Display']['hours-graph']),
        int(config['Display']['hours-list']))
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

@app.route('/log', methods=['POST'])
def log_temperature():
    global sensors
    name = request.form['name']
    sensors[name] = {}
    sensors[name]['time'] = datetime.now()
    sensors[name]['temperature'] = float(request.form['temperature'])
    if 'humidity' in request.form:
        sensors[name]['humidity'] = float(request.form['humidity'])
    if 'pressure' in request.form:
        sensors[name]['pressure'] = float(request.form['pressure'])
    return 'ok\r\n'

@app.route('/history')
def history():
    if not 'days' in request.args:
        return render_template('history.html',
            updateFreq=int(config['Display']['display-freq']))
    log = readSensorLog(datetime.now() - timedelta(hours=request.args['days']))
    width = request.args['width']
    return history_graph(log, width)

@app.route('/currently')
def currently():
    updateForecast()
    currently = forecast.currently()
    currently.summary = 'Currently ' + currently.summary.lower() + '.'
    now = datetime.now()
    if now > now.replace(minute=0, hour=20):
        daily = forecast.daily().data[1]
        daily.summary = 'Tomorrow, ' + daily.summary.lower()
    else:
        daily = forecast.daily().data[0]
    return render_template('currently.html',
        alerts=forecast.alerts(),
        currently=currently,
        daily=daily,
        unit=dispUnit('temperature'))

@app.route('/alerts')
def alerts():
    updateForecast()
    alerts = forecast.alerts()
    return render_template('alerts.html',
        alerts=alerts)

@app.route('/sensors')
def sensorList():
    global sensors
    if config['Sensors']:
        read_sensors()
    return render_template('sensors.html',
        sensors=sensors, unit=dispUnit('temperature'))

@app.route('/hourly')
def hourly():
    updateForecast()
    fType = request.args['type']
    if fType == 'graph':
        width = int(request.args['w'])
        start = datetime.now() - timedelta(hours=2)
        end = start + timedelta(hours=int(config['Display']['hours-graph']))
        return hourly_graph(start, end, width)
    elif fType == 'list':
        start = datetime.now()
        margin = 60
        h = 69
        num = (int(request.args['h']) - margin)/h - 1
        return hourly_list(start, num)
    else:
        return 'Error'

@app.route('/daily')
def daily():
    updateForecast()

    start = datetime.now()
    end = datetime.now() + timedelta(days=int(config['Display']['days']))
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
        offset=offset,
        unit=dispUnit('temperature'))

def history_graph(log, width):
    dpi = 100
    figsize = (width / dpi, 0.3 * width / dpi)
    fg = '#cccccc'
    bg = '#000000'
    fig = Figure(figsize=figsize, dpi=dpi, facecolor=bg, frameon=False)

    taxis = fig.add_axes((0.08, 0.1, 0.84, 0.8), facecolor=bg)
    for sensor in log:
        taxis.plot(log[sensor]['time'], log[sensor]['temperature'], color=fg)
    taxis.set_ylabel('Temp (%s)' % dispUnit('temperature'), color=fg)
    taxis.xaxis.set_tick_params(color=fg, labelcolor=fg)
    taxis.yaxis.set_tick_params(color=fg, labelcolor=fg)

    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)

    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response

def hourly_graph(start, end, width):
    offset = timedelta(hours=forecast.offset())
    time = []
    temp = []
    precip = []
    hour = 0
    hf = forecast.hourly().data[hour]
    while hf.time + offset < end:
        time.append(hf.time + offset)
        temp.append(hf.temperature)
        precip.append(hf.precipProbability)
        hour += 1
        hf = forecast.hourly().data[hour]

    dpi = 100
    figsize = (width / dpi, 0.3 * width / dpi)
    fg = '#cccccc'
    bg = '#000000'
    fig = Figure(figsize=figsize, dpi=dpi, facecolor=bg, frameon=False)

    # Temperature
    taxis = fig.add_axes((0.08, 0.1, 0.84, 0.8), facecolor=bg)
    taxis.plot(time, temp, color=fg)
    taxis.set_ylabel('Temp (%s)' % dispUnit('temperature'), color=fg)
    taxis.xaxis.set_tick_params(color=fg, labelcolor=fg)
    taxis.yaxis.set_tick_params(color=fg, labelcolor=fg)

    # Precipitation
    paxis = taxis.twinx()
    fg2 = '#4082f2'
    paxis.plot(time, precip, color=fg2)
    paxis.set_ylabel('Chance (%)', color=fg2)
    paxis.xaxis.set_tick_params(color=fg2, labelcolor=fg2)
    paxis.yaxis.set_tick_params(color=fg2, labelcolor=fg2)

    paxis.spines['bottom'].set_color(fg)
    paxis.spines['left'].set_color(fg)
    paxis.spines['right'].set_color(fg)
    paxis.spines['top'].set_visible(False)

    paxis.xaxis.set_major_formatter(mdates.DateFormatter('%-I%P'))
    paxis.set_ylim([0,1])
    paxis.set_xlim([start.replace(minute=0), end.replace(minute=0)])

    xticks = [start.replace(minute=0) + timedelta(hours=x) \
        for x in range(0, int(config['Display']['hours-graph']) + 1, 2)]
    paxis.set_xticks(xticks)

    yticks = range(0, 101, 25)
    paxis.set_yticks(yticks)

    for ymaj in taxis.yaxis.get_majorticklocs():
        taxis.axhline(y=ymaj, ls='-', color='#555555', lw=0.5)

    # Annotate highs and lows
    high = max(temp)
    tHigh = time[temp.index(high)]
    if tHigh > start + timedelta(hours=1):
        taxis.annotate('%d%s' % (high, dispUnit('temperature')), xy=(tHigh, high),
            xytext=(2,4), textcoords='offset points', color=fg)
    low = min(temp)
    tLow = time[temp.index(low)]
    if tLow > start + timedelta(hours=1):
        taxis.annotate('%d%s' % (low, dispUnit('temperature')), xy=(tLow, low),
            xytext=(2,4), textcoords='offset points', color=fg)
    prec = max(precip)
    tPrec = time[precip.index(prec)]
    paxis.annotate('%d%%' % (prec * 100), xy=(tPrec, prec),
        xytext=(2,4), textcoords='offset points', color=fg2)

    # Sunset-sunrise rectangles
    day = 0
    df = forecast.daily().data[day]
    while df.time + offset < end:
        sr = mdates.date2num(df.sunriseTime + offset)
        ss = mdates.date2num(df.sunsetTime + offset)
        width = ss - sr
        ymin, ymax = taxis.get_ylim()
        height = ymax - ymin
        rect = Rectangle((sr, ymin), width, height, color='#ffff00', alpha=0.1)
        taxis.add_patch(rect)
        day += 1
        df = forecast.daily().data[day]

    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)

    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response

def hourly_list(start, num):
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
        offset=offset,
        unit=dispUnit('temperature'))


def readSensorLog(date=None):
    fileName = "logs/" + str(datetime.strftime("%m_%d_%y_", date)+ "sensors.txt")
    log = {}
    if not os.path.exists(fileName):
        return log
    with open(fileName, "r") as f:
        all_lines = f.readlines()
    for line in all_lines:
        split = line.split(',')
        if not split[0] in log:
            log[split[0]] = {}
            log[split[0]]['time'] = []
            log[split[0]]['temperature'] = []
        log[split[0]]['time'].append(datetime.strptime(split[1],"%H:%M"))
        log[split[0]]['temperature'].append(float(split[2]))
    return log

def logThread():
    while True:
        time.sleep(15*60)
        print("Logging sensor values...")
        fileName = "logs/" + str(time.strftime("%m_%d_%y_")+ "sensors.txt")
        if os.path.exists(fileName):
            f = open(fileName, "a")
        else:
            f = open(fileName, "a+")
        global sensors
        for s in sensors:
            f.write(s + "," + time.strftime("%H:%M") + "," + 
                str(round(sensors[s]['temperature'])) + "\n")
        f.close()

if __name__ == '__main__':
    logWorker = Thread(target=logThread)
    logWorker.start()
    app.run('0.0.0.0', debug=True)
    



