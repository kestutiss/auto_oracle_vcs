'''
Created on 2014 gruod. 12

@author: Kestutis Saldziunas
'''

import cx_Oracle as odb

    # TODO provide type MySQL/ Oracle implement interface accordingly


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
    
    def getObjects (self):
        ddlq = []
        
        l_cur = self.__cursor.var(odb.CURSOR)
        l_query = self.__cursor.callproc("ddl_svn_mng.get_pending_changes",[l_cur])
        
        l_results = l_query[0]

        for row in l_results:
            ddlq.append(row[0])
        
        self.logger.debug('getPendingDDLQueue, %s',ddlq)
        
        return ddlq
                
        