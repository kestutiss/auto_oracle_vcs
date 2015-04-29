'''
Created on 2014 gruod. 12

@author: Kestutis Saldziunas
'''
import pysvn
import os
import ConfigParser
from logger import Logger
from settings import svncfg
#import pprint

class PySVNGw(object):
    
    def __init__(self):

        def notify(event_dict):
            self.logger.debug('svn update:')
            for k, v in event_dict.items():
            #event = event_dict.items()
                self.logger.debug('%s:%s',k,v)
            #pprint.pprint(event_dict)      
        
        def login(*args):
            return True, svncfg['USER'], svncfg['PASSWD'], False
        
        self.client = pysvn.Client()
        self.client.callback_get_login = login    
        
        self.logger = Logger(self.__class__.__name__).get() 
        
        self.client.callback_notify = notify
             
        # Configuring
        scriptdir = os.path.dirname(os.path.realpath(__file__))
        self.config = ConfigParser.SafeConfigParser()
        self.config.read(os.path.join(scriptdir, '..')+'/conf/auto_oracle_vcs.cfg')
    
    def update(self,work_path):
        self.client.update(work_path, True)
            
    def get_file_full_name(self, path, schemaName, objectType, objectName):
        return path + '/' + schemaName.lower() + '/' + self.config.get('object_local_location_path',objectType)  + '/' + objectName + '.sql'
           
    def commit_file(self, svnRepoPath, schemaName, objectType, objectName, sqlText, comment):
        
        addPathToSVN = None
         
        #svnRepoPath = self.config.get('SVN',svnTrunkType)
        schemaPath = svnRepoPath + '/' +  schemaName
        #packagesPath = self.config.get('SVN',svnTrunkType) + '/' + schemaName.lower() + '/' + 'packages'
        packagesPath = svnRepoPath + '/' + schemaName.lower() + '/' + 'packages'

        # TODO remove duplicate
        #fileName = self.config.get('SVN',svnTrunkType) + '/' + schemaName.lower() + '/' + self.config.get('object_local_location_path',objectType)  + '/' + objectName + '.sql'
        fileName = svnRepoPath + '/' + schemaName.lower() + '/' + self.config.get('object_local_location_path',objectType)  + '/' + objectName + '.sql'
        
        self.logger.debug('fileName %s',fileName)
           
        filePath = os.path.dirname(fileName)
        self.logger.debug('filePath %s',filePath)
        
        if not os.path.exists(schemaPath):
            addPathToSVN = schemaPath
        elif objectType.find('PACKAGE') != -1 and not os.path.exists(packagesPath):
            addPathToSVN = packagesPath
        elif not os.path.exists(filePath):
            addPathToSVN = filePath
            
        self.logger.debug('addPathToSVN %s',addPathToSVN)
    
        if addPathToSVN != None:  
            os.makedirs(filePath)
        
        addFileToSVN = 0
        if not os.path.exists(fileName):
            addFileToSVN = 1
            
        self.logger.debug('addFileToSVN %d',addFileToSVN)
        
        f = file(fileName, 'w')
        f.write(sqlText)
        f.close()  
        
        if addPathToSVN != None:        
            self.client.add(addPathToSVN)
            self.client.checkin([addPathToSVN], comment)
            self.logger.debug('addPathToSVN done')
        else: 
            if addFileToSVN == 1:
                self.client.add(fileName)
                self.logger.debug('addFileToSVN done')
            self.client.checkin([fileName], comment)
            self.logger.debug('checkin done')
    


 
        
        