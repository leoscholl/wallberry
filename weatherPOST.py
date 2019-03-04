from w1thermsensor import W1ThermSensor        
import requests
import socket
import time

sensors = {'Downstairs' : '01162bda03ee'}
period = 2 # minutes

def send_temps():
    for name in sensors:
        try:
            sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, 
                sensors[name])
            temperature = 9000
            while temperature > 150:
                temperature = sensor.get_temperature(W1ThermSensor.DEGREES_F)
            host = socket.gethostbyname('piclock.local')
            url = 'http://' + host + ':5000/log'
            r = requests.post(url, data={'name' : name, 'temperature' : temperature}, timeout=10)
            print(time.strftime('%X %x %Z') + ': ' + str(r.status_code))
        except Exception as err:
            print(time.strftime('%X %x %Z') + ': Exception ' + str(type(err)))
            print(err)

if __name__ == '__main__':
    while True:
        send_temps()
        time.sleep(period * 60)
