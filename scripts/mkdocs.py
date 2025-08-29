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


def generate_pages(d, objects_list, out_dir):
    # generate directory for Markdown pages
    pages_dir = os.path.join(out_dir, "pages")
    if not os.path.exists(pages_dir):
        os.makedirs(pages_dir)

    for item in objects_list:
        doc = snakemd.Document()
        # adding properties
        doc.add_raw(
            f"""---\n
hide:\n 
- navigation\n
title: {item["id"]}\n
tags: {item["type"]}\n 
---
"""
        )
        doc.add_heading("Title", 1)
        doc.add_horizontal_rule()
        doc.add_paragraph("Lorem ipsum...")

        # TO BE CONTINUED, following template

        """ Possible methods
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
    # Populate metadata according to template
    for object_type in d.keys():
        for obj in d[object_type]:
            pass
            # get right template code via function.
            # TO BE CONTINUED

        # save .md file
        doc.dump(item["id"], directory=pages_dir)
        input()
