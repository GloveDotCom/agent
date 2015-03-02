The idea is the Python agent will run on each individual node and communicate with the Redis data store to check if
the list of files are in sync or not.

The agent will define if the file is sync based on the below logic.
 - Check if the hash of the file on the node matches the hash in Redis
 - If no, it will check the file last modification timestamp to see if the file was updated on the node and should be
 - sync back up to the Redis or the file on the node is outdated and should be updated from the Redis data store
 - Then Sleep
 - there is a 'cron.output' file in the agent directory this is where the agent's std error output is stored

Redis Details:
A record in Redis will bet an hash data type which hold the below information
 - key: abs path where the file is stored on the node
  value:
     - hash: sha1sum hash of the file
     - encode base64 encoding of the file
     - time   the last mod time of the file
     - path   the path where the file is stored on the node

The list of files being watched are held in a set data type with a key value of "files".
 
 A set is used to store the files being watched to sysnc on the node. A second data structure was need to allow for
   more effective querying of the values. [i.e. using KEYS commands in production is no bueno]
- So when files are created they are automatically added to this set. Same goes when the file is removed. This is done
    atomically using Redis's transactions.

*Please see the open issues section on things I would improve.*

Instruction
- Run `Vagrant up` - this will take some time since it will download then install Redis, the agent, and cron job along with all its dependencies
        vagrant ssh serverX   - where X is 1,2 or 3 (server names)

Testing: To confirm that the agent actually work below are some details
 - log into a server - `cd` into the "agent" directory you will see two files, "test.txt" and "jaren.txt" - del them
   wait a a few seconds and you will see them reappear - can be done from any of the 3 nodes
 - now you can update any of the files using your favor editor - updated will replicate to other nodes
 - add a a file to be watched and sync
    - inside a node activate the python env with `source /home/vagrant/agent/venv/bin/activate`
    - create a file in a location that the user name vagrant owns (create ex: $HOME/agent/bowery)
    - cd into `/vagrant` folder start the python env by typing 'python' then type 'import redis,agent'
    - run `agent.buildHashThenUpdate(agent.REDIS, path_to_file)`
        - you can read about agent.REDIS and the function buildHashThenUpdate in their respective doc_string

    - then you can confirm the files is being watch by telnet from a node to the redis
        - telnet 10.0.0.10 8732 [from the Vagrantfile you can see Redis is hosted on port 8732 on that IP address]
    - run the command `smembers files` [the list of files being watch is stored in a set data type]
        - this will display all files currently being watched
    - run the follow command to see metadata created for the record in a hash
        - hgetall path_to_file


The agent only has to know information on where the Redis is located.

Requirements:
* Vagrant
* VirtualBox
* Please note that some IAAS compute doesn't work well with Virtualbox because of the hypervisor

