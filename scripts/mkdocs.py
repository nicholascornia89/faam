"""
Scritpts to generate Mkdocs Markdown documentation pages

"""

import sys
import snakemd

sys.path.append(".")
from utilities import *

# Generate Markdown page for each object in object_list

"""generate a JSON file with all metadata related to a specific object. 
This file could be used for dynamic rendering van lists (via Javascript) and
export option for users."""


def generate_page_json(obj, file_path):
	# save object metadata in `metadata` key.
	data = {}
	data["metadata"] = obj
	# generate graph representation according to D3.js standards
	graph = {}
	"""example of node
	{"id": "id for links", "label": "text on node", "group": "type node", "description": "text when hovered", "size": 100, "url": "hyperlink" }

	"""
	nodes = []
	"""example of link (edges)
	{"source": "node id", "target": "node id"}
	"""
	links = []

	for field in obj:
		# TO BE CONTINUED
		pass


"""generate Turtle RDF serialization of metadata according to Nodegoat2LOD mapping"""


def generate_page_rdf(obj, file_path, nodegoat2rdf_mapping):
	# TO BE CONTINUED
	pass


def generate_pages(faam_kb, nodegoat2faam_kb, out_dir):
	# generate directory for Markdown pages
	pages_dir = os.path.join(out_dir, "pages")
	# Templates are stored in a JSON file with Markdown blocks
	templates_dir = os.path.join("mapping", "templates")

	# generate template list
	templates = json2dict(os.path.join(templates_dir, "object_type_templates.json"))

	if not os.path.exists(pages_dir):
		os.makedirs(pages_dir)

	# make a Markdown document for each item of the knowledge base

	for item in faam_kb["items"]:
		doc = snakemd.Document()
		# adding properties
		doc.add_raw(
			f"""---\n
hide:\n 
- title\n
- toc\n
title: {item["id"]}\n
tags: {item["metadata"]["object_type"][0]["value"]}\n 
---
"""
		)
		# adding blocks according to template
		object_type = item["metadata"]["object_type"][0]["value"]
		if object_type in templates.keys():
			item_template = templates[object_type]

			# go through the listed blocks in template
			for key in item_template.keys():
				block = item_template[key]
				print(f"Current block: \n {block} \n")
				# headings
				if block["format"] == "heading":
					if key == "title":
						doc.add_heading(f"{item["metadata"]["label"][0]["value"]} ({item["id"]})")
					else:	
						doc.add_heading(block["content"][0]["label"], block["level"])
				# images
				elif block["format"] == "image":
					image_statement = item[block["content"][0]["category"]][
						block["content"][0]["property"]
					]
					doc.add_raw(
						f"""<img style="{block["attributes"]["style"]}" src="{image_statement[0]["base_url"]}{image_statement[0]["value"]}" width="{block["attributes"]["width"]}" height="{block["attributes"]["height"]}">"""
					)
				elif block["format"] == "button":
					pass
				# statements
				elif block["format"] == "quote":
					if block["data_format"] == "list":
						statements = item[block["content"][0]["category"]][block["content"][0]["property"]]
						statements_list = []
						for statement in statements:
							# check if item (hyperlink needed), otherwise only string
							if statement["type"] == "item":
								# I am assuming all items have FAAM UUID
								statements_list.append(sneakmd.Inline(statement["value"]).link(f"./{statement["id"]}.md"))
							else:
								statements_list.append(sneakmd.Inline(statement["value"]))
								



			# save .md file
			doc.dump(item["id"], directory=pages_dir)
			input()

			# TO BE CONTINUED, following template

			""" Possible methods
			# add link to text by using snakemd.Inline("text").link("url")
			doc.add_horizontal_rule()
			doc.add_heading("Label",1)
			doc.add_ordered_list(["first", "second"])
			doc.add_unordered_list(["first", "second"])
			doc.add_paragraph("Lorem ipsum...")
			table_header = ["first", ["second"]]
			table_rows = [["1st", "raw"], ["2nd", "raw"]]
			table_align = [snakemd.Table.Align.CENTER, snakemd.Table.Align.CENTER]
			doc.add_table(header, rows, align=align)
			"""
