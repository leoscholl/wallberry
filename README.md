## Synopsis

A simple, extensible web server for fetching and logging weather information and displaying nicely on a screen.

![example image](https://github.com/leoscholl/wallberry/blob/master/scrot.png)

## Dependencies

* forecastio
* python-flask
* matplotlib
* w1thermsensor (optional)

## Hardware

* Raspberry pi
* DS18B20 1-wire temperature sensor (optional)

## Setup

Install with pip and virtualenv:
```
python3 -m virtualenv ~/wallberry
source ~/wallberry/bin/activate
pip install wallberry
```

Requires a DarkSky API key (free from https://darksky.net/dev). 
Change the example config file to include your key and your location. Save config file as `config.py`

## Usage

Start the server on your local network by running `sh wallberry/server.sh &`
Open a web browser and navigate to `localhost:5000`

For a wall-clock, use crontab and screen to automatically start on boot

```
sudo apt-get install screen
crontab -e
```
add the following:
```
@reboot /usr/bin/screen -dmS Server /bin/sh ~/wallberry/server.sh
@reboot /bin/sh ~/wallberry/start.sh
0 7 * * * /bin/sh ~/wallberry/start.sh
0 23 * * * /bin/sh ~/wallberry/stop.sh
```
This will start a full-screen kiosk browser, and turn off the screen automatically from 11pm to 7am.

Included also is an example python script for a PIR motion sensor for automatically turning on and off the screen

## Adding sensors

Send temperature, humidity, and pressure data to the server with a POST requst to `/log` with the format
```
{
  name: <My Sensor Name>,
  temperature: <Temp>, (optional)
  humidity: <Humidity>, (optional)
  pressure: <Pressure> (optional)
}
```

An example script `weatherPOST.py` is included for reference using a DS18B20 sensor. To set up this sensor on a rpi:

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

Call `w1thermsensor ls` to list the hardware addresses of all connected sensors

## Viewing log history

![example log output](https://github.com/leoscholl/wallberry/blob/master/graph.png)

A GET request to `/log` yields a date range selection and simple graph
