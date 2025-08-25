import json, csv
import time
import os
from copy import deepcopy
from bisect import bisect_left
import pandas as pd

# Import UUID libraries.
import uuid
import shortuuid


def csv2dict(csv_filename):  # imports a CSV file as dictionary
    f = open(csv_filename, "r")
    reader = csv.DictReader(f)
    d = {"items": []}
    for row in reader:
        d["items"].append(row)
    return d["items"]


def dict2csv(d, csv_filename):
    df = pd.DataFrame(data=d)
    df.to_csv(csv_filename, sep=",", index=False)


def json2dict(json_filename):  # imports a JSON file as dictionary
    with open(json_filename, "r") as f:
        json_file = json.load(f)
        return json_file


def dict2json(d, json_filename):  # export a dictionary to JSON file
    json_file = open(json_filename, "w")
    json.dump(d, json_file, indent=2, ensure_ascii=False)


def load_latest_JSON(out_dir):
    latest_json_filename = get_latest_file(out_dir)
    print(f"Loading JSON file: {latest_json_filename}")
    return json2dict(latest_json_filename)


def get_current_date():
    return time.strftime("%Y-%m-%d", time.gmtime())


def get_latest_file(basepath):  # returns latest file path in a directory
    files = os.listdir(basepath)
    paths = [os.path.join(basepath, basename) for basename in files]
    return max(paths, key=os.path.getctime)


def generate_short_uuid4(length=8):
    u = uuid.uuid4()
    s = shortuuid.encode(u)

    return s[:length]
