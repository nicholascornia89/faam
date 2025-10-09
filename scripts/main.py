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
from data_visualization import *
from data_validation import *
from rdf import *
from statistics import *
from tropy import *

# Data

data_dir = "nodegoat_data"
out_dir = "tmp"

externalids2wd_mapping_filename = os.path.join("mapping", "externalids2wd_mapping.csv")

nodegoat2faam_kb_filename = os.path.join("mapping", "nodegoat2faam_kb_mapping.csv")

graph_attributes_type_filename = os.path.join(
    "mapping", "graph_attributes_type_mapping.csv"
)


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


def mapping_qid2uuid(d):
    object_list_filename = os.path.join(
        "tmp", "objects_list", "objects_list-" + get_current_date() + ".json"
    )
    wikidata_object_list = wikidata_objects_list(d)
    dict2json(wikidata_object_list, object_list_filename)

    print("Change references from QIDs to FAAM UUIDs...")  # NOT WORKING PROPERLY...
    d = qid2uuid_mapping(d)
    # Export to JSON
    nodegoat_export2JSON(d, os.path.join(out_dir, "nodegoat_export"))

    print("Importing new objects...")
    d, wikidata_object_list = import_new_objects_from_wd(d, out_dir)

    # Export everything to JSON
    nodegoat_export2JSON(d, os.path.join(out_dir, "nodegoat_export"))
    dict2json(wikidata_object_list, object_list_filename)

    return d


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

    d = mapping_qid2uuid(d)

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


def data_visualization():
    faam_kb = load_latest_JSON(os.path.join(out_dir, "faam_kb"))

    print("Generating image carousels for each manifestation...")
    github_api_repo = "https://api.github.com/repos/nicholascornia89"
    repo_name = "https://github.com/nicholascornia89/faam"
    generate_image_carousel(faam_kb, github_api_repo, repo_name)

    # generate pyvis networks
    # print("Generating graph networks visualizations...")
    # generate_faam_graphs(faam_kb, graph_attributes_type_filename, out_dir)


def data_validation():
    faam_kb = load_latest_JSON(os.path.join(out_dir, "faam_kb"))

    print("Unique labels, move the rest to aliases...")
    faam_kb = double_label_to_aliases(faam_kb)

    print("Remove duplicates in cross-references...")
    faam_kb = cross_references_duplicates(faam_kb)

    print("Getting cities list to CSV...")
    object_type2csv(faam_kb, object_type="city")

    print("Validating labels...")
    labels_validation(faam_kb)

    print("Validating qualifiers...")
    qualifiers_validation(faam_kb, nodegoat2faam_kb_filename)

    print("Checking for missing text fields with embedded IDs...")
    missing_fields_text_with_id(faam_kb)


# FAAM Knowledge base
def faam_kb():
    # FAAM kb script

    # saving JSON file
    faam_kb_filename = os.path.join(
        "tmp", "faam_kb", "faam_kb-" + get_current_date() + ".json"
    )

    print(f"Would you like to generate a new FAAM kb? y/n")
    answer = input()

    if answer == "y":
        d = load_latest_JSON(os.path.join(out_dir, "nodegoat_export"))

        d = mapping_qid2uuid(d)

        print("Generating FAAM knowledge base")

        faam_kb = generate_faam_kb(d, nodegoat2faam_kb_filename)

        faam_kb_filename = os.path.join(
            "tmp", "faam_kb", "faam_kb-" + get_current_date() + ".json"
        )

        dict2json(faam_kb, faam_kb_filename)

    else:
        faam_kb = load_latest_JSON(os.path.join(out_dir, "faam_kb"))

        faam_kb_mapping = csv2dict(nodegoat2faam_kb_filename)

        print(
            "Would you like to improve data via Wikidata queries? (Time consuming) y/n"
        )
        answer = input()

        if answer == "y":
            print(f"Improving MediaWiki image URLs...")
            faam_kb = images_base_url(faam_kb)

            print(f"Improving External ID URLs...")
            faam_kb = external_ids_base_url(faam_kb, faam_kb_mapping)

            print(f"Mapping QIDs to FAAM UUIDs...")
            faam_kb = qids2faamuudis(faam_kb)

            print(f"Remove empty statements...")
            faam_kb = remove_empty_statements(faam_kb)

            # adding Wikidata label to each qid statement
            print("Adding Wikidata labels to each QID...")
            faam_kb = add_label_to_qid_metadata(faam_kb)

            print(f"Adding labels to each statement and qualifier...")
            faam_kb = add_label_to_statement(faam_kb)

            # adding country statement in cities
            print("Adding country statement to cities...")
            faam_kb = add_country_to_cities(faam_kb)

        dict2json(faam_kb, faam_kb_filename)

        # adding cross_referencies WORKS FINE, BUT TIME CONSUMING
        print("Adding cross_references to each item...")
        cross_reference_mapping = json2dict(
            os.path.join("mapping", "cross_reference_mapping.json")
        )
        faam_kb = cross_references(faam_kb, cross_reference_mapping)

        dict2json(faam_kb, faam_kb_filename)

        # generate RDF graph ## TO BE TESTED
        generate_rdf_kb(
            faam_kb,
            nodegoat2faam_kb,
            os.path.join(out_dir, "rdf_kb", "rdf_kb-" + get_current_date() + ".ttl"),
        )

        # generate JSON serialization and append it to FAAM kb
        print("Generating JSON, CSV and RDF resources for each item...")
        faam_kb = generate_resource_items(faam_kb, nodegoat2faam_kb_filename, out_dir)

        dict2json(faam_kb, faam_kb_filename)


def statistics():
    faam_kb = load_latest_JSON(os.path.join(out_dir, "faam_kb"))

    # return basic statistics
    print("Some statistics...")
    basic_statistics(faam_kb)
    annotations_statistics(faam_kb)


# Mkdocs pages
def mkdocs_pages():
    faam_kb = load_latest_JSON(os.path.join(out_dir, "faam_kb"))

    # return basic statistics
    print("Some statistics...")
    basic_statistics(faam_kb)
    annotations_statistics(faam_kb)

    print("Generating Markdown pages from data...")
    # Mkdocs
    generate_pages(faam_kb, nodegoat2faam_kb_filename, out_dir)


################################
## CODE ##
################################


# nodegoat_import()
# wikidata_SPARQL_enhance()  ## It stall at a certain point...
faam_kb()
# data_visualization()
statistics()
data_validation()
# mkdocs_pages()
