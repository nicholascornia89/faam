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

nodegoat2faam_kb_filename = os.path.join("mapping", "nodegoat2faam_kb_mapping.csv")


# Generate FAAM Knowledge Base JSON from latest Nodegoat export
def generate_faam_kb(d):
    count_no_label = 0
    # Import mapping
    faam_kb_mapping = csv2dict(nodegoat2faam_kb_filename)
    faam_kb = {"items": []}
    for object_type in d.keys():
        for obj in d[object_type]:
            item = {
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
                    for statement in obj[field]:
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
                    item["metadata"]["label"][0] = [
                        {"type": "string", "value": obj["Wikidata Label"][0]}
                    ]
                except KeyError:
                    count_no_label += 1
            # append item to knowledge base
            faam_kb["items"].append(item)

    print(f"Items without label: {count_no_label}")

    return faam_kb
