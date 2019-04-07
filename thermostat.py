from gpiozero import OutputDevice
import requests
import socket
import time

period = 1 # minutes
undershoot = 0 # degrees
deadzone = 2 # degrees
hostname = 'piclock.local'

def doSchedule():
    return True

def checkState():
    try:
        host = socket.gethostbyname(hostname)
        url = 'http://' + host + ':5000/thermostat?json'
        r = requests.get(url, timeout=10)
        thermo = r.json()
        if (not 'status' in thermo) or (not 'settemp' in thermo):
            raise ValueError('Bad response from server')
        url = 'http://' + host + ':5000/log/temperature?json'
        r = requests.get (url, timeout=10)       
        currently = r.json()
        temp = None
        for sensor in currently:
            if sensor['name'] == 'Downstairs':
                temp = sensor['value']
        if temp == None:
            print(time.strftime('%X %x %Z') + ": In the blind! Staying off")
            return False
        if temp >= settemp['value'] - undershoot:
            print(time.strftime('%X %x %Z') + ": Off...")
            return False
        if temp < settemp['value'] - undershoot - deadzone:
            print(time.strftime('%X %x %Z') + ": Heating...")
            return True
    except Exception as err:
        print(time.strftime('%X %x %Z') + ': Exception ' + str(type(err)))
        print(err)
    return None

if __name__ == '__main__':
    relay = OutputDevice(18)
    while True:
        doSchedule()
        state = checkState()
        if state == True:
            relay.on()
        if state == False:
            relay.off()
        time.sleep(period * 60)
