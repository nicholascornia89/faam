"""
Main script
"""

# Import functions from other scripts
import sys

sys.path.append(".")
from utilities import *
from nodegoat import *
from rdf import *
from tropy import *

# Nodegoat

data_dir = "nodegoat_data"

nodegoat_csv2json(data_dir)


# RDF

# Tropy
database_filename = "test.tpy"

# It works. Results are stored in tmp directory
# export_tropy_tables(database_filename)
