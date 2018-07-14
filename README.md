## Synopsis

A simple, extensible web server for fetching weather and other information and displaying nicely on a screen.

![example image](https://github.com/leoscholl/wallberry/blob/master/2018-06-26-155531_1050x1680_scrot.png)

## Dependencies

* w1thermsensor
* forecastio
* python-flask
* matplotlib

## Hardware

* Raspberry pi
* DS18B20 1-wire temperature sensor (optional)

## Setup

Install:

```
git clone https://github.com/leoscholl/wallberry
sudo apt-get install python3-flask python3-matplotlib python3-w1thermsensor
sudo pip3 install python-forecastio
```

Requires a DarkSky API key (free from https://darksky.net/dev). 
Change the example config file to include your key and your location. Add addresses of any DS18B20 sensors attached through w1-gpio. Save config file as `config.ini`

If you have temperature sensors, you can set them up in one of two ways:

#### Normal mode:
Connect Vdd to 3.3v, data to gpio-4, ground to ground, pullup resistor between Vdd and data

to `/boot/config.txt` add:
```
dtoverlay=w1-gpio,gpiopin=4
``` 
4 is the default w1 gpio pin
 
to `/etc/modules` add:
```
w1-gpio
w1-therm
```

#### Parasitic mode:
Connect Vdd shorted with ground, data to gpio-4, pullup resistor between Vdd and data

to `/boot/config.txt` add:
```
dtoverlay=w1-gpio,gpiopin=4,pullup=1
``` 
 
to `/etc/modules` add:
```
w1-gpio
w1-therm strong_pullup=2
```

## Usage

Start the server on your local network by running `python3 wallberry/wallberry.py &`
Open a web browser and navigate to `localhost:5000`

For a wall-clock, use crontab and screen to automatically start on boot

```
sudo apt-get install chromium
sudo apt-get install screen
crontab -e
```
add the following:
```
@reboot /usr/bin/screen -dmS Clock /usr/bin/python3 /path/to/wallberry/wallberry.py
@reboot /bin/sh ~/wallberry/start.sh
0 7 * * * /bin/sh ~/wallberry/stop.sh
0 23 * * * /bin/sh ~/wallberry/start.sh
```
This will start a full-screen kiosk browser, and turn off the screen automatically from 11pm to 7am.
