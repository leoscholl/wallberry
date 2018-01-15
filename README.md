## Synopsis

A simple, extensible web server for fetching weather and other information and displaying nicely on a screen.

## Dependencies

* w1thermsensor
* forecastio
* python-flask
* matplotlib

## Hardware

* Raspberry pi
* DS18B20 1-wire temperature sensor (optional)

## Setup

Requires a DarkSky API key (free from https://darksky.net/dev). 
Set up the config file to include your key and your location. Add addresses of any DS18B20 sensors attached through w1-gpio. Save config file as `config.ini`

Connect the temperature sensor:

* normal mode (Vdd to 3.3v, data to gpio-4, ground to ground, pullup resistor between Vdd and data)
* parasitic mode (Vdd shorted with ground, data to gpio-4, pullup resistor between Vdd and data)

Set up the 1 wire gpio:

to `/boot/config.txt` add:

* ```dtoverlay=w1-gpio,gpiopin=4``` 4 is the default w1 gpio pin
* ```dtoverlay=w1-gpio,gpiopin=4,pullup=1``` if using parasitic mode (two wires)

to `/etc/modules` add:

```
w1-gpio
w1-therm
```

or
 
```
w1-gpio
w1-therm strong_pullup=2
```
if using parasitic mode

## Usage

Start the server on your local network by running `python wallberry.py &`
Open a web browser and navigate to `localhost:5000`

For a wall-clock, use crontab to automatically start on boot

```
@reboot /usr/bin/screen -dmS Clock /usr/bin/python3 /path/to/wallberry/wallberry.py
@reboot /bin/sh /path/to/wallberry/start.sh
0 7 * * * tvservice -p
0 23 * * * tvservice -o
```
will start a full-screen kiosk browser, and turn off the screen automatically from 11pm to 7am.
