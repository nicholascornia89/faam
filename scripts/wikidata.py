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


def enhance_nodegoat_fields(d):
	# get all objects according to type, assuming each object has a field called "Wikidata QID"
	for object_type in d.keys():
		print("getting in...")
		if "Wikidata QID" in d[object_type][0].keys():
			print(f"Enhancing {object_type} statements via SPARQL query...")
			for obj in d[object_type]:  # enhance every object
				if obj["Wikidata QID"][0] != "":  # check if Wikidata QID is present
					qid = obj["Wikidata QID"][0]
					print(f"Current object {qid}:")
					for field in nodegoat2wd.keys():
						if (
							field in obj.keys() and obj[field][0] == ""
						):  # if field is present and empty
							query = wb_get_property_data(
								qid, nodegoat2wd[field]
							)  # query property data
							if len(query) >= 1:
								# multiple entries
								values_list = []
								for statement in query:
									# print(statement)
									# input()
									try:
										values_list.append(
											statement["mainsnak"]["datavalue"]["value"]["id"]
										)
										
									except KeyError:
										# case datatype is not item
										try:
											if (
												"time"
												in statement["mainsnak"]["datavalue"][
													"value"
												].keys()
											):
												values_list.append(
													statement["mainsnak"]["datavalue"]["value"][
														"time"
													][1:11]
												)
										except Exception:
											pass
								# update object fields with new list
								obj[field] = values_list
								print(f"Updating object {obj["Wikidata QID"][0]} values of {field} to {obj[field]}")
								input()
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
