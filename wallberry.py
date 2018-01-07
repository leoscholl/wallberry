import forecastio
from datetime import timedelta, datetime, timezone
import configparser
import os
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)
configLoc = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.ini')
config = configparser.ConfigParser()
config.optionxform = str
config.read(configLocation)

if not isempty(config['Sensors']):
    from w1thermsensor import W1TermSensor

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

@app.route('/weather')
def weather():

    # Fetch the forecast
    forecast = forecastio.load_forecast(
        config['API']['apiKey'], 
        config['Location']['lat'], 
        config['Location']['lon'],
        units=config['API']['units'])

    # Configure units
    if config['API']['units'] == 'us':
        unit = u'\u00b0' + 'F'
        thermUnit = W1ThermSensor.DEGREES_F
    else:
        unit = u'\u00b0' + 'C'
        thermUnit = W1ThermSensor.DEGREES_C

    # Read sensors
    temperature = {}
    for hwid in config['Sensors']:
        sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, 
            config['Sensors'][hwid])
        temperature[hwid] = sensor.get_temperature(thermUnit)

    # Build a list of hourly forecasts with sunrise/sunset information
    offset = timedelta(hours=forecast.offset())
    timeUpdated = forecast.currently().time + offset

    start = datetime.now()
    end = datetime.now() + timedelta(hours=int(config['Display']['hours']))

    day = 0
    hour = 0
    df = forecast.daily().data[day]
    hf = forecast.hourly().data[hour]
    data = []

    if df.sunriseTime + offset > start and \
        df.sunriseTime + offset < start + timedelta(hours=1):
        sr = {'icon' : 'sunrise',
            'summary' : 'Sunrise',
            'time' : df.sunriseTime}
        data.append(sr)
    elif df.sunsetTime + offset > start and \
        df.sunsetTime + offset < start + timedelta(hours=1):
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

    # Choose the most appropriate day for the daily forecast
    if start > start.replace(minute=0, hour=20):
        daily = forecast.daily().data[1]
        daily.summary = 'Tomorrow, ' + daily.summary.lower()
    else:
        daily = forecast.daily().data[0]

    # Modify the current conditions slightly
    currently = forecast.currently()
    currently.summary = 'Currently ' + currently.summary.lower() + '.'

    return render_template('weather.html',
        currently=currently,
        temperature=temperature, 
        daily=daily,
        hourly=data,
        offset=offset,
        unit=unit)

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)



