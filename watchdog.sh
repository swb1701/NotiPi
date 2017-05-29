#!/bin/bash
while true; do
    /bin/sleep 120
    if [ -e "/tmp/notifier-alive" ]
    then
	/bin/rm /tmp/notifier-alive
    else
	echo "Notifier appears hung -- will kill to restart"
	/usr/bin/pkill -f "notifier.py"
    fi    
done
