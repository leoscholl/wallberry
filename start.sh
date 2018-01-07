#!/bin/bash
sleep 30
export DISPLAY=:0
chromium-browser --kiosk --incognito http://localhost:5000 &
