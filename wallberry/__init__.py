from datetime import datetime, date
import os
from flask import Flask, render_template
from flask.json import JSONEncoder

class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):
        try:
            if isinstance(obj, date):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)

def dateFmt(value, format='time'):
    if format == 'time':
        format = "%-I:%M%P"
    elif format == 'day':
        format = "%A"
    elif format == 'full':
        format = "%a %-I:%M%P"
    return datetime.strftime(value, format)

def tempFmt(value):
    return str(round(value))

def create_app(test_config=None):

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'wallberry.sqlite'),
    )
    from . import config
    app.config.from_object(config.DefaultConfig)
    if test_config is None:
        app.config.from_envvar('WALLBERRY_CONFIG')
    else:
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Add jinja2 filters
    app.jinja_env.filters['datefmt'] = dateFmt
    app.jinja_env.filters['tempfmt'] = tempFmt
    app.jinja_env.globals['TEMP_UNIT'] = u'\xb0' + \
        ('F' if app.config['UNITS'] == 'us' else 'C')

    # Apply json date encoder
    app.json_encoder = CustomJSONEncoder

    # Register blueprints
    from . import forecast, sensors, thermostat
    app.register_blueprint(forecast.bp)
    app.register_blueprint(sensors.bp)
    app.register_blueprint(thermostat.bp)

    # Define landing page route
    @app.route('/')
    def wall_clock():
        return render_template('index.html',
            precipThreshold=app.config['RAIN_THR'],
	          updateFreq=app.config['REFRESH_PERIOD'])

    # Initialize the database
    from . import db
    db.init_app(app)

    # Initialize forecast
    from . import cache
    app.forecast = cache.Forecast(app.config['API_KEY'], app.config['LATITUDE'],
        app.config['LONGITUDE'], app.config['UNITS'], app.config['UPDATE_PERIOD']*60)

    return app

    



