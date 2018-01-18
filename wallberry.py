import forecastio
from datetime import timedelta, datetime, timezone
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import rcParams as defaults
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates
import configparser
import os
import io
from flask import Flask, request, render_template, send_from_directory, make_response, jsonify

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

if config['Sensors']:
    from w1thermsensor import W1ThermSensor

forecast = forecastio.load_forecast(
    config['API']['apiKey'], 
    config['Location']['lat'], 
    config['Location']['lon'],
    units=config['API']['units'])

def dispUnit(measurement):
    if measurement == 'temperature':
        if config['API']['units'] == 'us':
            return u'\u00b0' + 'F'
        else:
            return u'\u00b0' + 'C' 

def updateForecast():
    offset = timedelta(hours=forecast.offset())
    if forecast.currently().time + offset < \
        datetime.now() - timedelta(minutes=int(config['API']['updateFreq'])):
        disp('Updating forecast from DarkSky...')
        forecast.update()

def read_sensors(temperature):
    for hwid in config['Sensors']:
        sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, 
            config['Sensors'][hwid])
        if config['API']['units'] == 'us':
            temperature[hwid] = sensor.get_temperature(W1ThermSensor.DEGREES_F)
        else:
            temperature[hwid] = sensor.get_temperature(W1ThermSensor.DEGREES_C)
    return temperature

@app.after_request
def add_header(response):
    response.cache_control.max_age = 0
    return response

@app.route('/temp/<path:path>')
def send_css(path):
    return send_from_directory('temp', path)

@app.route('/')
def wall_clock():
    return send_from_directory('templates', 'index.html')

@app.route('/precipitation')
def precipChance():
    updateForecast()
    offset = timedelta(hours=forecast.offset()) 
    end = datetime.now() + timedelta(hours=int(config['Display']['hours']))
    maxPrecipProb = 0
    hour = 0
    hf = forecast.hourly().data[hour]
    while hf.time + offset < end:
        if hasattr(hf, 'precipProbability'):
            maxPrecipProb = max(maxPrecipProb, hf.precipProbability)
        hour += 1
        hf = forecast.hourly().data[hour]
    return jsonify(maxPrecipProb)

@app.route('/currently')
def currently():
    temperature = {}
    if config['Sensors']:
        read_sensors(temperature)
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
        temperature=temperature,
        alerts=forecast.alerts(),
        currently=currently,
        daily=daily,
        unit=dispUnit('temperature'))

@app.route('/hourly')
def hourly():
    updateForecast()

    start = datetime.now()
    end = datetime.now() + timedelta(hours=int(config['Display']['hours']))

    fType = request.args['type']
    if fType == 'graph':
        width = int(request.args['w'])
        return hourly_graph(start, end, width)
    elif fType == 'list':
        return hourly_list(start, end)
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
    paxis.set_ylabel('Precipitation %', color=fg2)
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
        for x in range(0, int(config['Display']['hours']) + 1, 2)]
    paxis.set_xticks(xticks)

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

def hourly_list(start, end):
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

    while hf.time + offset < end:
        if hf.time + offset > start and \
            hf.time + offset < end:
            data.append(hf)
            if df.sunriseTime > hf.time and \
                df.sunriseTime < hf.time + timedelta(hours=1):
                sr = {'icon' : 'sunrise',
                    'summary' : 'Sunrise',
                    'time' : df.sunriseTime}
                data.append(sr)
            elif df.sunsetTime > hf.time and \
                df.sunsetTime < hf.time + timedelta(hours=1):
                ss = {'icon' : 'sunset',
                    'summary' : 'Sunset',
                    'time' : df.sunsetTime}
                data.append(ss)
        hour += 1
        hf = forecast.hourly().data[hour]
        if hf.time >= forecast.daily().data[day + 1].time:
            day += 1
            df = forecast.daily().data[day]

    return render_template('hourly.html',
        data=data,
        offset=offset,
        unit=dispUnit('temperature'))


if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)



