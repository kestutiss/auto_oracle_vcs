#!/usr/bin/env python

'''
Created on 2014 gruod. 12

@author: Kestutis Saldziunas
'''
if __name__ == '__main__':
    pass

#import getopt
import os
import sys
#import logging as log, logging.handlers
from logger import Logger
from DbDDLLogGw import DbDDLLogGw
#import svngw
from PySVNGw import PySVNGw
import datetime
import re
from settings import svncfg
 
import ConfigParser
import difflib

def nullstrip(s):
    """Return a string truncated at the first null character."""
    try:
        s = s[:s.index('\x00')]
    except ValueError:  # No nulls were found, which is okay.
        pass
    return s
    
#sys.exit(0)    
 
# Configuring
scriptdir = os.path.dirname(os.path.realpath(__file__))
config = ConfigParser.SafeConfigParser()
config.read(os.path.join(scriptdir, '..')+'/conf/auto_oracle_vcs.cfg')

#TODO do test iternation, then prod       
svn_trunk_type = 'TEST'  # todo two iterations PROD + TEST
dbcfg = 'ORACLE_DB_'+ svn_trunk_type

os.environ['ORACLE_HOME'] = config.get(dbcfg,'ORACLE_HOME')
os.environ['LD_LIBRARY_PATH'] = os.environ['ORACLE_HOME'] + "/lib"
  
#Logger configuration
logger = Logger(__name__).get()
logger.debug('Checkout SVN')

svn = PySVNGw()
svn.update(svncfg['WORK_PATH'])

# get source code   
ddl = DbDDLLogGw(config.get(dbcfg,'username'), config.get(dbcfg,'password'), config.get(dbcfg,'sid'), config.get(dbcfg,'ip'), config.get(dbcfg,'port'))
 
ddl_q = ddl.getPendingDDLQueue()

if len(ddl_q)==0:
    logger.debug("exit, queue is empty")
    sys.exit(0)

for i in ddl_q:
    # get source, type, obj_name to commit
    ddl.setObjectDDLByID(i)
    
    logger.debug("object to process: %d %s", i, ddl.objectName)
    
    comment = "auto commit - no comment was found"
    
    today = datetime.date.today()
    today_str =  today.strftime('%Y-%m-%d')
    
    m = re.search('MODIFICATION.*HISTORY.*' + today_str + '(.*?)\n', ddl.sqlText, re.DOTALL)
    
    if m != None:
        comment = m.group(1)
    
    svn_comment = "<change>\n<user>%s</user>\n<host>%s</host>\n<ipaddr>%s</ipaddr>\n<module>%s</module>\n<comment>%s</comment>\n</change>" % (ddl.user, ddl.host, ddl.ipaddr, ddl.module,comment.strip())
        
    logger.debug("svn_comment:\n" + svn_comment)
    
    svn_file_full_name = svn.get_file_full_name('TRUNK_'+svn_trunk_type, ddl.objectSchemaName.lower(), ddl.objectType, ddl.objectName)
    logger.debug("full path to file: " + svn_file_full_name)
        
    if os.path.exists(svn_file_full_name):    
        file_object = open(svn_file_full_name, 'r')
        svn_sql_text = file_object.read()
        diff = difflib.context_diff(svn_sql_text, nullstrip(ddl.sqlText))
        logger.debug("diff: " + ''.join(diff),)
    else:
        logger.debug("file is new:" + svn_file_full_name)

    svn.commit_file('TRUNK_'+svn_trunk_type, ddl.objectSchemaName, ddl.objectType, ddl.objectName, nullstrip(ddl.sqlText), svn_comment)
    
    ddl.commit(ddl.ddlID);    
    logger.debug("svn commits done, exit") 
    