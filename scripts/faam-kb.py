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
				"metadata": [
				{"id": "FAAM UUID",
				"nodegoat_id": "old Nodegoat ID",
				"qid": "Wikidata QID",
				"type": "object type for templating"
				"label": "preferred label",
				"aliases": ["alternative labels"],
				"description": "short string"
				]
				"statements": [
								"property_name": [
									{"label": "label_to be_shown", "data_type": "string", "value": "string value"},
									{"label": "label_to be_shown", "data_type": "externalid", "value": "id with baseurl"},
									{"label": "label_to be_shown", "data_type": "item", "value": "uuid"},
									{"label": "label_to be_shown", "data_type": "date", "value": "date"},
									{"label": "label_to be_shown", "data_type": "url", "value": "url"}

								
								]


				}
				]
}
"""

nodegoat2faam_kb_filename = os.path.join("mapping", "nodegoat2faam_kb_mapping.csv")
