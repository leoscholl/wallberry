from gpiozero import MotionSensor
import subprocess
import time
import logging

def displayPower(value=None):
    if value == None:
        status = subprocess.check_output(['vcgencmd', 'display_power']).decode('utf-8')
        return int(status[status.find('=') + 1:].strip())
    subprocess.call(['vcgencmd', 'display_power', str(value)])

def reset():
    logging.info('Motion detected')
    global timeout
    displayPower(1)
    timeout = 3600

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
    level=logging.DEBUG)

if displayPower():
    timeout = 3600
else:
    timeout = -1

pir = MotionSensor(17)
pir.when_motion = reset


while True:
    if timeout == 0 and displayPower():
        logging.info('No motion for 1 hour, turning off screen')
        displayPower(0)
    time.sleep(1)
    timeout -= 1


