'''
Created on 2014 gruod. 12

@author: Kestutis Saldziunas
'''

import cx_Oracle as odb


class DbObjDDL(object):
    def __init__(self, dbUser, dbPasswd, dbIPAddress, dbSID, dbPort):
                           
        oracle_tns = odb.makedsn(dbIPAddress, dbPort, dbSID)
        self.__db = odb.connect(dbUser, dbPasswd, oracle_tns)
        self.__cursor = self.__db.cursor()
 
    def __del__(self):
        self.__cursor.close()
        self.__db.close()
              
    def getDDL (self,objType,objName,schemaName):
    
        self.__cursor.execute('select DBMS_METADATA.GET_DDL(:1,:2,:3) from dual', (objType, objName, schemaName))
        clob_res = self.__cursor.fetchall()
    
        return clob_res[0][0].read()
    
    def get_objects (self):
        
        l_cur = self.__cursor.var(odb.CURSOR)
        l_query = self.__cursor.callproc("ddl_svn_mng.get_objects",[l_cur])
        l_results = l_query[0]
        
        cursor_dict = {}
        
        for row in l_results:
            if not bool(cursor_dict):
                cursor_dict = {'row':[]} 
                  
            result = [row[0],row[1],row[2],row[3]]
            cursor_dict['row'].append(result)
        
        return cursor_dict
                
        