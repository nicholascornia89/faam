"""
Main script
"""

# Import functions from other scripts
import sys

sys.path.append(".")
from utilities import *
from nodegoat import *
from wikidata import *
from mkdocs import *
from faam_kb import *
from rdf import *
from tropy import *

# Data

data_dir = "nodegoat_data"
out_dir = "tmp"

externalids2wd_mapping_filename = os.path.join("mapping", "externalids2wd_mapping.csv")

nodegoat2faam_kb_filename = os.path.join("mapping", "nodegoat2faam_kb_mapping.csv")


# Nodegoat
def nodegoat_import():
    print(
        "This script generates a new JSON file from Nodegoat CSV export in nodegoat_data folder.\n Press enter to continue..."
    )
    input()

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

    nodegoat_export2JSON(d, os.path.join(out_dir, "nodegoat_export"))


# Wikidata
def wikidata_SPARQL_enhance():
    print(
        "This script will enhance the latest nodegoat_export JSON serialization via Wikidata queries.\n Press enter to continue..."
    )
    input()

    d = load_latest_JSON(os.path.join(out_dir, "nodegoat_export"))

    # Generate object list and export it to file
    print("Generating object list...")
    object_list_filename = os.path.join(
        "tmp", "objects_list", "objects_list-" + get_current_date() + ".json"
    )
    wikidata_object_list = wikidata_objects_list(d)
    dict2json(wikidata_object_list, object_list_filename)

    print("Importing new objects...")
    d, wikidata_object_list = import_new_objects_from_wd(d, out_dir)

    # Export everything to JSON
    nodegoat_export2JSON(d, os.path.join(out_dir, "nodegoat_export"))
    dict2json(wikidata_object_list, object_list_filename)

    print("Change references from QIDs to FAAM UUIDs...")  # NOT WORKING PROPERLY...
    d = qid2uuid_mapping(d)
    # Export to JSON
    nodegoat_export2JSON(d, os.path.join(out_dir, "nodegoat_export"))

    # Query very demanding!
    print("Updating description and aliases from Wikidata...")
    d = query_descriptions_and_aliases(d, os.path.join(out_dir, "nodegoat_export"))

    # Wikimedia image URLs redirect
    d = change_wikimedia_image_url(
        d,
        base_url="https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/",
        old_base_url="https://commons.wikimedia.org/wiki/File:",
    )
    # Export to JSON
    nodegoat_export2JSON(d, os.path.join(out_dir, "nodegoat_export"))

    # Retrieve Wikidata QID from external identifiers TO BE CHECKED
    print("Retrieving Wikidata QID from external identifiers...")
    d = external2wikidataqid(
        d, os.path.join(out_dir, "nodegoat_export"), externalids2wd_mapping_filename
    )

    # Enhance data via SPARQL queries
    print("Enhancing data via Wikidata SPARQL queries...")
    d = enhance_nodegoat_fields(d, os.path.join(out_dir, "nodegoat_export"))

    # Export to JSON
    nodegoat_export2JSON(d, os.path.join(out_dir, "nodegoat_export"))
    # Update object list
    wikidata_object_list = wikidata_objects_list(d)
    dict2json(wikidata_object_list, object_list_filename)


# FAAM Knowledge base
def faam_kb():
    # FAAM kb script

    d = load_latest_JSON(os.path.join(out_dir, "nodegoat_export"))

    """
    print("Importing new objects...")
    d, wikidata_object_list = import_new_objects_from_wd(d, out_dir)

    # Export everything to JSON
    nodegoat_export2JSON(d, os.path.join(out_dir, "nodegoat_export"))
    dict2json(
        wikidata_object_list,
        os.path.join(
            out_dir, "objects_list", "object_list-" + get_current_date() + ".json"
        ),
    )

    print("Change references from QIDs to FAAM UUIDs...")  # NOT WORKING PROPERLY...
    d = qid2uuid_mapping(d)
    # Export to JSON
    nodegoat_export2JSON(d, os.path.join(out_dir, "nodegoat_export"))

    input()
    """
    """
    print("Fix Nodegoat sub-objects statements:")
    d = fix_subobjects_statements(
        d, os.path.join(data_dir, "manifestation_agents.csv"), nodegoat2faam_kb_filename
    )
    nodegoat_export2JSON(d, os.path.join(out_dir, "nodegoat_export"))
    """

    print("Generating FAAM knowledge base")

    faam_kb = generate_faam_kb(d, nodegoat2faam_kb_filename)

    faam_kb_filename = os.path.join(
        "tmp", "faam_kb", "faam_kb-" + get_current_date() + ".json"
    )

    dict2json(faam_kb, faam_kb_filename)


# Mkdocs pages
def mkdocs_pages():
    print("Generating Markdown pages from data...")
    # Mkdocs
    d = load_latest_JSON(os.path.join(out_dir, "nodegoat_export"))
    generate_pages(faam_kb, nodegoat2faam_kb_filename, out_dir)


################################
## CODE ##
################################


# nodegoat_import()
# wikidata_SPARQL_enhance()
faam_kb()
# mkdocs_pages()
