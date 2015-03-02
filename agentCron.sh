#!/bin/bash 

# A simple script that will check if agent.py is running
# if not, it kicks it off
# Make sure a process is always running.

process='agent.py'
makerun='python /vagrant/agent.py'

if ps ax | grep -v grep | grep $process > /dev/null;
then
    exit
else
    $makerun &
fi

exit

