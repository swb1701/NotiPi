#!/bin/bash
cd /home/pi
/bin/mv -f notifier.py notifier.bkp
/home/pi/watchdog.sh &
while true; do
#To use another variant of the notifier.py just swap which github routine is pulled below
/usr/bin/wget https://raw.githubusercontent.com/swb1701/NotiPi/master/notifier4.py -O notifier.py
/usr/bin/python notifier.py
/bin/sleep 10
done
