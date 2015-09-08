## sets up a context-managed database connection

import psycopg2
import contextlib
from sqlalchemy import create_engine
from util import cred
import pandas as pd


# set up a context manager for the database
# NOTE: THIS WILL NOT CLOSE THE CURSOR, YOU NEED TO HANDLE THIS ON YOUR OWN

@contextlib.contextmanager
def connect_to_db(host, username, pword, dbname):

	try:
		conn = psycopg2.connect(host = host, user = username,
								password = pword, dbname = dbname)

		yield conn

	except Exception as e:
		conn.rollback()
		raise e

	finally: 
		conn.close()




def tableExists(cursor, tablename='schools', tableschema='college_persistence'):
	'''
	@description: Small helper to check if a table of a given name already exists in db.
	@param cursor: cursor to postgres db from psycopg2
	@param tablename: name of the table to check for
	@param tableschame: name of the schema to check for
	'''
	cursor.execute("select exists(select * from information_schema.tables where table_schema=%s and table_name=%s)", (tableschema, tablename,))
	return (True if cursor.fetchone()[0] else False)


def dropTable(cursor,tablename='schools',tableschema='college_persistence'):
	'''
	@description: Drop table of a given name from postgresql db.
	@raises IOError: If the table doesn't exist, throws an exception.
	'''
	if not tableExists(cursor,tablename, tableschema):
		raise IOError("Table '%s' can't be dropped as it doesn't exist."%tablename)
	cursor.execute('drop table %s.%s;'%(tableschema, tablename))
	cursor.connection.commit()


def populateTable(df, tablename='schools', tableschema='college_persistence',
				dialect = 'postgresql', if_exists='append', index=False, **kwargs):
	'''
	@description: Pushes a dataframe to our postgresql db.
	@param df: Dataframe to be pushed.
	@param tablename: name for the table in the db
	@param dialect: dialect of the SQLAlchemy engine that connects to our db
	@param if_exists: {'fail', 'replace', 'append'} passed to Panda's to_sql function,
					  defines what to do if the table already exists.
	@param index: passed to Panda's to_sql function (sets if the dataframe's index becomes a column)
	@param kwargs: dictionary of parameters, gets passed to Panda's to_sql function.
	'''

	engine = create_engine(dialect + '://' + cred.user + 
		':' + cred.pw + '@' + cred.host + '/' + cred.user)

	df.to_sql(name=tablename, con=engine, if_exists=if_exists, schema=tableschema,
				index=index, **kwargs)



def list_SQLcolumn_names(table):

    schemaname, tablename = table.split('.')

    # Write SQL command to string
    cmd_fetchcols = '''
    SELECT column_name
    FROM information_schema.columns
      WHERE table_name = \'''' + tablename + '''\'
      AND table_schema = \'''' + schemaname + '\';'

    # Execute the SQL command
    with connect_to_db(cred.host, cred.user, cred.pw, cred.dbname) as conn: # use context managed db connection
        with conn.cursor() as cur:

            cur.execute(cmd_fetchcols)
            sqlreturn = cur.fetchall()

    # Return list of strings (instead of list of tuples with 1 string in each)
    return [x[0] for x in sqlreturn]


def copyTempTableToSQL(sqlcmd,cleandf,cleancsv,tablename):
    ## Connect to the database; create the SQL table and load the data into it

    with connect_to_db(cred.host, cred.user, cred.pw, cred.dbname) as conn: # use context managed db connection
        with conn.cursor() as cur:

            # create the temporary table
            cur.execute(sqlcmd)

            # load the table with data from cleaned CSV
            with open(cleancsv,"r") as f:
                cur.copy_from(f, tablename, sep=',', null = 'NaN', columns = list(cleandf.columns.values))
            conn.commit()

            # XX need to perform join with studentid table
            print 'Successfully loaded temp data to SQL.'

def joinTempToId(temptable,temptable_joinid,idtable,idtable_joinid,createtable):

    # prepare the join SQL command
    colnames = list_SQLcolumn_names(temptable)
    colselect = ', '.join( [temptable+'.'+col for col in colnames if col not in temptable_joinid] )

    cmd_joinanddrop = 'DROP TABLE IF EXISTS ' + createtable + ''';

    CREATE TABLE ''' + createtable + ''' AS
      SELECT ''' + idtable + '.id' + ', ' + colselect + '''
        FROM ''' + idtable + ' RIGHT JOIN ' + temptable + '''
          ON ''' + idtable + '.' + idtable_joinid + '=' + temptable + '.' + temptable_joinid + ''';

    DROP TABLE ''' + temptable + ';'

    # perform the join
    with connect_to_db(cred.host, cred.user, cred.pw, cred.dbname) as conn: # use context managed db connection
        with conn.cursor() as cur:

            # create the permanent table & drop temporary table
            cur.execute(cmd_joinanddrop)

            # commit the change to the database
            conn.commit()
            print 'Successfully joined temp data to id, creating permanent SQL table.'

def addDataColumnToTable(df, columns_added, constraints_added, target_table, join_col, target_schema = 'college_persistence'):
    # alter the table to include the relevant new columns
    columns_with_constraints = zip(columns_added, constraints_added)
    alter_query = 'ALTER TABLE schoolid ' + ','.join(['ADD COLUMN ' + ' '.join(x) for x in columns_with_constraints]) + ';'

    #create sql alchemy engine
    engine = create_engine('postgresql' + '://' + cred.user + 
        ':' + cred.pw + '@' + cred.host + '/' + cred.user)
    #create connection with engine
    with engine.begin() as conn:
        #alter the table
        print 'altering the table'
        conn.execute(alter_query)
        #load the data into a temp table
        print 'loading temp table'
        temp_table_query = pd.io.sql.get_schema(df, 'temp_table', con= engine)
        conn.execute(temp_table_query)
    # pandas can't handle being inside the connection, not sure why    
    df.to_sql(name='temp_table', con=engine,if_exists='replace', schema = target_schema, index=False)
    with engine.begin() as conn: 
        print 'updating old table'
        #update the old table with data from temp table
        update_query = 'update ' + target_table + ' set '
        column_list = []
        for column in columns_added: # loop over multiple columns to create full sql statement
            column_list.append(column + ' = t.' + column)
        update_query += ', '.join(column_list)
        update_query += ' from temp_table as t where ' + target_table + '.' + join_col + '= t.' + join_col
        conn.execute(update_query)
        #drop the temp table
        print 'dropping temp table'
        conn.execute('drop table temp_table')





