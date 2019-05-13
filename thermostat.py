from gpiozero import OutputDevice
from pyHS100 import Discover, SmartPlug
from datetime import datetime, timedelta
import requests
import socket
import time


class Thermostat:

    def __init__(self, hostname, port, period=1, blind=30, undershoot=0, deadzone=1):
        self.period = period # minutes
        self.blind = blind # minutes
        self.undershoot = undershoot # degrees
        self.deadzone = deadzone # degrees
        self.hostname = hostname
        self.port = port
        self.status = None
        self.climate = {}
        for c in ['temperature', 'pressure', 'humidity']:
            self.climate[c] = None

    def updateStatus(self):
        host = socket.gethostbyname(self.hostname)
        url = 'http://' + host + ':' + str(self.port) + '/thermostat?json'
        r = requests.get(url, timeout=10)
        self.status = r.json()

    def updateClimate(self):
        host = socket.gethostbyname(self.hostname)
        for c in ['temperature', 'pressure', 'humidity']:
            url = 'http://' + host + ':' + str(self.port) + '/log/' + c + '?json'
            r = requests.get(url, timeout=10)       
            self.climate[c] = r.json()

    def commandState(self, state):
        if state == True:
            print(time.strftime('%X %x %Z') + ": HVAC On")
        elif state == False:
            print(time.strftime('%X %x %Z') + ": HVAC Off")
        return

    def isExpired(self, timestamp):
        return datetime.now() - datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S') > timedelta(minutes=self.blind)

    def step(self):
        self.updateStatus()
        self.updateClimate()
        state = None
        temps = self.climate['temperature']
        sensor = next((s for s in temps if s['name'] == 'Downstairs'), None)
        if self.status == None or self.status['status'] == False:
            print(time.strftime('%X %x %Z') + ": Thermostat Off")
            state = False
        elif self.isExpired(self.status['time']) or sensor == None:
            print(time.strftime('%X %x %Z') + ": In the blind!")
            state = False
        elif sensor['value'] >= self.status['settemp']-self.undershoot:
            state = False
        elif sensor['value'] < self.status['settemp']-self.undershoot-self.deadzone:
            state = True
        self.commandState(state)

    def run(self):
        while True:
            self.step()
            time.sleep(self.period * 60)

class PassiveCoolingThermostat(Thermostat):
    def step(self):
        self.updateStatus()
        self.updateClimate()
        state = None
        temps = self.climate['temperature']
        outside = next((s for s in temps if s['name'] == 'Outside'), None)
        inside = next((s for s in temps if s['name'] == 'Downstairs'), None)
        if self.status == None or self.status['status'] == False:
            print(time.strftime('%X %x %Z') + ": Thermostat Off")
            state = False
        elif self.isExpired(self.status['time']) or inside == None or outside == None:
            print(time.strftime('%X %x %Z') + ": In the blind!")
            state = False
        elif inside['value'] <= self.status['settemp']+self.undershoot:
            state = False
        elif outside['value'] > inside['value']: # passive only
            state = False
        elif inside['value'] > self.status['settemp']+self.undershoot+self.deadzone:
            state = True
        self.commandState(state)

class RelayHeaterThermostat(Thermostat):
    def __init__(self, pin, hostname, port=5000):
        self.relay = OutputDevice(pin)
        super().__init__(hostname, port)

    def commandState(self, state):
        if state == True:
            self.relay.on()
        elif state == False:
            self.relay.off()
        super().commandState(state)

class SmartPlugFanThermostat(PassiveCoolingThermostat):
    def __init__(self, plugs, hostname, port=5000):
        self.plugs = plugs
        super().__init__(hostname, port)

    def commandState(self, state):
        for dev in self.plugs:
            if state == True:
                dev.turn_on()
            elif state == False:
                dev.turn_off()
        super().commandState(state)

if __name__ == '__main__':
    #t = RelayHeaterThermostat(18, hostname='raspberrypi.local', port=8080)
    plugs = Discover.discover().values()
    t = SmartPlugFanThermostat(plugs, hostname='raspberrypi.local', port=8080)
    t.run()


