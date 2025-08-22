"""
Scritpts to enhance missing fields using SPARQL query to Wikidata.

"""

import sys

sys.path.append(".")
from utilities import *

from wikibase_api import Wikibase

# from SPARQLWrapper import SPARQLWrapper, JSON

# Load Wikidata (as default)
wb = Wikibase()

# Import fields to Wikidata properties mapping

nodegoat2wd_filename = os.path.join("mapping", "nodegoat2wd_mapping.csv")
nodegoat2wd = csv2dict(nodegoat2wd_filename)

def wikidata_objects_list(
	d
):  # generates a list of all objects with a Wikidata QID
	wikidata_object_list = []
	for object_type in d.keys():
		if "Wikidata QID" in d[object_type][0]:
			for obj in d[object_type]:
				if obj["Wikidata QID"][0] != "":
					wikidata_object_list.append(
						{
							"id": obj["id"],
							"nodegoat_id": int(obj["nodegoat_id"][0]),
							"Wikidata QID": obj["Wikidata QID"][0],
							"Wikidata id": int(obj["Wikidata QID"][0][1:]),
							"type": object_type,
						}
					)
			

	return sorted(wikidata_object_list, key=lambda x: x["Wikidata id"])

def enhance_nodegoat_fields(d):
	# generate wikidata object list and their ids for bisect search
	wikidata_object_list = wikidata_objects_list(d)
	wikidata_ids = []
	for obj in wikidata_object_list:
		wikidata_ids.append(obj["Wikidata id"])

	# list of new Wikidata IDs not previously present in the database.
	new_wikidata_items = []

	# get all objects according to type, assuming each object has a field called "Wikidata QID"
	for object_type in d.keys():
		print(f"Current object type: {object_type}")
		print("It might take a while...")
		if "Wikidata QID" in d[object_type][0].keys():
			print(f"Enhancing {object_type} statements via SPARQL query...")
			# generate list of fields to be queried to Wikidata for the object type
			fields_to_be_queried = []
			for field in d[object_type][0].keys():
				query = list(filter(lambda x: x["nodegoat_field"] == field, nodegoat2wd))
				if len(query) > 0:
					fields_to_be_queried.append(query[0])
			for obj in d[object_type]:  # enhance every object
				#print(f"Current object: {obj["Wikidata QID"][0]}")
				if obj["Wikidata QID"][0] != "":  # check if Wikidata QID is present
					qid = obj["Wikidata QID"][0]
					#print(f"Current object {qid}:")
					for field in fields_to_be_queried:
						if obj[field["nodegoat_field"]][0] == "":  # if field is empty
							query = wb_get_property_data(
								qid, field["wd_property"]
							)  # query property data
							if len(query) >= 1:
								values_list = []
								for statement in query:
									# print(statement)
									# input()
									try:
										if statement != "": # skip empty statements
											if statement["mainsnak"]["datatype"] == "external-id":
												values_list.append(statement["mainsnak"]["datavalue"]["value"])
											#if "id" in statement["mainsnak"]["datavalue"]["value"].keys(): # item case
											elif statement["mainsnak"]["datatype"] == "wikibase-item":
												values_list.append(
												statement["mainsnak"]["datavalue"]["value"]["id"]
											)
											elif statement["mainsnak"]["datatype"] == "time":
											#elif "time" in statement["mainsnak"]["datavalue"]["value"].keys(): # date case
												values_list.append(
														statement["mainsnak"]["datavalue"]["value"][
															"time"
														][1:11]
													)
											else:
												print(f"Unknown type for {statement} for {obj} ")
												input()
									except Exception:
										print (f"Error for {statement} for {obj} ")
										values_list.append("")
										input()

									
								# update object fields with new list
								if len(values_list) >0:
									obj[field["nodegoat_field"]] = values_list
									print(f"Updating object {obj["Wikidata QID"][0]} values of {field} to {obj[field["nodegoat_field"]]}")
									# check if the Wikidata QIDs are present in the Nodegoat database already
									for qid in obj[field["nodegoat_field"]]:
										try:
											if qid != "" and qid[0] == "Q":
												# bisect search
												index = bisect_left(wikidata_ids,int(qid[1:]))
												query = wikidata_object_list[index]
												if query == qid:
													pass 
												else:
													# if not present, add to new Wikidata items list
													new_wikidata_items.append(qid)
										except KeyError:
											print(f"Error for values list: {values_list} for {obj} ")
											input()

								
			print(f"Current number of new Wikidata items = {len(new_wikidata_items)}")
			print(new_wikidata_items)

	return d
							
def test_wb_query():
	# Example: Adolf Ruthardt data
	qid = "Q4401191"
	return wb.entity.get(qid)["entities"][qid]["labels"]

def wb_get_property_data(qid, pid):
	# get entity profile given property
	try:
		entity = wb.entity.get(qid)["entities"][qid]
		properties_list = entity["claims"].keys()
		# look for property
		if pid in properties_list:
			return entity["claims"][pid]
		else:
			return [""]
	# no qid case
	except Exception:
		return [""]
