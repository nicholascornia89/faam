"""
Nodegoat import
"""

# Import functions from other scripts
import sys

sys.path.append(".")
from utilities import *


# Not working properly!!!!
def check_id_in_fields(d, id_value, search_fields):
    for field in search_fields:
        for item in d[field]:
            for key in item.keys():
                # look only into Object ID fields
                if "Object ID" in key:
                    query = list(filter(lambda x: x == id_value, item[key]))
                    if len(query) > 0:
                        print(f"Found {id_value} in field {field} of {item}")
                        input()
                        return True
    return False


""" This function takes all csv exports and converts them to a unique json file """


def import_csv_nodegoat(csv_filename):
    # convert csv to dictionary
    csv_dict = csv2dict(csv_filename)
    # generate list
    l = []
    old_ObjID = ""
    element = {"id": ""}
    for item in csv_dict:
        # print("Current item:")
        # print(item)
        # input()
        for field in item.keys():
            # print(f"Field: {field}")
            # check if new ObjID <> old_ObjID
            if field == '''\ufeff"Object ID"''':
                if item[field] == old_ObjID:
                    pass
                else:
                    # save element and create new one
                    old_ObjID = item[field]
                    l.append(element)
                    element = {}
                    element["id"] = [old_ObjID]

            else:  # metadata
                if field not in element:
                    element[field] = [item[field]]
                else:
                    # check duplicate for field
                    if item[field] not in element[field]:
                        element[field].append(item[field])
                    else:
                        # skip
                        pass

    return l[1:]


""" Given a csv file from Nodegoat export, returns a list without duplicates 
I assume that the first column will always be 'Nodegoat ID' """


def nodegoat_csv2json(data_dir):
    # Import raw CSV data
    d = {}
    for filename in os.listdir(data_dir):
        if filename.endswith(".csv"):
            d[filename[:-4]] = import_csv_nodegoat(os.path.join(data_dir, filename))

    """Cleanup and enhance data
		- [ ] Delete cities and countries that do not appear as metadata
		- [ ] Enhance Agent metadata through wd script
		- [ ] Convert ID value to dictionary {id,label}
		- [ x ] Merge manifestation lists to a unique one 
		- [ ] Convert Sub-Objects like Agent and Organization to dictionary
			{id,label,date,location,role}

	"""
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
                        lambda x: x[1]["id"] == item["id"],
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

    """ reduce countries """

    print("Reducing countries...")
    search_fields = ["music_organization", "agent", "holding_institution"]

    countries_to_be_kept = []  # list of countries ids to be kept

    cities_to_be_kept = []  # list of cities ids to be kept

    """ gather cities and countries from music_organization object """
    for item in d["music_organization"]:
        for city in item["City - Object ID"]:
            if city not in cities_to_be_kept:
                cities_to_be_kept.append(city)
        for country in item["Country - Object ID"]:
            if country not in countries_to_be_kept:
                countries_to_be_kept.append(country)

    """ gather cities and countries from holding_institution object """
    for item in d["holding_institution"]:
        for city in item["place - Object ID"]:
            if city not in cities_to_be_kept:
                cities_to_be_kept.append(city)
        for country in item["country - Object ID"]:
            if country not in countries_to_be_kept:
                countries_to_be_kept.append(country)

    """ gather cities and countries from agent object """
    for item in d["agent"]:
        for city in item["place of birth - Object ID"]:
            if city not in cities_to_be_kept:
                cities_to_be_kept.append(city)
        for city in item["place of death - Object ID"]:
            if city not in cities_to_be_kept:
                cities_to_be_kept.append(city)
        for country in item["country of citizenship - Object ID"]:
            if country not in countries_to_be_kept:
                countries_to_be_kept.append(country)

    """ gather cities and countries from manifestation object """
    for item in d["manifestation"]:
        for city in item["[Agent] Location Reference - Object ID"]:
            if city not in cities_to_be_kept:
                cities_to_be_kept.append(city)
        for city in item["[Organisation] Location Reference - Object ID"]:
            if city not in cities_to_be_kept:
                cities_to_be_kept.append(city)

    print(f"Cities to be kept: {len(cities_to_be_kept)}")
    print(f"Countries to be kept: {len(countries_to_be_kept)}")

    print("Cleaning up superfluous cities and countries...")

    d_copy_city = deepcopy(d["city"])
    d_copy_country = deepcopy(d["country"])
    d["city"] = []
    d["country"] = []

    # cleaning up cities and countries

    for city in d_copy_city:
        if city["id"][0] in cities_to_be_kept:
            d["city"].append(city)

    for country in d_copy_country:
        if country["id"][0] in countries_to_be_kept:
            d["country"].append(country)

    # Export to JSON

    print("Exporting Nodegoat data to tmp folder...")
    dict2json(d, os.path.join("tmp", "nodegoat_export.json"))

    return
