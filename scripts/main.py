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

externalids2wd_mapping_filename = os.path.join("mapping", "externalids2wd_mapping.csv")

print("Would you like to generate a new JSON file? y/n")
answer = input()

if "y" in answer:
    # Collect CSV data into unique JSON file
    d = nodegoat_csv2json(data_dir)

    # Assign unique (short)UUID identifiers
    print("Assigning unique (short)UUID identifiers to each objects...")
    d = nodegoat_uuid_generator(d)

    # Substitute Nodegoat Object ID referencing with UUIDs
    print("Echaning cross-relationships references with new UUIDs...")
    d = nodegoat_uuid_mapping(d)

    # Cleanup unused entities, such as cities, countries and works.
    d = nodegoat_cleaup_superfluous_objects(d)

    # Export to JSON

    nodegoat_export2JSON(d, out_dir)

else:  # import data from latest JSON backup
    d = load_nodegoat_JSON(out_dir)

    # Generate object list and export it to file
    print("Generating object list...")
    object_list_filename = os.path.join(
        "tmp", "object-list-" + get_current_date() + ".json"
    )
    wikidata_object_list = wikidata_objects_list(d)

    dict2json(wikidata_object_list, object_list_filename)

    # Record items to be added TO BE CONTINUED
    dict2json(
        create_new_ids_after_wikidata_enhance(d),
        os.path.join("tmp", "new_wikidata_ids-" + get_current_date() + ".json"),
    )

    # Wikimedia image URLs redirect TO BE CHECKED
    d = change_wikimedia_image_url(
        d,
        base_url="https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/",
        old_base_url="https://commons.wikimedia.org/wiki/File:",
    )

    # Retrieve Wikidata QID from external identifiers TO BE CHECKED

    d = external2wikidataqid(d, externalids2wd_mapping_filename)

    # Enhance data via SPARQL queries
    print("Enhancing data via Wikidata SPARQL queries...")
    d = enhance_nodegoat_fields(d, out_dir)  # TO BE CHECKED

    # Export to JSON
    nodegoat_export2JSON(d, out_dir)


# RDF

# Tropy
database_filename = "test.tpy"

# It works. Results are stored in tmp directory
# export_tropy_tables(database_filename)
