"""
Generate the FAAM knowedge graph
"""
import sys

sys.path.append(".")
from utilities import *

"""
Structure of JSON serialization

{
	"items": [
				{
					"id": "FAAM UUID",
					"metadata": {
						"id": [{"type": "id", "value": "FAAM UUID"}],
						"nodegoat_id": "old Nodegoat ID",
						"qid": "Wikidata QID",
						"object_type": [{"type": "schema", "value": "object_type"}]
						"label": "preferred label",
						"aliases": ["alternative labels"],
						"description": "short string"
						},

					"statements": {
									"property_name": [
										{"type": "string", "value": "string value"},
										{"type": "externalid", "value": "id with baseurl"},
										{"type": "item", "value": "uuid"},
										{"type": "date", "value": "date"},
										{"type": "url", "value": "url"}

									
									]


						},

					"cross-references": {
									"property_name": [  # format is assessed in template.csv file
														{"label": "label_to be_shown", "data_type": "data_type", "value": "value", "thumb": ""},
														{"label": "label_to be_shown", "data_type": "data_type", "value": "value", "thumb": "url to .gif file"},
														]

						
				
					},

					"resources": {
						"JSON": [{"label": "JSON","type": "url",  "value": "url to .json file"}],
						"RDF": [{"label": "RDF","type": "url",  "value": "url to .ttl file"}],
						"CSV" : [{"label": "CSV","type": "url",  "value": "url to .csv file"}],
						"GitHub": [{"label": "GitHub images","type": "url",  "value": "url to GitHub repository directory"}]
	
						}
"""


def images_base_url(
	faam_kb,
	wikimedia_common_base_url="https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/",
	faam_thumbs_base_url="../assets/images/thumbs/",
):
	# Add base urls to image and thumb.
	for item in faam_kb["items"]:
		# thumbs and images
		for key in item["resources"]:
			if key == "thumb":
				# remove old FAAM url and keep only filename
				item["resources"]["thumb"][0]["value"] = (
					item["metadata"]["FAAM manifestation ID"][0]["value"] + ".gif"
				)
				item["resources"]["thumb"][0]["base_url"] = faam_thumbs_base_url
			if key == "image":
				# make sure redirects to Wikimedia Commons

				item["resources"]["image"][0]["base_url"] = wikimedia_common_base_url
				if wikimedia_common_base_url in item["resources"]["image"][0]["value"]:
					# keep only filename
					item["resources"]["image"][0]["value"] = item["resources"]["image"][
						0
					]["value"].replace(wikimedia_common_base_url, "")
				else:
					item["resources"]["image"][0]["value"] = item["resources"]["image"][
						0
					]["value"].replace(" ", "_")
	return faam_kb


def external_ids_base_url(faam_kb, faam_kb_mapping):
	# externalid
	for item in faam_kb["items"]:
		for key in item["metadata"].keys():
			if item["metadata"][key][0]["type"] == "externalid":
				# lookup base url for statement
				query = list(
					filter(lambda x: x["faam_property"] == key, faam_kb_mapping)
				)
				base_url = query[0]["base_url"]
				for statement in item["metadata"][key]:
					statement["base_url"] = base_url

		for key in item["statements"].keys():
			if item["statements"][key][0]["type"] == "externalid":
				# lookup base url for statement
				query = list(
					filter(lambda x: x["faam_property"] == key, faam_kb_mapping)
				)
				base_url = query[0]["base_url"]
				for statement in item["statements"][key]:
					statement["base_url"] = base_url

		return faam_kb


def qids2faamuudis(faam_kb):
	# generate QID list
	qid_list = []
	item_list = []
	for item in faam_kb["items"]:
		if "qid" in item["metadata"].keys():
			if item["metadata"]["qid"][0]["value"] != "":
				qid_list.append(int(item["metadata"]["qid"][0]["value"][1:]))
				item_list.append(
					{"id": item["id"], "qid": item["metadata"]["qid"][0]["value"]}
				)

	changed_qids = []

	# Check if items statements have QIDs instead of FAAM UUIDs.
	for item in faam_kb["items"]:
		for key in item["statements"].keys():
			if item["statements"][key][0]["type"] == "item":
				for statement in item["statements"][key]:
					# check if value is Wikidata QID
					if statement["value"] != "":
						if statement["value"][0] == "Q":
							try:
								qid_number = int(statement["value"][1:])
								qid_number = int(qid_number)
								index = bisect_left(qid_list, qid_number)
								qid = "Q" + str(qid_number)
								print(f"Query {qid} with result {item_list[index]}")
								input()
								if item_list[index]["qid"] == "Q" + str(qid_number):
									# replace QID with FAAM UUID
									statement["value"] = item_list[index]["id"]
									changed_qids.append(item_list[index]["qid"])
							except Exception:
								pass

	print(f"Changed QID statements {len(changed_qids)}: \n {changed_qids}")

	return faam_kb


# Generate FAAM Knowledge Base JSON from latest Nodegoat export
def generate_faam_kb(d, nodegoat2faam_kb_filename):
	count_no_label = 0
	# Import mapping
	faam_kb_mapping = csv2dict(nodegoat2faam_kb_filename)
	faam_kb = {"items": []}
	for object_type in d.keys():
		for obj in d[object_type]:
			item = {
				"id": obj["id"],
				"metadata": {},
				"statements": {},
				"cross-references": {},
				"resources": {},
			}
			for field in obj.keys():
				# lookup field in mapping
				try:
					field_mapping = list(
						filter(lambda x: x["nodegoat_field"] == field, faam_kb_mapping)
					)[0]
				except IndexError:
					pass
				# record information according to mapping layout
				# save object type
				item["metadata"]["object_type"] = [
					{"type": "schema", "value": object_type}
				]
				# save FAAM UUID
				if field == "id":
					item["metadata"]["id"] = [{"type": "id", "value": obj["id"]}]
				# rest of statements
				else:
					# I am assuming that there are equal number of qualifiers as statement of type `statement`. Unfortunately there might be problems with multiple roles assigned to one agent!
					for statement in obj[field]:
						if field_mapping["data_type"] == "statement":
							# append qualifiers

							############# TO BE TESTED! #################
							statement_number = len(obj[field])
							i = 0
							qualifier_fields = field_mapping["qualifiers"].split(",")
							while i < statement_number:
								qualifiers = []
								print(f"List of qualifiers: {qualifier_fields}")
								for qualifier_field in qualifier_fields:
									qualifier_field_mapping = list(
									filter(lambda x: x["nodegoat_field"] == qualifier_field, faam_kb_mapping))[0]
									qualifier_number = len(item["statements"][qualifier_field])
									if qualifier_number == statement_number:
										qualifiers.append({"type": qualifier_field_mapping["data_type"], "value": item["statements"][qualifier_field][i]})
									else:
										print(f"Incongruent number of qualifiers and statements for item {item["id"]}")

								print(f"Qualifiers for {field} with statement {statement}: \n {qualifiers}")
								input()

								try:
									item[field_mapping["category"]][
										field_mapping["faam_property"]
									].append(
										{"type": field_mapping["data_type"], "value": statement, "qualifiers": qualifiers}
									)
								except KeyError:
									# key not yet created
									item[field_mapping["category"]][
										field_mapping["faam_property"]
									] = [
										{"type": field_mapping["data_type"], "value": statement, "qualifiers": qualifiers}
									]

								i +=1
								
							


						elif field_mapping["data_type"] == "qualifier":
							# qualifiers are appended to the corresponding statement
							pass

						else: # not nested data type statement
							# I am appending multiple nodegoat fields that maps to a unique faam property
							try:
								item[field_mapping["category"]][
									field_mapping["faam_property"]
								].append(
									{"type": field_mapping["data_type"], "value": statement}
								)
							except KeyError:
								# key not yet created
								item[field_mapping["category"]][
									field_mapping["faam_property"]
								] = [
									{"type": field_mapping["data_type"], "value": statement}
								]


			# assign label value from Wikidata Label if absent
			if item["metadata"]["label"][0]["value"] == "":
				try:
					item["metadata"]["label"][0] = {
						"type": "string",
						"value": obj["Wikidata Label"][0],
					}

				except KeyError:
					count_no_label += 1
			# append item to knowledge base
			faam_kb["items"].append(item)

	print(f"Items without label: {count_no_label}")

	# extra scripts

	faam_kb = images_base_url(faam_kb)

	faam_kb = external_ids_base_url(faam_kb, faam_kb_mapping)

	faam_kb = qids2faamuudis(faam_kb)

	return faam_kb
