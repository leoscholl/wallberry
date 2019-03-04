import forecastio
from datetime import datetime, timedelta
from flask import current_app

class Forecast:

    def __init__(self, key, lat, lon, units, refresh):
        self.forecast = None
        self.refresh = refresh
        self.key = key
        self.lat = lat
        self.lon = lon
        self.units = units

    def get_forecast(self):
        if not self.forecast == None:
            time = self.forecast.currently().time + timedelta(hours=self.forecast.offset())
            if time < datetime.now() - timedelta(seconds=self.refresh):
                self.forecast = None
        if self.forecast == None:
            current_app.logger.debug('Updating forecast from DarkSky...')
            self.forecast = forecastio.load_forecast(self.key, self.lat, self.lon, 
                units=self.units)
        return self.forecast

