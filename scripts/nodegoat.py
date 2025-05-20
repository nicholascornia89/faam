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
                        return True
    return False


""" This function takes all csv exports and converts them to a unique json file """


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

    """ reduce cities : TOO SLOW!

    print("Reducing number of cities...")

    search_fields = [
        "music_organization",
        "agent",
        "holding_institution",
        "manifestation",
    ]

    

    for i in range(len(d["city"])):
        city_id = d["city"][i]["id"]
        if check_id_in_fields(d, city_id, search_fields):
            # keep city
            pass
        else:
            del d["city"][i]

    """

    """ reduce countries: TOO SLOW and not working

    print("Reducing countries...")
    search_fields = ["music_organization", "agent", "holding_institution"]

    countries_to_be_deleted = []

    for i in range(len(d["country"])):
        country_id = d["country"][i]["id"]
        if check_id_in_fields(d, country_id, search_fields):
            # keep country
            pass
        else:
            countries_to_be_deleted.append(country_id)

    print(f"There are {len(countries_to_be_deleted)} superfluous countries.")

    for element in countries_to_be_deleted:
        query = list(filter(lambda x: x[1]["id"] == element, enumerate(d["country"])))
        del d["country"][query[0][0]]

    """

    # Export to JSON

    print("Exporting Nodegoat data to tmp folder...")
    dict2json(d, os.path.join("tmp", "nodegoat_export.json"))

    return


""" Given a csv file from Nodegoat export, returns a list without duplicates 
I assume that the first column will always be 'Nodegoat ID' """


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
