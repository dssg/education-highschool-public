import contextlib
import csv
import logging
import tempfile

import pandas.io.sql
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy.engine.url import URL

def connect(settings):
    """
    Performs database connection using database settings from the environmental variable 'edu_db_string'.
    Connection URL is formatted as: postgresql://<username>:<password>@<host>/<database>
    Returns SQLAlchemy Engine instance.
    """
    try:
      engine = create_engine(URL(**settings))
      # Test database connection.
      connection = engine.connect()
      connection.close()
      return engine
    except Exception as e:
        raise MyCusomException('Could not initialize database.') 

def postgres_copy(self, frame, name, if_exists='fail', index=True,
           index_label=None, schema=None, chunksize=None, dtype=None):
    """
    Write records stored in a DataFrame to a SQL database.

    Parameters
    ----------
    name : string
        Name of SQL table.
    frame : DataFrame
        DataFrame to upload.
    index : boolean, default True
        Write DataFrame index as a column.
    if_exists : {'fail', 'replace', 'append'}, default 'fail'
        - fail: If table exists, do nothing.
        - replace: If table exists, drop it, recreate it, and insert data.
        - append: If table exists, insert data. Create if does not exist.
    index_label : string or sequence, default None
        Column label for index column(s). If None is given (default) and
        `index` is True, then the index names are used.
        A sequence should be given if the DataFrame uses MultiIndex.
    schema : string, default None
        Name of SQL schema in database to write to (if database flavor
        supports this). If specified, this overwrites the default
        schema of the SQLDatabase object.
    chunksize : int, default None
        If not None, then rows will be written in batches of this size at a
        time. If None, all rows will be written at once.
    dtype : dict of column name to SQL type, default None
        Optional, specifying the datatype for columns. The SQL type should
        be a SQLAlchemy type.
    """

    if dtype is not None:
        import sqlalchemy.sql.type_api as type_api

        for col, my_type in dtype.items():
            if not issubclass(my_type, type_api.TypeEngine):
                raise ValueError('The type of %s is not a SQLAlchemy '
                                 'type ' % col)

    table = pandas.io.sql.SQLTable(name, self, frame=frame, index=index, 
                                   if_exists=if_exists, index_label=index_label, 
                                   schema=self.meta.schema, dtype=dtype)

    # Some tricks needed here:
    #   Need to explicitly keep reference to connection.
    #   Need to "open" temp file seperately in write and read mode.
    #   Otherwise data does not get loaded.
    conn = self.engine.raw_connection()
    with conn.cursor() as cur, tempfile.NamedTemporaryFile(mode='w') as temp_file:
        frame.to_csv(temp_file, index=index)
        temp_file.flush()

        with open(temp_file.name, 'r') as f:
            sql = "COPY {schema_name}.{table_name} ({column_names}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE)".format(
                schema_name=schema, table_name=name, column_names=', '.join(frame.columns.values))
            cur.copy_expert(sql, f)
    conn.commit()

    # Check for potential case sensitivity issues (GH7815).
    self.meta.reflect()
    if name not in self.engine.table_names(schema=schema or self.meta.schema):
        logging.warn("The provided table name '{0}' is not found exactly "
                      "as such in the database after writing the table, "
                      "possibly due to case sensitivity issues. Consider "
                      "using lowercase table names.".format(name))

def csv_to_sql(settings, csv_file, name, schema=None):
    engine = connect(settings)
    pandas_sql = pd.io.sql.pandasSQL_builder(engine, schema=schema, flavor=None)
    
    conn = pandas_sql.engine.raw_connection()
    # Get headers.
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        headers = reader.next()
    if headers == []:
        logging.warn("No data to load to table name '{0}'.".format(name))
        return
    # Load data using the PostgreSQL 'copy' command.
    with open(csv_file, 'r') as f:
        sql = "COPY {schema_name}.{table_name} ({column_names}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE)".format(
            schema_name=schema, table_name=name, column_names=', '.join(headers))
        conn.cursor().copy_expert(sql, f)
    conn.commit()
    return None

def df_to_sql(settings, frame, name, schema=None, index=False):
    engine = connect(settings)
    pandas_sql = pd.io.sql.pandasSQL_builder(engine, schema=schema, flavor=None)
    postgres_copy(pandas_sql, frame, name, schema=schema, index=index)