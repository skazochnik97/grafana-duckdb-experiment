#!/usr/bin/python3
# apt install python3-pip
# pip3 install duckdb pandas

import duckdb
import os
import re

# Specify the directory to monitor for new Parquet raw files
watched_dir = '/var/parquetraw/'

connection = duckdb.connect(database=':memory:')
all_files = os.listdir(watched_dir);
filepattern_set = set()
filepattern=""

# iterate on all files in directory
for file in all_files:
    filepattern = re.split("_", file)[0]
    
    # work with uniq file pattern only
    if filepattern not in filepattern_set:
        filepattern_set.add(filepattern)

        schema_query = duckdb.sql(f"SELECT name, type, converted_type FROM parquet_schema('{watched_dir + file}');").fetchall()

        rows=""
        # first row consists "schema" header. We really don't want to use it
        for row in schema_query[1:]:
            rows = rows +  f"\"{row[0]}\"\t\t{'text' if row[1] == 'BYTE_ARRAY' else 'int'},\n"
        # render sql-script for creating foreign table
        print(f"CREATE FOREIGN TABLE public.{filepattern} (\n\
{rows} \
 filename                     text\n\
) \n\
SERVER duckdb_server \n\
OPTIONS ( \n\
    table 'read_parquet(\"/var/parquetraw/{filepattern}_*.parquet\", filename=true)' \n\
); \n\
")

connection.close()
