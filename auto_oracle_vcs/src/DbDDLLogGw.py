'''
Created on 2014 gruod. 12

@author: Kestutis Saldziunas
'''

from logger import Logger

       
import cx_Oracle as odb


class DbDDLLogGw(object):

    def __init__(self, userName, password, databaseName, ipAddr, port):
        self.logger = Logger(self.__class__.__name__).get() 
        
        self.databaseName = databaseName               
        oracle_tns = odb.makedsn(ipAddr, port, databaseName)
        self.__db = odb.connect(userName, password, oracle_tns)
        self.__cursor = self.__db.cursor()
 
    def __del__(self):
        self.__cursor.close()
        self.__db.close()  
        
    def commit (self,ddlID):
        
        self.__cursor.callproc("ddl_svn_mng.commit_ddl",[ddlID])
        self.__db.commit()
        
        self.logger.debug('ddl_svn_mng.commit_ddl on %d',ddlID)
        
    def setObjectDDLByID (self,ddlID):

        self.ddlID = ddlID
        
        l_obj_name = self.__cursor.var(odb.STRING)
        l_obj_schema_name = self.__cursor.var(odb.STRING)
        l_obj_type = self.__cursor.var(odb.STRING)
        l_user = self.__cursor.var(odb.STRING)
        l_module = self.__cursor.var(odb.STRING)
        l_host = self.__cursor.var(odb.STRING)
        l_ipaddr = self.__cursor.var(odb.STRING)
        
         
        l_sql_text = self.__cursor.var(odb.CLOB) 
        
        self.__cursor.callproc("ddl_svn_mng.get_ddl",[ddlID,l_obj_name,l_obj_schema_name,l_obj_type,l_user,l_module,l_host,l_ipaddr,l_sql_text])
        
        self.sqlText = str(l_sql_text.getvalue())
        self.objectName = l_obj_name.getvalue()
        self.objectSchemaName = l_obj_schema_name.getvalue().lower()
        self.objectType = l_obj_type.getvalue()   
        self.user = l_user.getvalue() 
        self.host = l_host.getvalue() 
        self.module = l_module.getvalue() 
        self.ipaddr = l_ipaddr.getvalue()
        
        self.logger.debug('ddl_svn_mng.get_ddl, %s',self.objectName)
              
    def getPendingDDLQueue (self):
        ddlq = []
        
        l_cur = self.__cursor.var(odb.CURSOR)
        l_query = self.__cursor.callproc("ddl_svn_mng.get_pending_changes",[l_cur])
        
        l_results = l_query[0]

        for row in l_results:
            ddlq.append(row[0])
        
        self.logger.debug('getPendingDDLQueue, %s',ddlq)
        
        return ddlq