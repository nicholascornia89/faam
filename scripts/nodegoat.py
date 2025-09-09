"""
Nodegoat import
"""

# Import functions from other scripts
import sys

sys.path.append(".")
from utilities import *


""" This function takes all csv exports and converts them to a unique json file """


def import_csv_nodegoat(csv_filename):
    # convert csv to dictionary
    csv_dict = csv2dict(csv_filename)
    # generate list
    l = []
    # record last Object ID
    old_ObjID = ""
    # initialise empty element
    element = {"id": "", "nodegoat_id": ""}
    for item in csv_dict:
        for field in item.keys():
            # check if new ObjID <> old_ObjID
            if field == '''\ufeff"Object ID"''':
                if item[field] == old_ObjID:
                    pass
                else:
                    # save element and create new one
                    old_ObjID = item[field]
                    l.append(element)
                    element = {"id": ""}
                    element["nodegoat_id"] = [old_ObjID]

            elif (
                "[Agent]" in field or "[Organisation]" in field
            ):  # metadata as compound object type with references for [Agent] and [Organisation]
                if field not in element:
                    element[field] = [item[field]]
                else:
                    # I am explicitly repeating fields to guarantee matching between references.
                    element[field].append(item[field])

            else:
                # normal metadata
                if field not in element:
                    element[field] = [item[field]]
                else:
                    # check duplicate for field
                    if item[field] not in element[field]:
                        element[field].append(item[field])
                    else:
                        # skip
                        pass

    # append last element (more elegant solution is needed...
    l.append(element)
    # we return from the second element, not considering the first empty one.
    return l[1:]


""" Given a csv file from Nodegoat export, returns a list without duplicates 
I assume that the first column will always be 'Nodegoat ID' """


def nodegoat_csv2json(data_dir):
    # Import raw CSV data
    d = {}
    for filename in os.listdir(data_dir):
        if filename.endswith(".csv"):
            d[filename[:-4]] = import_csv_nodegoat(os.path.join(data_dir, filename))

    # merge manifestation
    print("Merging manifestation fields together...")
    manifestation_merged = []
    manifestation_fields = []
    for field in d.keys():
        if "manifestation" in field:
            manifestation_fields.append(field)
            for item in d[field]:
                # lookup for id in manifestation_merged
                query = list(
                    filter(
                        lambda x: x[1]["nodegoat_id"] == item["nodegoat_id"],
                        enumerate(manifestation_merged),
                    )
                )
                if len(query) == 0:
                    # create a new element in manifestation_merged
                    manifestation_merged.append(item)
                else:
                    # append metadata to existing element manifestation_merged[query[0][0]]
                    for key in item.keys():
                        if key not in manifestation_merged[query[0][0]]:
                            # append metadata
                            manifestation_merged[query[0][0]][key] = item[key]
                        else:
                            pass

    # remove old fields
    for field in manifestation_fields:
        d.pop(field, None)

    # append merged manifestation
    d["manifestation"] = manifestation_merged

    return d


def nodegoat_cleaup_superfluous_objects(d):
    print("Reducing superfluous items...")

    cities = []
    for city in d["city"]:
        cities.append(city["id"])

    countries = []
    for country in d["country"]:
        countries.append(country["id"])

    works = []
    for work in d["musical_work"]:
        works.append(work["id"])

    countries_to_be_kept = []  # list of countries ids to be kept

    cities_to_be_kept = []  # list of cities ids to be kept

    works_to_be_kept = []  # list of works ids to be kept

    for item in d["manifestation"]:
        for note in item["Notes"]:
            if note != "":
                if note in cities:
                    cities_to_be_kept.append(note)
                elif note in works:
                    works_to_be_kept.append(note)
                elif note in countries:
                    countries_to_be_kept.append(note)
                else:
                    pass

        for sections in item["Sections"]:
            if sections != "":
                if sections in cities:
                    cities_to_be_kept.append(sections)
                elif sections in works:
                    works_to_be_kept.append(sections)
                elif sections in countries:
                    countries_to_be_kept.append(sections)
                else:
                    pass

    """gather works to be kept"""

    for item in d["musical_work"]:
        for work in item["based on"]:
            if work not in works_to_be_kept:
                works_to_be_kept.append(work)

    for item in d["manifestation"]:
        for work in item["Musical Works"]:
            if work not in works_to_be_kept:
                works_to_be_kept.append(work)

    """ gather cities and countries from music_organization object """
    for item in d["music_organization"]:
        for city in item["place"]:
            if city not in cities_to_be_kept:
                cities_to_be_kept.append(city)
        for country in item["country"]:
            if country not in countries_to_be_kept:
                countries_to_be_kept.append(country)

    """ gather cities and countries from holding_institution object """
    for item in d["holding_institution"]:
        for city in item["place"]:
            if city not in cities_to_be_kept:
                cities_to_be_kept.append(city)
        for country in item["country"]:
            if country not in countries_to_be_kept:
                countries_to_be_kept.append(country)

    """ gather cities and countries from agent object """
    for item in d["agent"]:
        for city in item["place of birth"]:
            if city not in cities_to_be_kept:
                cities_to_be_kept.append(city)
        for city in item["place of death"]:
            if city not in cities_to_be_kept:
                cities_to_be_kept.append(city)
        for country in item["country of citizenship"]:
            if country not in countries_to_be_kept:
                countries_to_be_kept.append(country)

    """ gather cities and countries from manifestation object """
    for item in d["manifestation"]:
        try:
            for city in item["[Agent] Location Reference"]:
                if city not in cities_to_be_kept:
                    cities_to_be_kept.append(city)
            for city in item["[Organisation] Location Reference"]:
                if city not in cities_to_be_kept:
                    cities_to_be_kept.append(city)
        except KeyError:
            print(f"Error in this item: \n {item}")

    print(f"Cities to be kept: {len(cities_to_be_kept)}")
    print(f"Countries to be kept: {len(countries_to_be_kept)}")
    print(f"Works to be kept: {len(works_to_be_kept)}")

    d_copy_city = deepcopy(d["city"])
    d_copy_country = deepcopy(d["country"])
    d_copy_work = deepcopy(d["musical_work"])
    d["city"] = []
    d["country"] = []
    d["musical_work"] = []

    # cleaning up

    for city in d_copy_city:
        if city["id"] in cities_to_be_kept:
            d["city"].append(city)

    for country in d_copy_country:
        if country["id"] in countries_to_be_kept:
            d["country"].append(country)

    for work in d_copy_work:
        if work["id"] in works_to_be_kept:
            d["musical_work"].append(work)

    return d


def nodegoat_uuid_generator(
    d,
):  # generates a unique uuid v4 (+short version) for each object
    for object_type in d.keys():
        for obj in d[object_type]:
            obj["id"] = generate_short_uuid4()

    return d


def nodegoat_objects_list(
    d,
):  # generates a list of all objects, with their relative object type
    object_list = []
    for object_type in d.keys():
        for obj in d[object_type]:
            object_list.append(
                {
                    "id": obj["id"],
                    "nodegoat_id": int(obj["nodegoat_id"][0]),
                    "Wikidata QID": "",
                    "type": object_type,
                }
            )
            if "Wikidata QID" in obj.keys():
                object_list[-1]["Wikidata QID"] = obj["Wikidata QID"][0]

    return sorted(object_list, key=lambda x: x["nodegoat_id"])


def nodegoat_uuid_mapping(d):  # substitute object ID referencing with (short)UUID
    # generate object list of all types
    object_list = nodegoat_objects_list(d)

    nodegoat_ids = []
    for obj in object_list:
        nodegoat_ids.append(obj["nodegoat_id"])

    for object_type in d.keys():
        # print(f"Current object type: {object_type}")
        # select fields to be updated
        to_be_updated_fields = []
        for field in d[object_type][0].keys():
            if "Object ID" in field:
                to_be_updated_fields.append(field)

        # print(f"Fields to be updated: {to_be_updated_fields}")

        for obj in d[object_type]:
            for field in to_be_updated_fields:
                uuid_field = []
                for reference in obj[field]:
                    if reference != "":
                        # bisection method to retrieve UUID given nodegoat ID
                        index = bisect_left(nodegoat_ids, int(reference))
                        query = [object_list[index]]
                        try:
                            uuid_field.append(query[0]["id"])
                        except IndexError:
                            print(f"Missing reference: {reference} for object!")

                        # rename field
                        uuid_field_name = field.split(" - ")[0]
                        # substitute new UUID field with to old one with Object IDs
                        obj[uuid_field_name] = uuid_field
                    else:
                        # keep key in case of empty reference
                        uuid_field_name = field.split(" - ")[0]
                        # substitute new UUID field with to old one with Object IDs
                        obj[uuid_field_name] = [""]

                # delete old field with 'Object ID' in it
                obj.pop(field, None)

    return d


def nodegoat_export2JSON(d, out_dir):
    # print("Exporting Nodegoat data to tmp folder...")
    dict2json(
        d, os.path.join(out_dir, "nodegoat_export-" + get_current_date() + ".json")
    )

    return
