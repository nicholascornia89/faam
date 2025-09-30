"""
Scritpts to generate Mkdocs Markdown documentation pages

"""

import sys
# Markdown module
import snakemd


sys.path.append(".")
from utilities import *
from data_visualization import *
from faam_kb import *
from rdf import *


"""generate a JSON file with all metadata related to a specific object. 
This file could be used for dynamic rendering van lists (via Javascript) and
export option for users."""
def generate_resource_items(faam_kb,nodegoat2faam_kb_filename,out_dir):
	nodegoat2faam_kb = csv2dict(nodegoat2faam_kb_filename)
	for item in faam_kb["items"]:
		item["resources"]["JSON"] = [
			{
				"type": "url",
				"base_url": "http://nicholascornia89.github.io/faam/json/",
				"value": item["id"]+".json"

			}
		]
		# generate RDF Turtle serialization
		generate_rdf_item(item,nodegoat2faam_kb,os.path.join(out_dir,"rdf_items",item["id"]+".ttl"))
		item["resources"]["RDF"] = [
			{
				"type": "url",
				"base_url": "http://nicholascornia89.github.io/faam/rdf/",
				"value": item["id"]+".ttl"
			}

		]
		# generate CSV serialization
		generate_csv_item(item,nodegoat2faam_kb,os.path.join(out_dir,"csv_items",item["id"]+".csv"),separator="|")
		item["resources"]["CSV"] = [
			{
				"type": "url",
				"base_url": "http://nicholascornia89.github.io/faam/csv/",
				"value": item["id"]+".csv"
			}

		]

		data = item
		dict2json(data,os.path.join(out_dir,"json_items",f"{item["id"]}.json"))

	return faam_kb

def generate_csv_item(item,nodegoat2faam_kb,file_path,separator):
	# serialize JSON item to CSV
	csv_dict = []
	for category in item.keys():
		if category in ["metadata","statements"]:
			for faam_property in item[category].keys():
				if faam_property not in ["id","uuid_num"]:
					for statement in item[category][faam_property]:
						try:
							if statement["type"] in ["string","id","date","html"] :
								csv_dict.append({
									"category": category,
									"faam_property": faam_property,
									"type": statement["type"],
									"value": statement["value"]
									})
							elif statement["type"] in ["externalid","image"]:
								try:
									csv_dict.append({
										"category": category,
										"faam_property": faam_property,
										"type": statement["type"],
										"value": statement["value"],
										"base_url": statement["base_url"]
										})
								except KeyError:
									csv_dict.append({
										"category": category,
										"faam_property": faam_property,
										"type": statement["type"],
										"value": statement["value"]
										})

							elif statement["type"] == "item":
								try: 
									csv_dict.append({
										"category": category,
										"faam_property": faam_property,
										"type": statement["type"],
										"value": statement["value"],
										"label": statement["label"]
										})
								except KeyError:
									csv_dict.append({
										"category": category,
										"faam_property": faam_property,
										"type": statement["type"],
										"value": statement["value"]
										})

							elif statement["type"] == "statement":
								qualifiers = ""
								for qual in statement["qualifiers"]:
									qualifiers = qualifiers + qual["value"] + separator
								# get rid of last separator
								if len(qualifiers) > 1:
									qualifiers = qualifiers[:-1]
								try:
									csv_dict.append({
										"category": category,
										"faam_property": faam_property,
										"type": statement["type"],
										"value": statement["value"],
										"label": statement["label"],
										"qualifiers": qualifiers
										})
								except KeyError:
									#print(f'Id: {item["id"]} \n statement without label: {statement}')
									csv_dict.append({
										"category": category,
										"faam_property": faam_property,
										"type": statement["type"],
										"value": statement["value"],
										"qualifiers": qualifiers
										})

						except Exception: # case of not list keys such as id and uuid_num
							print(f"Problem for item {item["id"]}")
							input()
							pass

	# generate CSV file
	dict2csv(csv_dict,file_path)

# Generate Markdown page for each object in object_list

def generate_pages(faam_kb, nodegoat2faam_kb_filename, out_dir):
	# import mapping
	nodegoat2faam_kb = csv2dict(nodegoat2faam_kb_filename)
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
		print(f"""Current item: {item["id"]}""")
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
				#print(f"Current block: \n {block} \n")
				if block["format"] == "string":
					doc.add_raw(f"""{block["content"][0]["value"]}""")
				# headings
				if block["format"] == "heading":
					if key == "title":
						doc.add_heading(f"{item["metadata"]["label"][0]["value"]} ({item["id"]})")
						doc.add_raw("""---""")
					else:	
						doc.add_heading(block["content"][0]["label"], block["level"])
						doc.add_raw("""---""")
				# images
				elif block["format"] == "image":
					image_statement = item[block["content"][0]["category"]][
						block["content"][0]["property"]
					]
					if image_statement != "":
						doc.add_raw(
							f"""<img style="{block["attributes"]["style"]}" src="{image_statement[0]["base_url"]}{image_statement[0]["value"]}" width="{block["attributes"]["width"]}" height="{block["attributes"]["height"]}">"""
						)
					else: # add default image if empty
						doc.add_raw(
							f"""<img style="{block["attributes"]["style"]}" src="{block["redirect_image"]}" width="{block["attributes"]["width"]}" height="{block["attributes"]["height"]}">"""
						)
				elif block["format"] == "button":
					buttons = []
					for button in block["content"]:
						if "GitHub" in button["label"]:
							try:
								githuburl = item["resources"]["GitHub"][0]["value"]
								buttons.append(f"""[{button["label"]} {button["icon"]}]({githuburl}){{.md-button}}""")
							except IndexError:
								print("No GitHub url")
								input() 
						else: # file serializations
							resource_url = f"""{item[button["category"]][button["property"]][0]["base_url"]}{item[button["category"]][button["property"]][0]["value"]}"""
							buttons.append(f"""[{button["label"]} {button["icon"]}]({resource_url}){{.md-button}}""")
					doc.add_raw(" ".join(buttons))

				elif block["format"] == "embed":
					for embed in block["content"]:
						cat = embed["category"]
						prop = embed["property"]
						width = block["attributes"]["width"]
						height = block["attributes"]["height"]
						doc.add_raw(f"""<iframe src="{embed["base_url"]}{item[cat][prop][0]["value"]}{embed["extension"]}" height="{height}" width="{width}" title="{item[cat][prop][0]["value"]}"></iframe>""")

				# statements
				elif block["format"] == "quote":
					if block["data_format"] == "string":
						try:
							statements = item[block["content"][0]["category"]][block["content"][0]["property"]]
							if len(statements) > 0: # append block only if statements are not empty
								doc.add_raw(f"""{block["collapse"]} {block["icon"]} "{block["label"]}" """)
								statements_list = []
								for statement in statements:
									if statement["value"] != "":
										# check if item (hyperlink needed), otherwise only string
										if statement["type"] == "item":
											# I am assuming all items have FAAM UUID
											statements_list.append(snakemd.Inline(statement["label"]).link(f"{statement["value"]}"))
										elif statement["type"] == "externalid":
											statements_list.append(snakemd.Inline(statement["label"]).link(f"{statement["base_url"]}{statement["value"]}"))
										else:
											statements_list.append(snakemd.Inline(statement["value"]))

								# create unordered list. p.s. Tab is fundamental for layout structuring
								for element in statements_list:
									doc.add_raw(f"""	{element}""")
						except KeyError: # statement not found
							pass

					elif block["data_format"] == "list":
						statements = item[block["content"][0]["category"]][block["content"][0]["property"]]
						if len(statements) > 0:
							doc.add_raw(f"""{block["collapse"]} {block["icon"]} "{block["label"]}" """)
							statements_list = []
							for statement in statements:
								if statement["value"] != "":
									# check if item (hyperlink needed), otherwise only string
									if statement["type"] == "item":
										# I am assuming all items have FAAM UUID
										statements_list.append(snakemd.Inline(statement["label"]).link(f"{statement["value"]}"))
									elif statement["type"] == "externalid":
										statements_list.append(snakemd.Inline(statement["label"]).link(f"{statement[base_url]}{statement["value"]}"))
									else:
										statements_list.append(snakemd.Inline(statement["value"]))

							# create unordered list. p.s. Tab is fundamental for layout structuring
							for element in statements_list:
								doc.add_raw(f"""	- {element}""")
					elif block["data_format"] == "table":
						headings = []
						# generate headings case with statement and qualifiers
						if "qualifiers" in block["content"][0].keys():
							for element in block["content"]:
								if element["type"] == "statement":
									headings.append(element["label"])
									# append qualifiers in `qualifiers` key
									for qual in element["qualifiers"]:
										headings.append(qual)
							print(f"Headings: {headings}")

							statements = item[block["content"][0]["category"]][block["content"][0]["property"]]
							if len(statements) > 0:
								doc.add_raw(f"""{block["collapse"]} {block["icon"]} "{block["label"]}" """)

								# I am assuming uniform length statements!
								table_raws = []
								for statement in item[block["content"][0]["category"]][block["content"][0]["property"]]:
									raw = []
									for heading in headings: # assume heading = property and qualifiers key
										if statement["value"] != "":
											if statement["type"] == "statement":
												raw.append(snakemd.Inline(statement["label"]).link(f"{statement["value"]}"))
												for qual in statement["qualifiers"]:
													if qual in headings:
														if qual["type"] == "item":
															raw.append(snakemd.Inline(qual["label"]).link(f"{qual["value"]}"))
														else:
															raw.append(snakemd.Inline(qual["value"]))
									table_raws.append(raw)

						else: # case with normal items
							for element in block["content"]:
								headings.append(element["label"])

							statements = item[block["content"][0]["category"]][block["content"][0]["property"]]
							if len(statements) > 0:
								doc.add_raw(f"""{block["collapse"]} {block["icon"]} "{block["label"]}" """)

								# I am assuming uniform length statements!
								table_raws = []
								for i in range(len(item[block["content"][0]["category"]][block["content"][0]["property"]])):
									raw = []
									for element in block["content"]:
										try:
											current_item = item[element["category"]][element["property"]][i]
										except IndexError:
											# produce empty item
											current_item = {"type": "string", "value": "", "label": "", "base_url": ""}
										if current_item["type"] == "item":
											raw.append(snakemd.Inline(current_item["label"]).link(f"{current_item["value"]}"))

										elif current_item["type"] == "externalid":
											if "wikidata.org" in current_item["base_url"]:
												try:
													raw.append(snakemd.Inline(current_item["label"]).link(f"""{current_item["base_url"]}{current_item["value"]}"""))
												except KeyError:
													print(f"QID without label: {current_item["value"]}")
													raw.append(snakemd.Inline(current_item["value"]).link(f"""{current_item["base_url"]}{current_item["value"]}"""))

											else:
												raw.append(snakemd.Inline(current_item["value"]).link(f"""{current_item["base_url"]}/{current_item["value"]}"""))

										else: # string and date cases
											raw.append(snakemd.Inline(current_item["value"]))
								table_raws.append(raw)

						# alignment (center)
						table_align = [snakemd.Table.Align.CENTER for i in range(len(headings))]
						# append table to document
						doc.add_table(headings,table_raws,align=table_align,indent=4)

				# cross-references
				elif block["format"] == "grid":
					if block["object_type"] in item[block["category"]].keys():
						# opening div for Material grid
						doc.add_raw(f"""<div class="grid cards" markdown>""")
						for reference in item[block["category"]][block["object_type"]]:
							# add title based on label
							#doc.add_raw(f"""{snakemd.Inline("")}""")
							doc.add_raw(f"""-	__[{reference["label"]}]({reference["id"]})__""")
							#doc.add_raw(f"""{snakemd.Inline("")}""")
							# add image if exists
							if "image" in reference.keys():
								if reference["image"]["value"] != "":
									doc.add_raw(f"""	![Image]({reference["image"]["base_url"]}{reference["image"]["value"]}){{align={block["attributes"]["align"]} width="{block["attributes"]["width"]}" height="{block["attributes"]["height"]}"}} """)
								else:
									doc.add_raw(f"""	![Image]({block["redirect_image"]}){{align={block["attributes"]["align"]} width="{block["attributes"]["width"]}" height="{block["attributes"]["height"]}"}} """)
							elif "thumb" in reference.keys():
								if reference["thumb"]["value"] != "":
									doc.add_raw(f"""	![Image]({reference["thumb"]["base_url"]}{reference["thumb"]["value"]}){{align={block["attributes"]["align"]} width="{block["attributes"]["width"]}" height="{block["attributes"]["height"]}"}} """)
								else:
									doc.add_raw(f"""	![Image]({block["redirect_image"]}){{align={block["attributes"]["align"]} width="{block["attributes"]["width"]}" height="{block["attributes"]["height"]}"}} """)
							# add description
							doc.add_raw(f"""	{snakemd.Inline(reference["description"])}""")
						#close div
						doc.add_raw(f"""</div>""")







						
						
			# save .md file
			doc.dump(item["id"], directory=pages_dir)
			#input()

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
