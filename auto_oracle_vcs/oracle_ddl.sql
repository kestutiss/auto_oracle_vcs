grant select any dictionary to kestas;



CREATE OR REPLACE TRIGGER ddl_log_alter_trg BEFORE ALTER ON DATABASE
  DECLARE
  BEGIN

    IF ora_dict_obj_name IN ('DDL_LOG', 'DDL_LOG_H') OR ora_dict_obj_owner IN ('SYS') THEN
      RETURN;
    END IF;

    IF ora_dict_obj_owner IN ('LABAS') THEN
      DDL_SVN_MNG.register_ddl;
    END IF;

  END ddl_log_alter_trg;

create or replace TRIGGER ddl_log_create_trg AFTER
CREATE ON DATABASE
  DECLARE

  BEGIN
  
  if ora_dict_obj_name = 'DDL_SVN_MNG' or ora_dict_obj_owner in ('SYS') then
    return;
  end if;
  
  DDL_SVN_MNG.register_ddl;
  
  END ddl_log_create_trg;

create or replace PACKAGE ddl_svn_mng
AS
  -- pragma SERIALLY_REUSABLE;
  PROCEDURE register_ddl;

  PROCEDURE get_pending_changes (
      ddl_queue_cur OUT sys_refcursor) ;

  PROCEDURE get_objects (
      object_cur OUT sys_refcursor) ;

  PROCEDURE commit_ddl (
      p_ddl_id IN NUMBER) ;

  PROCEDURE get_ddl (
      p_ddl_id IN NUMBER,
      p_obj_name OUT VARCHAR,
      p_obj_schema_name OUT VARCHAR,
      p_obj_type OUT VARCHAR,
      p_user OUT VARCHAR,
      p_module OUT VARCHAR,
      p_host OUT VARCHAR,
      p_ipaddr OUT VARCHAR,
      p_sql_text OUT CLOB) ;

END ddl_svn_mng;

create or replace PACKAGE BODY DDL_SVN_MNG
AS
  -- pragma SERIALLY_REUSABLE;
  PROCEDURE register_ddl
  AS
    l_sql_text ora_name_list_t;
    l_stmt CLOB := '';
    n NUMBER;
    l_ddl_row ddl_log%rowtype;
    -- TODO: check coding convension
  BEGIN
    n := ora_sql_txt (l_sql_text) ;

    FOR i IN 1 .. n
    LOOP
      l_stmt := l_stmt || l_sql_text (i) ;

    END LOOP;
    l_ddl_row.CHANGED_ON := sysdate;
    -- get from sys utils get_current_dt
    l_ddl_row.OBJ_OWNER  := ora_dict_obj_owner;
    l_ddl_row.OBJ_NAME   := ora_dict_obj_name;
    l_ddl_row.SQL_TEXT   := l_stmt;
    l_ddl_row.OBJ_TYPE   := ora_dict_obj_type;
    l_ddl_row.OS_USER    := sys_context ('USERENV', 'OS_USER') ;
    l_ddl_row.HOST       := sys_context ('USERENV', 'HOST') ;
    l_ddl_row.IP_ADDRESS := sys_context ('USERENV', 'IP_ADDRESS') ;
    l_ddl_row.SYS_EVENT  := ora_sysevent;
    l_ddl_row.MODULE     := sys_context ('USERENV', 'MODULE') ;
    -- ignore objects with spec label or from ignore list table
    -- TODO: pass object if it invalid, no need to commit only distinct objects
    l_ddl_row.ddl_ID := ddl_log_seq.nextval;

    INSERT
    INTO
      ddl_log VALUES l_ddl_row;

  END register_ddl;

  PROCEDURE get_pending_changes
    (
      ddl_queue_cur OUT sys_refcursor
    )
  IS
  BEGIN
    OPEN ddl_queue_cur FOR SELECT MAX
    (
      ddl_ID
    )
    FROM ddl_log group by OBJ_NAME,
    OBJ_OWNER,
    OBJ_TYPE;

  END get_pending_changes;

  PROCEDURE get_objects
    (
      object_cur OUT sys_refcursor
    )
  IS
  BEGIN
    OPEN object_cur FOR SELECT owner,
    object_name,
    object_type,
    CASE
    WHEN object_type = 'PACKAGE BODY' THEN
      'PACKAGE_BODY'
    WHEN object_type = 'PACKAGE' THEN
      'PACKAGE_SPEC'
    ELSE
      object_type
    END ddl_object_type FROM all_objects WHERE owner = 'KESTAS' /* AND
    object_name IN
    (
      'MBUSMNG', 'MBUSU', 'MERGE_BILLING_MULTI_CHECK', 'MERGE_SMS',
      'PREPPOST_SELFCARE', 'SYNC_MERGE_BILLING_ACTIONS'
    ) */
    AND object_type IN
    (
      'TABLE', 'PROCEDURE', 'TRIGGER', 'SEQUENCE', 'PACKAGE', 'PACKAGE BODY',
      'INDEX', 'VIEW', 'FUNCTION'
    )
    ;

  END get_objects;

  PROCEDURE commit_ddl
    (
      p_ddl_id IN NUMBER
    )
  IS
    l_ddl_row ddl_log%rowtype;
  BEGIN

    SELECT
      *
    INTO
      l_ddl_row
    FROM
      ddl_log
    WHERE
      ddl_id = p_ddl_id;

    INSERT
    INTO
      ddl_log_h
    SELECT
      OBJ_OWNER,
      OBJ_NAME,
      CHANGED_ON,
      OBJ_TYPE,
      SYS_EVENT,
      OS_USER,
      HOST,
      IP_ADDRESS,
      MODULE,
      DDL_ID,
      sysdate commited_on,
      SQL_TEXT,
      FULL_SQL_TEXT
    FROM
      ddl_log
    WHERE
      ddl_id <= p_ddl_id
    AND
      obj_name = l_ddl_row.obj_name
    AND
      obj_owner = l_ddl_row.obj_owner ;

    DELETE
    FROM
      ddl_log
    WHERE
      ddl_id <= p_ddl_id
    AND
      obj_name = l_ddl_row.obj_name
    AND
      obj_owner = l_ddl_row.obj_owner ;

  END commit_ddl;

  PROCEDURE get_ddl (
      p_ddl_id IN NUMBER,
      p_obj_name OUT VARCHAR,
      p_obj_schema_name OUT VARCHAR,
      p_obj_type OUT VARCHAR,
      p_user OUT VARCHAR,
      p_module OUT VARCHAR,
      p_host OUT VARCHAR,
      p_ipaddr OUT VARCHAR,
      p_sql_text OUT CLOB)
  IS
    l_ddl_row ddl_log%rowtype;
    l_last_ddl_id ddl_log.ddl_id%type;
  BEGIN

    SELECT
      *
    INTO
      l_ddl_row
    FROM
      ddl_log
    WHERE
      ddl_id = p_ddl_id;

    -- get last change of object

    SELECT
      MAX (ddl_id)
    INTO
      l_last_ddl_id
    FROM
      ddl_log
    WHERE
      obj_name = l_ddl_row.obj_name
    AND
      obj_owner = l_ddl_row.obj_owner;

    SELECT
      *
    INTO
      l_ddl_row
    FROM
      ddl_log
    WHERE
      ddl_id = l_last_ddl_id;

    p_sql_text := l_ddl_row.sql_text ;

    IF l_ddl_row.sys_event = 'ALTER' THEN
      -- TODO beginning space to remove
      p_sql_text := DBMS_METADATA.GET_DDL (l_ddl_row.obj_type,
      l_ddl_row.obj_name, l_ddl_row.obj_owner) ;

      UPDATE
        ddl_log
      SET
        full_sql_text = p_sql_text
      WHERE
        ddl_id = l_last_ddl_id;

    END IF;

    -- tODO not needed select

    SELECT
      OBJ_NAME,
      OBJ_OWNER,
      OBJ_TYPE,
      OS_USER,
      HOST,
      MODULE,
      IP_ADDRESS
    INTO
      p_obj_name,
      p_obj_schema_name,
      p_obj_type,
      p_user,
      p_host,
      p_module,
      p_ipaddr
    FROM
      ddl_log
    WHERE
      DDL_ID = l_last_ddl_id;

  END get_ddl;

END DDL_SVN_MNG;

--------------------------------------------------------
--  DDL for Table DDL_LOG
--------------------------------------------------------

  CREATE TABLE "KESTAS"."DDL_LOG" 
   (	"OBJ_OWNER" VARCHAR2(30 BYTE), 
	"OBJ_NAME" VARCHAR2(30 BYTE), 
	"CHANGED_ON" DATE, 
	"OBJ_TYPE" VARCHAR2(100 BYTE), 
	"SYS_EVENT" VARCHAR2(100 BYTE), 
	"OS_USER" VARCHAR2(100 BYTE), 
	"HOST" VARCHAR2(100 BYTE), 
	"IP_ADDRESS" VARCHAR2(100 BYTE), 
	"MODULE" VARCHAR2(100 BYTE), 
	"DDL_ID" NUMBER(15,0), 
	"SQL_TEXT" CLOB, 
	"FULL_SQL_TEXT" CLOB
   ) SEGMENT CREATION IMMEDIATE 
  PCTFREE 10 PCTUSED 40 INITRANS 1 MAXTRANS 255 NOCOMPRESS LOGGING
  STORAGE(INITIAL 65536 NEXT 1048576 MINEXTENTS 1 MAXEXTENTS 2147483645
  PCTINCREASE 0 FREELISTS 1 FREELIST GROUPS 1 BUFFER_POOL DEFAULT FLASH_CACHE DEFAULT CELL_FLASH_CACHE DEFAULT)
  TABLESPACE "SYSTEM" 
 LOB ("SQL_TEXT") STORE AS BASICFILE (
  TABLESPACE "SYSTEM" ENABLE STORAGE IN ROW CHUNK 8192 RETENTION 
  NOCACHE LOGGING 
  STORAGE(INITIAL 65536 NEXT 1048576 MINEXTENTS 1 MAXEXTENTS 2147483645
  PCTINCREASE 0 FREELISTS 1 FREELIST GROUPS 1 BUFFER_POOL DEFAULT FLASH_CACHE DEFAULT CELL_FLASH_CACHE DEFAULT)) 
 LOB ("FULL_SQL_TEXT") STORE AS BASICFILE (
  TABLESPACE "SYSTEM" ENABLE STORAGE IN ROW CHUNK 8192 RETENTION 
  NOCACHE LOGGING 
  STORAGE(INITIAL 65536 NEXT 1048576 MINEXTENTS 1 MAXEXTENTS 2147483645
  PCTINCREASE 0 FREELISTS 1 FREELIST GROUPS 1 BUFFER_POOL DEFAULT FLASH_CACHE DEFAULT CELL_FLASH_CACHE DEFAULT)) ;

   COMMENT ON COLUMN "KESTAS"."DDL_LOG"."OBJ_OWNER" IS 'Schema name';
   COMMENT ON COLUMN "KESTAS"."DDL_LOG"."OBJ_NAME" IS 'Object name';
   COMMENT ON COLUMN "KESTAS"."DDL_LOG"."CHANGED_ON" IS 'When user did change
';
   COMMENT ON COLUMN "KESTAS"."DDL_LOG"."OBJ_TYPE" IS 'Object type (e.g. trigger)';
   COMMENT ON COLUMN "KESTAS"."DDL_LOG"."SYS_EVENT" IS 'What kind of change was?
';
   COMMENT ON COLUMN "KESTAS"."DDL_LOG"."OS_USER" IS 'User did change';
   COMMENT ON COLUMN "KESTAS"."DDL_LOG"."HOST" IS 'User did change from client host';
   COMMENT ON COLUMN "KESTAS"."DDL_LOG"."IP_ADDRESS" IS 'User did change from client host with ip address';
   COMMENT ON COLUMN "KESTAS"."DDL_LOG"."MODULE" IS 'User dd change using software';
   COMMENT ON COLUMN "KESTAS"."DDL_LOG"."DDL_ID" IS 'Change auto sequence';
   COMMENT ON COLUMN "KESTAS"."DDL_LOG"."SQL_TEXT" IS 'Posted object change';
   COMMENT ON COLUMN "KESTAS"."DDL_LOG"."FULL_SQL_TEXT" IS 'in case of alter source is taken from database';
--------------------------------------------------------
--  DDL for Index DDL_LOG_PK
--------------------------------------------------------

  CREATE UNIQUE INDEX "KESTAS"."DDL_LOG_PK" ON "KESTAS"."DDL_LOG" ("DDL_ID") 
  PCTFREE 10 INITRANS 2 MAXTRANS 255 COMPUTE STATISTICS 
  STORAGE(INITIAL 65536 NEXT 1048576 MINEXTENTS 1 MAXEXTENTS 2147483645
  PCTINCREASE 0 FREELISTS 1 FREELIST GROUPS 1 BUFFER_POOL DEFAULT FLASH_CACHE DEFAULT CELL_FLASH_CACHE DEFAULT)
  TABLESPACE "SYSTEM" ;
--------------------------------------------------------
--  Constraints for Table DDL_LOG
--------------------------------------------------------

  ALTER TABLE "KESTAS"."DDL_LOG" ADD CONSTRAINT "DDL_LOG_PK" PRIMARY KEY ("DDL_ID")
  USING INDEX PCTFREE 10 INITRANS 2 MAXTRANS 255 COMPUTE STATISTICS 
  STORAGE(INITIAL 65536 NEXT 1048576 MINEXTENTS 1 MAXEXTENTS 2147483645
  PCTINCREASE 0 FREELISTS 1 FREELIST GROUPS 1 BUFFER_POOL DEFAULT FLASH_CACHE DEFAULT CELL_FLASH_CACHE DEFAULT)
  TABLESPACE "SYSTEM"  ENABLE;
  ALTER TABLE "KESTAS"."DDL_LOG" MODIFY ("DDL_ID" NOT NULL ENABLE);

--------------------------------------------------------
--  DDL for Table DDL_LOG_H
--------------------------------------------------------

  CREATE TABLE "KESTAS"."DDL_LOG_H" 
   (	"OBJ_OWNER" VARCHAR2(30 BYTE), 
	"OBJ_NAME" VARCHAR2(30 BYTE), 
	"CHANGED_ON" VARCHAR2(30 BYTE), 
	"OBJ_TYPE" VARCHAR2(100 BYTE), 
	"SYS_EVENT" VARCHAR2(100 BYTE), 
	"OS_USER" VARCHAR2(100 BYTE), 
	"HOST" VARCHAR2(100 BYTE), 
	"IP_ADDRESS" VARCHAR2(100 BYTE), 
	"MODULE" VARCHAR2(100 BYTE), 
	"DDL_ID" NUMBER(15,0), 
	"COMMITED_ON" DATE, 
	"SQL_TEXT" CLOB, 
	"FULL_SQL_TEXT" CLOB
   ) SEGMENT CREATION IMMEDIATE 
  PCTFREE 10 PCTUSED 40 INITRANS 1 MAXTRANS 255 NOCOMPRESS LOGGING
  STORAGE(INITIAL 65536 NEXT 1048576 MINEXTENTS 1 MAXEXTENTS 2147483645
  PCTINCREASE 0 FREELISTS 1 FREELIST GROUPS 1 BUFFER_POOL DEFAULT FLASH_CACHE DEFAULT CELL_FLASH_CACHE DEFAULT)
  TABLESPACE "SYSTEM" 
 LOB ("SQL_TEXT") STORE AS BASICFILE (
  TABLESPACE "SYSTEM" ENABLE STORAGE IN ROW CHUNK 8192 RETENTION 
  NOCACHE LOGGING 
  STORAGE(INITIAL 65536 NEXT 1048576 MINEXTENTS 1 MAXEXTENTS 2147483645
  PCTINCREASE 0 FREELISTS 1 FREELIST GROUPS 1 BUFFER_POOL DEFAULT FLASH_CACHE DEFAULT CELL_FLASH_CACHE DEFAULT)) 
 LOB ("FULL_SQL_TEXT") STORE AS BASICFILE (
  TABLESPACE "SYSTEM" ENABLE STORAGE IN ROW CHUNK 8192 RETENTION 
  NOCACHE LOGGING 
  STORAGE(INITIAL 65536 NEXT 1048576 MINEXTENTS 1 MAXEXTENTS 2147483645
  PCTINCREASE 0 FREELISTS 1 FREELIST GROUPS 1 BUFFER_POOL DEFAULT FLASH_CACHE DEFAULT CELL_FLASH_CACHE DEFAULT)) ;



   CREATE SEQUENCE  "KESTAS"."DDL_LOG_SEQ"  MINVALUE 1 MAXVALUE 9999999999999999999999999999 INCREMENT BY 1 START WITH 173 CACHE 2 NOORDER  NOCYCLE ;

