'''
Created on 2015 bal. 1

@author: Kestutis Saldziunas
'''

import os
import logging 
import logging.handlers

#TODO import settings   # alternativly from whereever import settings  

class Logger(object):

    def __init__(self, name):
        name = name.replace('.log','')
        logger = logging.getLogger('log_namespace.%s' % name)    # log_namespace can be replaced with your namespace 
        logger.setLevel(logging.DEBUG)
        
        if not logger.handlers:
            #file_name = os.path.join(settings.LOGGING_DIR, '%s.log' % name)    # usually I keep the LOGGING_DIR defined in some global settings file
            #handler = logging.FileHandler(file_name)
            LOG_FILENAME = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')+'/logs/ora_svn.log'
            handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=20000000, backupCount=5)
            #handler = logging.FileHandler()
        
            formatter = logging.Formatter('%(asctime)s %(levelname)s:%(name)s %(message)s')
            handler.setFormatter(formatter)
            handler.setLevel(logging.DEBUG)
            logger.addHandler(handler)
        self._logger = logger


#logging.basicConfig(level=logging.DEBUG)
#logger = log.getLogger(__name__)

#formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
#logger.setLevel(logging.INFO)


    def get(self):
        return self._logger