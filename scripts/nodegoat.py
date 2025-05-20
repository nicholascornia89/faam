"""
Nodegoat import
"""

# Import functions from other scripts
import sys

sys.path.append(".")
from utilities import *

""" This function takes all csv exports and converts them to a unique json file """


def nodegoat_csv2json(data_dir):
    d = {}
    for filename in os.listdir(data_dir):
        if filename.endswith(".csv"):
            d[filename[:-4]] = import_csv_nodegoat(os.path.join(data_dir, filename))

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
