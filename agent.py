#!/usr/bin/env python
''' ToDo:
  Add SSL http://bencane.com/2014/02/18/sending-redis-traffic-through-an-ssl-tunnel-with-stunnel/
  LOGGING - should log in redis?
'''
import redis
import os
import base64 
import time
import hashlib

# some constants for the redis data store
HOST = '10.0.0.10'
PORT = '8732'
DB = '0' 

# this is helpful for adding new files to data store
REDIS = redis.StrictRedis(host=HOST, port=PORT, db=DB)

# redis,key,hash,encode,time,path
# some test data to load into redis
TEST_1 = {'hash':'bf0a2a09e0d02546e874721e745a246c32212266', 'encode':'RmFpdGggSGVicmV3cyAK', 'time':1424396034.1868312,'path':'/home/vagrant/agent/test.txt'}
TEST = {'hash':'1617c8a29b952ec68c7de8f3b3b56f3237fc9cce', 'encode':'SWYgeW91IHJlYWRpbmcgdGhpcyBpdHMgdG9vIGxhdGUK', 'time':1424491994.6776202,'path':'/home/vagrant/agent/jaren.txt'}

# add some a binary file for testing

def getEncode(filename):
    ''' Creates a Base64 encodings of a filename

    :param filename: abs path of the file
    :return: file translated it into a radix-64 representation string
    '''

    return open(filename,"rb").read().encode("base64").replace("\n", "")


def getDecode(data):
    ''' Decodes the Base64 encoded string

    :param data: encoded string to be decoded
    :return: the decoded string
    '''
    return data.decode('base64')


def getTimestamp(filename):
    '''Returns the modification timestamp of a file

    :param filename: abs path of the file to be processed
    :return:
    '''
    # TODO: sync server with ubuntu's ntp server

    try:
        return os.path.getmtime(filename)
    except:
        return False

def getPath(filename):
    ''' Returns the abs path to a file

    :param filename: file to be processed
    :return: abs path of the file
    '''
    return os.path.abspath(filename)


def getHashFile(filename):
    ''' Creates a sha1 hash of a filename

    :param filename: abs path of file
    :return: sha1 hash of the filename
    '''
    try:
        return hashlib.sha1(open(filename).read()).hexdigest()
    except:
        return False



def getFiles(redis,key):
    ''' Return the list of values in a given key - we are using it to obtain all the files being watched

    :param redis: redis object
    :param key: the string value of the key
    :return: a dict full of the values being stored at the key
    '''
    files = redis.smembers(key)
    result = []
    for f in files:
        result.append(f)
    return result


def make_sure_path_exists(path):
    ''' Checks if path given exists then create it if it doesn't exist - MUST HAVE PERMISSION -i.e. non root

    :param path: abs path
    :return: N/A
    '''
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))




def createRecord(redis,key,value):
    ''' Create a record (hash) in Redis given a key and a value

    :param redis: redis object
    :param key: string value for key
    :param value: dic that represent the value of the hash
    :return:
    '''
    # uses a pipeline() to make sure these steps are atomic
    pipeline = redis.pipeline()
    redis.hmset(key,value)
    redis.sadd('files',value['path'])
    pipeline.execute()

def syncNode(redis,key):
    ''' Sync the node if the Redis data store has a new software version

    :param redis: redis object
    :param key: string value of the key
    :return:
    '''
    pipeline = redis.pipeline()
    decoded_file= getDecode(redis.hmget(key,'encode')[0])
    # check if director is there
    make_sure_path_exists(key)
    fHandle = open(key,'wb')
    fHandle.write(decoded_file)
    fHandle.close()
    pipeline.execute()

def deleteRecord(redis,key):
    ''' Delete a record from the Redis data store

    :param redis: redis object
    :param key: string key value of the record to delete
    :return:
    '''
    pipeline = redis.pipeline()
    redis.delete(key)
    redis.srem('files',key)   # files hash
    pipeline.execute()

def getHashOfKey(redis,key):
    ''' Return the hash field of a record in Redis

    :param redis: redis object
    :param key: string key value to the hash in question
    :return: return the 'hash' value of a given record
    '''
    return redis.hmget(key,'hash')[0] # redis returns an dic


def compareFileToHash(filename, hash):
    ''' Given a abs file path and a hash - check to see if that filename hashes to the hash in question

    :param filename: abs path of the file
    :param hash: the hash value in Redis
    :return: True if it match - False if it doesn't
    '''
    if getHashFile(filename) == hash:
        return True
    else:
        print getHashFile(filename)
        return False

def buildHashThenUpdate(redis,key):
    ''' Create the proper values for a hash record

    :param redis: redis object
    :param key: string value key which should be the abs path of the software being watched
    :return:
    '''
    pipeline = redis.pipeline()
    r_encode = getEncode(key)
    r_hash = getHashFile(key)
    r_time = getTimestamp(key)
    r_path = getPath(key)
    record = {'encode': r_encode, 'hash': r_hash, 'time':r_time,'path':r_path}
    createRecord(redis,key,record)
    pipeline.execute()

def getHash(redis,key):
    ''' Return the entire hash value of a given key value

    :param redis: redis object
    :param key: string key value
    :return: hash record of the given key from Redis
    '''
    return redis.hgetall(key)

def checkNode(redis,files_list):
    ''' Process the list of files being watched to see if the hash on current nodes match redis's hash for that file
        if it doesn't - check the timestamp to know if it should update redis or update the node

    :param redis: redis object
    :param files_list: a dictionary of files to check on
    :return:
    '''
    # loop over all files being 'watched'
    for r_file in files_list:
            remote_file = getHash(redis,r_file)

            # check the hash b/t node and redis
            if remote_file['hash'] != getHashFile(remote_file['path']):
                # check last mod date to know who has the "newest" files
                if float(remote_file['time']) > getTimestamp(remote_file['path']):
                    syncNode(redis,remote_file['path'])
                    print "sync node"
                else:
                    print "im newer"
                    buildHashThenUpdate(redis,remote_file['path'])
            else:
                print "Hash Matched Bro"

def sleep(howlong):
    ''' Sleep for X seconds

    :param howlong: time in seconds to sleep
    '''
    time.sleep(howlong)


def redisClient(host,port,db):
    ''' Create a redis client w/ the given parameters

    :param host: host of the redis server
    :param port: port redis server is listening on
    :param db: db of the redis server - mostly likely zero
    :return: a redis object
    '''

    return redis.StrictRedis(host=HOST, port=PORT, db=DB)


def main():
    ''' While loop to force the agent to sync with the redis data store every X seconds

    '''
    # SEEDS the redis server with some two files
    createRecord(redisClient(HOST,PORT,DB),TEST['path'],TEST)
    createRecord(redisClient(HOST,PORT,DB),TEST_1['path'],TEST_1)


    while (True):
        checkNode(REDIS,getFiles(REDIS,'files'))
        time.sleep(5)
        print "Just been sleeping ...zzz"

if __name__ == '__main__':
    main()
