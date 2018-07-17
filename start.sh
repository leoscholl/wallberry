#!/bin/bash
pkill chromium
sleep 30
export DISPLAY=:0
chromium-browser --kiosk --incognito http://localhost:5000 &
sleep 60
vcgencmd display_power 1

