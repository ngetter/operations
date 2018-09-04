# -*- coding: UTF-8 -*-
import os

###### configuration
try:
    LOCAL = os.getenv('C9_HOSTNAME')=="scheduleme-ngetter.c9users.io"# Make true if running from the IDE
    MONGO_LOCAL = LOCAL and True # Make true if running from the IDE and the mongod is running too on the local machine
    RETURN_TO = os.getenv('IP')
except Exception:
    LOCAL = False
    MONGO_LOCAL = False
    RETURN_TO = r'http://opsign.herokuapp.com'

if MONGO_LOCAL:
    MONGODB_HOST = os.getenv('IP')
    MONGODB_PORT = 27017
    MONGODB_DATABASE = 'test'
else:

    MONGODB_HOST = 'ds127928.mlab.com'
    MONGODB_PORT = 27928
    MONGODB_DATABASE = 'operations'
    MONGODB_USERNAME = 'nir'
    MONGODB_PASSWORD = '123456'

TOR_SIZE = 64

############# configuration