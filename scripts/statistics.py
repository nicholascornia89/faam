"""
Scripts to generate statistics of the FAAM knowledge base
"""

# Import functions from other scripts
import sys

sys.path.append(".")
from utilities import *


def basic_statistics(faam_kb):  # returns the number of items
    number_of_items = len(faam_kb["items"])

    print(f"Number of Items in the FAAM knowledge base: {number_of_items}")

    number_statements_from_item = 0
    number_statements_from_wd = 0
    number_statements_other = 0
    number_qualifiers_from_item = 0
    number_qualifiers_from_wd = 0
    number_qualifiers_other = 0
    number_empty_statements = 0
    number_empty_labels = 0
    number_empty_descriptions = 0

    for item in faam_kb["items"]:
        for category in item.keys():
            if category not in ["id", "uuid_num", "cross-references", "resources"]:
                for prop in item[category]:
                    for statement in item[category][prop]:
                        if statement["value"] == "":
                            number_empty_statements += 1
                            if prop == "label":
                                number_empty_labels += 1
                            elif prop == "description":
                                number_empty_descriptions += 1
                            else:
                                continue
                        if statement["type"] == "item":
                            number_statements_from_item += 1
                        elif statement["type"] == "externalid":
                            if (
                                "wikidata.org" in statement["base_url"]
                            ):  # Wikidata entity
                                number_statements_from_wd += 1
                            else:
                                number_statements_other += 1
                        elif statement["type"] == "statement":
                            for qual in statement["qualifiers"]:
                                if qual["type"] == "item":
                                    number_qualifiers_from_item += 1
                                elif qual["type"] == "externalid":
                                    if "wikidata.org" in qual["base_url"]:
                                        number_qualifiers_from_wd += 1
                                    else:
                                        number_qualifiers_other += 1
                                else:
                                    number_qualifiers_other += 1
                        else:
                            number_statements_other += 1

    number_statements = (
        number_statements_from_item
        + number_statements_from_wd
        + number_statements_other
    )

    number_qualifiers = (
        number_qualifiers_from_item
        + number_qualifiers_from_wd
        + number_qualifiers_other
    )

    print(f"Total number of statements: {number_statements}")
    print(
        f"from item: {100*float(number_statements_from_item)/number_statements}%, from Wikidata: {100*float(number_statements_from_wd)/number_statements}%"
    )

    print(f"Total number of qualifiers: {number_qualifiers}")
    print(
        f"from item: {100*float(number_qualifiers_from_item)/number_qualifiers}%, from Wikidata: {100*float(number_qualifiers_from_wd)/number_qualifiers}%"
    )

    print(
        f"Empty statements: {number_empty_statements} \n Empty labels: {100*float(number_empty_labels)/number_of_items}% \n Empty descriptions: {100*float(number_empty_descriptions)/number_of_items}% "
    )


def annotations_statistics(faam_kb):
    manifestations = list(
        filter(
            lambda x: x["metadata"]["object_type"][0]["value"] == "manifestation",
            faam_kb["items"],
        )
    )

    number_of_manifestations = len(manifestations)
    number_of_handwritten_annotations = 0
    number_of_editorial_annotations = 0
    for manifestation in manifestations:
        number_of_handwritten_annotations += len(
            manifestation["statements"]["handwritten annotation"]
        )
        number_of_editorial_annotations += len(
            manifestation["statements"]["editorial annotation"]
        )

    print(f"Number of manifestations: {number_of_manifestations}")

    print(f"Number of handwritten annotations: {number_of_handwritten_annotations}")

    print(f"Number of editorial annotations: {number_of_editorial_annotations}")
