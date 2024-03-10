#!/usr/bin/python3

import duckdb
import pandas
import os

# connect to database
connection = duckdb.connect(database='/var/duckdb/database.duckdb', read_only=False)

# Specify the directory to monitor for new Parquet files
watched_dir = '/var/parquet/'

## Preparing
# create stub aggregations_table table if it not exists
connection.execute(
    "CREATE TABLE IF NOT EXISTS aggregations_table ( \
      Key VARCHAR, \
      Interval1Value BIGINT, \
      Interval2Value BIGINT, \
      Interval3Value BIGINT, \
      Interval4Value BIGINT, \
      filename VARCHAR);")

# create stub filenames_table table if it not exists for already loaded parquete files
connection.execute(
    "CREATE TABLE IF NOT EXISTS filenames_table ( \
      filename VARCHAR);")

## Main block
# get all file names from watched dir
dataFrameWatchedFiles = pandas.DataFrame({"filename": [os.path.abspath(os.path.join(watched_dir, file)) for file in os.listdir(watched_dir)]})
# get all already loaded filenames
dataFrameLoadedFiles = connection.query("SELECT filename FROM filenames_table").to_df()

# get diff from exists and loaded
dataFrameDiffed = pandas.concat([dataFrameWatchedFiles, dataFrameLoadedFiles]).drop_duplicates(keep=False)

# load diffed files into duckdb database
for index, row in dataFrameDiffed.iterrows():
  print("Loading into database: " + row["filename"])
  connection.execute("BEGIN TRANSACTION; \
                      INSERT INTO filenames_table VALUES ('" + row["filename"] + "'); \
                      INSERT INTO aggregations_table SELECT * FROM read_parquet('" + row["filename"] + "', filename=true); \
                      COMMIT;")
