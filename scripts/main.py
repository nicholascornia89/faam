"""
Main script
"""

# Import functions from other scripts
import sys

sys.path.append(".")
from utilities import *
from nodegoat import *
from wikidata import *
from rdf import *
from tropy import *

# Nodegoat

data_dir = "nodegoat_data"
out_dir = "tmp"

# Collect CSV data into unique JSON file
d = nodegoat_csv2json(data_dir)

# Assign unique (short)UUID identifiers

d = nodegoat_uuid_generator(d)

# Substitute Nodegoat Object ID referencing with UUIDs

# d = nodegoat_uuid_mapping(d) # TO BE CONTINUED

# Enhance data via SPARQL queries

# d = SPARQL_enhance_metadata(d) # TO BE CONTINUED

# Cleanup unused entities, such as cities, countries and works.

d = nodegoat_cleaup_superfluous_objects(d)

# Export to JSON

nodegoat_export2JSON(d, out_dir)


# RDF

# Tropy
database_filename = "test.tpy"

# It works. Results are stored in tmp directory
# export_tropy_tables(database_filename)
