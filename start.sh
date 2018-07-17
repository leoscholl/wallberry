#!/bin/bash
pkill chromium
sleep 30
export DISPLAY=:0
chromium-browser --kiosk --incognito http://localhost:5000 &
sleep 30
tvservice -p
