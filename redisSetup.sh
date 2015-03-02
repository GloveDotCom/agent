#!/bin/bash
# Author:   @JarenGlover
# Date:     Feb 21st - RIP Malcolm
# A script that will do the following
#   - Pull down and install redis
#   - Install Redis dependencies based on the vagrant box "hashicorp/precise64" : Make and tcl
#   - run make and make test
#   - start redis-server on port 8732 and bind to 0.0.0.0

function downloadRedis {
    cd $HOME
    wget http://download.redis.io/releases/redis-2.8.19.tar.gz  # grab said version of redis
    sudo apt-get -y install make tcl                            # need make and tcl to install redis
    tar xzf redis-2.8.19.tar.gz
    cd redis-2.8.19
    make

    cat >> $HOME/redis.conf <<EOF                               # create a basic redis.conf file
    # Redis configuration files

    bind 0.0.0.0
    port 8732
EOF
    sudo make test
    echo "downloaded and should be running on below info"
    cat $HOME/redis.conf
    src/redis-server $HOME/redis.conf&                          # run it

}

echo "starting to download and install Redis"
downloadRedis

