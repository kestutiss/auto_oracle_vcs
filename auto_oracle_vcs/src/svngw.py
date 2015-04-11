'''
Created on 2014 gruod. 12

@author: Kestutis Saldziunas
'''

import os
import ConfigParser
import subprocess

def ifnull(var, val):
    if var is None:
        return val
    
    return var

def get_file_full_name(repoType, schemaName, objectType, objectName):
    
    # Configuring
    scriptdir = os.path.dirname(os.path.realpath(__file__))
    config = ConfigParser.SafeConfigParser()
    config.read(os.path.join(scriptdir, '..')+'/conf/svn.cfg')
    
    return config.get('svn_repo_path',"TEST") + '/' + schemaName.lower() + '/' + config.get('object_local_location_path',objectType)  + '/' + objectName + '.sql'
       
def commit_file(repoType, schemaName, objectType, objectName, sqlText, comment):
    
    # Configuring
    scriptdir = os.path.dirname(os.path.realpath(__file__))
    config = ConfigParser.SafeConfigParser()
    config.read(os.path.join(scriptdir, '..')+'/conf/svn.cfg')

    addPathToSVN = None
     
    svnRepoPath = config.get('svn_repo_path',repoType)
    schemaPath = svnRepoPath + '/' +  schemaName
    packagesPath = config.get('svn_repo_path',repoType) + '/' + schemaName.lower() + '/' + 'packages'

    # TODO remove duplicate
    fileName = config.get('svn_repo_path',"TEST") + '/' + schemaName.lower() + '/' + config.get('object_local_location_path',objectType)  + '/' + objectName + '.sql'
       
    filePath = os.path.dirname(fileName)

    if not os.path.exists(schemaPath):
        addPathToSVN = schemaPath
    elif objectType.find('packages') != -1 and not os.path.exists(packagesPath):
        addPathToSVN = packagesPath
    elif not os.path.exists(filePath):
        addPathToSVN = filePath

    print "addPathToSVN: " + ifnull(addPathToSVN,'None')
    #print "scriptdir: " + scriptdir
    
    if addPathToSVN != None:  
        os.makedirs(filePath)
    
    addFileToSVN = 0
    if not os.path.exists(fileName):
        addFileToSVN = 1
    
    f = file(fileName, 'w')
    f.write(sqlText)
    f.close()    
     
    if addPathToSVN != None:    
        addPathToSVN = addPathToSVN.replace(" ", "\ ");
        cmd = "svn add " + addPathToSVN
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        print "addPathToSvn is", output
        
        #subprocess.call(["svn", "add",addPathToSVN])       
    elif addFileToSVN == 1:
        #subprocess.call(["svn", "add",fileName])    
        fileName = fileName.replace(" ", "\ ");
        cmd = "svn add " + fileName
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
            
    #subprocess.call(["svn", "commit","-m",comment]) 
    cmd = 'svn commit -m "' + comment + '"'
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()

 
        
        