'''
Created on 2014 gruod. 18

@author: kestutis saldziunas
'''
import cx_Oracle as odb
from DbObjDDL import DbObjDDL
from PySVNGw import PySVNGw
import os, sys
import subprocess
 
import ConfigParser
from logger import Logger

if __name__ == '__main__':
    pass

scriptdir = os.path.dirname(os.path.realpath(__file__))
config = ConfigParser.SafeConfigParser()
config.read(os.path.join(scriptdir, '..')+'/conf/auto_oracle_vcs.cfg')
  
#Logger configuration
logger = Logger(__name__).get()

dev_mode = "DEV"

svncfg = "TRUNK_" + dev_mode
dbcfg = 'ORACLE_DB_'+ dev_mode

logger.debug('Starting sync ...')

oracle_tns = odb.makedsn(config.get(dbcfg,'ip'), config.get(dbcfg,'port'), config.get(dbcfg,'sid'))
db = odb.connect(config.get(dbcfg,'username'), config.get(dbcfg,'password'), oracle_tns)
cursor = db.cursor()

os.chdir("/home/ugnius/svn_moon/moon")

p = subprocess.Popen("svn info http://svn.int.bite.lt/svn/moon | grep \"Revision\" | awk '{print $2}'", stdout=subprocess.PIPE, shell=True)
(output, err) = p.communicate()

logger.debug('Revision is %s',output)

p = subprocess.Popen("svn update", stdout=subprocess.PIPE, shell=True)
(output, err) = p.communicate()
logger.debug('Update %s',output)

#revs = client.update(work_path)
#new_rev = revs[-1].number
#print 'updated from %s to %s.\n' % (old_rev, new_rev)

#sys.exit()

ddl = DbObjDDL(config.get(dbcfg,'username'),config.get(dbcfg,'password'),config.get(dbcfg,'ip'),config.get(dbcfg,'sid'),config.get(dbcfg,'port'))

svn = PySVNGw()

svn_comment = "<change>\n"\
    + "\t<user>TKSA</user>\n"\
    + '\t<host>jonazoliu</host>\n'\
    + '\t<ipaddr>ip</ipaddr>\n'\
    + '\t<module>sqldeveloper</module>\n'\
    + '\t<comment>initial upload</comment>\n'\
    + '</change>'
        
#sql = "select object_name, object_type, case when object_type = 'PACKAGE BODY' then 'PACKAGE_BODY' when object_type = 'PACKAGE' then 'PACKAGE_SPEC' else object_type end ddl_object_type from all_objects where owner = :arg_1 and object_type in ('TABLE','PROCEDURE','TRIGGER','SEQUENCE','PACKAGE','PACKAGE BODY','INDEX','VIEW','FUNCTION')"
# get list of objects
#cursor.execute( sql , arg_1 = schema_name)
 
rows = ddl.get_objects()  

for row in rows['row']:
    schema_name = row[0]
    object_name = row[1]
    object_type = row[2]
    ddl_object_type = row[3]
    
    sql_text = ddl.getDDL(ddl_object_type,object_name,schema_name)[3:]
    svn_file_full_name = svn.get_file_full_name(svncfg, schema_name.lower(), object_type, object_name)
    
    logger.debug('file %s',svn_file_full_name)
        
    if os.path.exists(svn_file_full_name):
        
        file_object = open(svn_file_full_name, 'r')
        svn_sql_text = file_object.read()
        if sql_text[sql_text.find('\n'):] != svn_sql_text[svn_sql_text.find('\n'):]:
            # TODO print diff
            logger.debug('not equal: %s',svn_file_full_name)
            svn.commit_file(svncfg, schema_name.lower(), object_type, object_name, sql_text, svn_comment)
    else:
        logger.debug('created %s',svn_file_full_name)
        svn.commit_file(svncfg, schema_name.lower(), object_type, object_name, sql_text, svn_comment)
            
cursor.close()
db.close()

logger.debug("Good Bye")

