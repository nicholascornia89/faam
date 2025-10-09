"""
Data validation and consistency
"""

# Import functions from other scripts
import sys

sys.path.append(".")
from utilities import *
from wikidata import *


def object_type2csv(
	faam_kb, object_type
):  # returns a csv list with basic metadata for a given object type. You can un-comment the Instance of lines to get extra info
	object_type_dict = []

	for item in faam_kb["items"]:
		if item["metadata"]["object_type"][0]["value"] == object_type:
			try:
				#instance_of = wb_get_property_data(item["metadata"]["qid"][0]["value"],"P31")[0]
				object_type_dict.append(
					{
						"id": item["id"],
						"qid": item["metadata"]["qid"][0]["value"],
						"nodegoat_id": item["metadata"]["nodegoat_id"][0]["value"],
						"label": item["metadata"]["label"][0]["value"],
						"qid_label": item["metadata"]["qid"][0]["label"]
						#"instance_of": instance_of
					}
				)
			except IndexError: # no instance of statement
				try:
					object_type_dict.append(
						{
							"id": item["id"],
							"qid": item["metadata"]["qid"][0]["value"],
							"nodegoat_id": item["metadata"]["nodegoat_id"][0]["value"],
							"label": item["metadata"]["label"][0]["value"],
							"qid_label": item["metadata"]["qid"][0]["label"]
							#"instance_of": ""
						}
					)
				except KeyError: # no label found
					object_type_dict.append(
						{
							"id": item["id"],
							"qid": item["metadata"]["qid"][0]["value"],
							"nodegoat_id": item["metadata"]["nodegoat_id"][0]["value"],
							"label": item["metadata"]["label"][0]["value"],
							"qid_label": ""
							#"instance_of": ""
						}
					)

			except KeyError:
				try:
					object_type_dict.append(
						{"id": item["id"], 
						"nodegoat_id": item["metadata"]["nodegoat_id"][0]["value"],
						"label": item["metadata"]["label"][0]["value"]}
					)
				except KeyError:
					print(f"No label for {item["id"]}?")
					input()
					object_type_dict.append(
						{"id": item["id"], "label": ""}
					)

	# export to csv
	dict2csv(object_type_dict, os.path.join("tmp", object_type + "_list.csv"))
	print(f"Number of items for {object_type}: {len(object_type_dict)}")


def cross_references_duplicates(faam_kb):  # remove duplicates from cross-references
	cleaned_cross_references = 0
	for item in faam_kb["items"]:
		if len(item["cross-references"].keys()) > 0:
			# check for duplicates
			clean = False
			for key in item["cross-references"].keys():
				cross_ref_ids = [cross_ref["id"] for cross_ref in item["cross-references"][key]]
				if len(cross_ref_ids) != len(set(cross_ref_ids)):
					cross_references = []
					# delete duplicates
					for cross_ref_id in set(cross_ref_ids):
						# retrieve reference and append it to new cross_references
						cross_references.append(list(filter(lambda x: x["id"] == cross_ref_id, item["cross-references"][key]))[0])

					#print(f"Current item: {item["id"]}")
					#print(f"Former cross-ref: {len(item["cross-references"][key])} \n ")
					#print(f"New cross-ref: {len(cross_references)}")
					#print(cross_references[0])
					#input()

					# upload cross references
					item["cross-references"][key] = cross_references
					clean = True 

			if clean:
				cleaned_cross_references +=1

	#export
	print(f"Number of item cleaned: {cleaned_cross_references}")
	return faam_kb


def double_label_to_aliases(faam_kb):
	for item in faam_kb["items"]:
		# cleanup labels
		if len(item["metadata"]["label"]) > 1:
			labels = [label["value"] for label in item["metadata"]["label"]]
			if len(labels) != len(set(labels)):  # duplicates!
				#print(f"Current item: {item['id']}")
				# keep first label, the rest goes to aliases
				for alias in item["metadata"]["label"][1:]:
					item["metadata"]["aliases"].append(alias)
				item["metadata"]["label"] = [item["metadata"]["label"][0]]

		# cleanup aliases
		try:
			if len(item["metadata"]["aliases"]) > 1:
				try:
					aliases = [alias["value"] for alias in item["metadata"]["aliases"]]
				except TypeError:
					print(item["metadata"]["aliases"])
					input()
				if len(aliases) != len(set(aliases)):  # duplicates!
					unique_aliases = list(set(aliases))
					# print(f"Current item: {item['id']}")
					# print(f"Old aliases: {item["metadata"]["aliases"]}")
					item["metadata"]["aliases"] = [
						{"type": "string", "value": alias} for alias in unique_aliases
					]
					# print(f"New aliases: {item["metadata"]["aliases"]}")
		except KeyError:  # no aliases key
			item["metadata"]["aliases"] = []

	return faam_kb

def labels_validation(faam_kb):  # label should be unique and not empty
	problematic_labels = []
	for item in faam_kb["items"]:
		if len(item["metadata"]["label"]) > 1:
			problematic_labels.append(
				{
					"id": item["id"],
					"labels": "|".join(
						[label["value"] for label in item["metadata"]["label"]]
					),
				}
			)

		elif item["metadata"]["label"][0]["value"] == "":
			problematic_labels.append({"id": item["id"], "labels": ""})

	# export to csv
	dict2csv(problematic_labels, os.path.join("tmp", "problematic_labels.csv"))
	print(f"Number of problematic labels: {len(problematic_labels)}")

def qualifiers_validation(
	faam_kb, nodegoat2faam_kb_filename
):  # check for redundant qualifiers or uneven number of them
	# import mapping
	nodegoat2faam_kb = csv2dict(nodegoat2faam_kb_filename)

	object_type_statement = list(
		filter(lambda x: x["data_type"] == "statement", nodegoat2faam_kb)
	)

	statements_list = [
		statement["faam_property"] for statement in object_type_statement
	]

	number_qualifiers = [
		len(statement["qualifiers"].split(",")) for statement in object_type_statement
	]

	print(f"Properties of type statement: {object_type_statement}")
	problematic_qualifiers = []

	for item in faam_kb["items"]:
		for prop in item["statements"].keys():
			if prop in statements_list:
				# check qualifiers
				for statement in item["statements"][prop]:
					# find duplicate qualifiers
					qual_ids = [qual["value"] for qual in statement["qualifiers"]]
					if len(qual_ids) != len(set(qual_ids)):  # there are duplicates
						if "" not in qual_ids:
							problematic_qualifiers.append(
								{
									"id": item["id"],
									"statement": statement["value"],
									"qualifiers": "|".join(qual_ids),
								}
							)
					# check if number of statement is conform
					if len(qual_ids) not in number_qualifiers:
						problematic_qualifiers.append(
							{
								"id": item["id"],
								"statement": statement["value"],
								"qualifiers": "|".join(qual_ids),
							}
						)

	# export to csv
	dict2csv(problematic_qualifiers, os.path.join("tmp", "problematic_qualifiers.csv"))
	print(f"Number of problematic qualifiers: {len(problematic_qualifiers)}")


def missing_fields_text_with_id(
	faam_kb, missing_properties=["note", "sections"], control_property="related item"
):  # nodegoat csv import does not import HMTL code of fields if embedded IDs are present
	missing_properties_list = []

	for item in faam_kb["items"]:
		if "control_property" in item["statements"].keys():
			if len(item["statements"][control_property]) > 0:
				missing_properties_list.append(
					{
						"id": item["id"],
						"nodegoat_id": item["metadata"]["nodegoat_id"][0]["value"],
					}
				)

	# export to csv
	dict2csv(
		missing_properties_list, os.path.join("tmp", "missing_properties_list.csv")
	)
	print(f"Number of missing properties: {len(missing_properties_list)}")
