#!/bin/bash

# Author:   @JarenGlover
# Date:     Feb 21st - RIP Malcolm

# A script that will do the following
#   - install function
#       -   pull down git and pip
#       -   install pip & virtualenv
#   - cron function
#        - create the cron job on the node

function install {
    sudo apt-get -y install git
    cd $HOME
    wget https://bootstrap.pypa.io/get-pip.py
    sudo python get-pip.py
    sudo pip install virtualenv



    mkdir -p $HOME/agent
    virtualenv $HOME/agent/venv
    source $HOME/agent/venv/bin/activate
    pip install -r /vagrant/requirements.txt # install redis client
}

function cron {

echo "setting crontab"
FILENAME='/vagrant/agentCron.sh'

# check if cron job is installed

if crontab -l | grep $FILENAME > /dev/null;
then
    echo "cron job already installed"
    exit
else
    # adds the env related variables to make sure cron jobs runs properly
    echo "updating cron"
    echo "SHELL=/bin/bash
    HOME=/home/vagrant/
    PATH=/home/vagrant/agent/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/opt/vagrant_ruby/bin
    */2 * * * * /bin/bash /vagrant/agentCron.sh 2>> /home/vagrant/agent/cron.output"| crontab -
fi

}

# run functions
install
cron

