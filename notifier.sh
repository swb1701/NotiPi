#!/bin/bash
cd /home/pi
/bin/mv -f notifier.py notifier.bkp
while true; do
/usr/bin/wget https://raw.githubusercontent.com/swb1701/NotiPi/master/notifier.py -O notifier.py
/usr/bin/python notifier.py
/bin/sleep 10
done
