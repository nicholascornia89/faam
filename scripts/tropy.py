"""
Official documentation: https://docs.python.org/3/library/sqlite3.html
"""

import sqlite3
import os

# Import functions from other scripts
import sys

sys.path.append(".")

from utilities import *

# Pandas allows to export and import dataframes to sql
import pandas as pd

tropy_tables = [
    "project",
    "access",
    "subjects",
    "images",
    "photos",
    "selections",
    "items",
    "metadata",
    "metadata_values",
    "notes",
    "lists",
    "list_items",
    "tags",
    "taggings",
    "trash",
]


# Query the loaded database
def sql_query(database_filename, query):
    # Load the database connector to Python
    con = sqlite3.connect(database_filename)
    # Import the result of the query to Pandas Dataframe
    query_df = pd.read_sql_query(query, con)
    con.close()
    return query_df


def export_tropy_tables(database_filename, tropy_tables=tropy_tables):
    base_query = """SELECT * from """
    for table in tropy_tables:
        query = base_query + table
        # export table to Pandas DataFrame
        table_df = sql_query(database_filename, query)
        # export to CSV to tmp folder
        table_df.to_csv(os.path.join("tmp", f"{table}.csv"))
