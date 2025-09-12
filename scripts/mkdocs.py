"""
Scritpts to generate Mkdocs Markdown documentation pages

"""

import sys
# Markdown module
import snakemd
# graph visualization modules 
from pyvis.network import Network
import networkx as nx
import matplotlib
import matplotlib.pyplot

sys.path.append(".")
from utilities import *
from faam_kb import *

# Pyvis functions

def add_node_faam(item,uuid_int,net,graph_attributes_type,nodes_list):
	# append new item to node
	attributes = list(filter(lambda x: x["type"] == item["metadata"]["object_type"][0]["value"],graph_attributes_type))[0]
	if "thumb" in item["resources"]:
		image = f"""<img src="{item["resources"]["thumb"][0]["base_url"]}{item["resources"]["thumb"][0]["value"]}" width="250" height="200">"""
	elif "image" in item["resources"]:
		image = f"""<img src="{item["resources"]["image"][0]["base_url"]}{item["resources"]["image"][0]["value"]}" width="250" height="200">"""
	else:
		image = "<p></p>"
	title = (
	            """
			<body>
			<h3> <a href='./"""
	            + item["id"]
	            + """.md'>"""
	            + item["metadata"]["label"][0]["value"]
	            + """</a></h3>
			<p>"""
	            + item["metadata"]["description"][0]["value"]
	            + """</p>"""
	            + image +
				"""
			</body>
			"""
	        )
	nodes_list.append(uuid_int)
	net.add_node(item["id"],
					label = item["metadata"]["label"][0]["value"],
					color= attributes["color_code"],
					value= attributes["value"],
					title = title
					)

	return net,nodes_list

def generate_network(faam_kb,graph_attributes_type_filename,out_dir):
	# generate integer list for bisect query
	uuid_list,item_list = generate_uuid_list(faam_kb)
	nodes_list = []
	graph_attributes_type = csv2dict(graph_attributes_type_filename)
	# initialize network
	net = nx.Graph()
	# GENERATE NODES
	for item in faam_kb["items"]:
		# get integer representation of item id
		uuid_int = shortuuid.decode(item["id"]).int
		# query value in uuid_list
		try:
			index = bisect_left(nodes_list,uuid_int)
			if item["id"] == item_list[index]["id"]:
				# already present
				pass
			else:
				net,nodes_list = add_node_faam(item,uuid_int,net,graph_attributes_type,nodes_list)
				
		except IndexError: # item not in list
			net,nodes_list = add_node_faam(item,uuid_int,net,graph_attributes_type,nodes_list)

	# ADD EDGES

	for item in faam_kb["items"]:
		for prop in item["statements"].keys():
			if item["statements"][prop][0]["type"] == "item":
				for statement in item["statements"][prop]:
					net.add_edge(item["id"], statement["value"], weight=10)

			if item["statements"][prop][0]["type"] == "statement": # consider all qualifiers
				for statement in item["statements"][prop]:
					for qual in statement["qualifiers"]:
						if qual["type"] == "item":
							net.add_edge(statement["value"], qual["value"], weight=5)

	# Save Network serialization

	net_dict = nx.node_link_data(net, edges="links")
	dict2json(net_dict,os.path.join(out_dir,"pyvis_graph","network-"+get_current_date()+".json"))
	return net

def pyvis_visualization(net,net_filename):
	layout = nx.spring_layout(net)
	visualization=Network(height="1200px", width="1200px", bgcolor="#1C1A19", font_color="#f8f7f4", directed=False,select_menu=False,filter_menu=False,notebook=False)
	visualization.barnes_hut()
	visualization.from_nx(net)
	visualization.toggle_physics(False)
	visualization.show_buttons(filter_=['nodes','physics'])
	#for i in visualization.nodes:
			#node_id = i["id"]
			#if node_id in layout:
				#i["x"], i["y"] = layout[node_id][0]*1000, layout[node_id][1]*1000
	options = """
			var options = {
   					"configure": {
						"enabled": false
   							},
  					"edges": {
					"color": {
	  				"inherit": true
						},
					"smooth": false
  					},
  					"physics": {
					"barnesHut": {
	  				"gravitationalConstant": -12050
					},
					"minVelocity": 0.75
  					}
					}
				"""
	visualization.set_options(options)
	#visualization.show(net_filename+'.html',notebook=False)
	#input()
	#visualization.write_html(name='example.html',notebook=False,open_browser=False)
	visualization.save_graph(net_filename+".html")

def generate_distance_matrix(net,max_dist):
	print("Distance matrix operations...")
	distances = dict(nx.all_pairs_shortest_path_length(net,cutoff=max_dist))
	return distances

def pyvis_visualization_local(center_node,net,distances,base_path):
	sub_net_nodes = []
	print("Generating subgraph...")
	for node in distances[center_node]:
			sub_net_nodes.append(node)
	sub_net = net.subgraph(sub_net_nodes)
	print("Getting labels...")
	labels = nx.get_node_attributes(sub_net, "label")
	print("Render visualization...")
	#print(sub_net.nodes())
	#print(sub_net.edges())
	pyvis_visualization(sub_net,os.path.join(base_path,str(center_node)))

def generate_faam_graphs(faam_kb,graph_attributes_type_filename,out_dir):
	# generate whole network
	print("Generating network...")
	net = generate_network(faam_kb,graph_attributes_type_filename,out_dir)
	# generate distance matrix
	print("Generating distance matrix. It might take a while!")
	distances = generate_distance_matrix(net,max_dist=2)
	print("Generating individual graph visualizations in HTML using pyvis...")

	for node in net:
		pyvis_visualization_local(node,net,distances,os.path.join(out_dir,"networks"))



"""generate a JSON file with all metadata related to a specific object. 
This file could be used for dynamic rendering van lists (via Javascript) and
export option for users."""
def generate_resource_items(faam_kb,nodegoat2faam_kb_filename,out_dir):
	nodegoat2faam_kb = csv2dict(nodegoat2faam_kb_filename)
	for item in faam_kb["items"]:
		data = item
		dict2json(data,os.path.join(out_dir,"json_items",f"{item["id"]}.json"))
		item["resources"]["JSON"] = [
			{
				"type": "url",
				"base_url": "./",
				"value": item["id"]+".json"

			}
		]
		# generate RDF Turtle serialization
		generate_rdf_item(item,nodegoat2faam_kb,os.path.join(out_dir,"pages",item["id"]+".ttl"))
		item["resources"]["RDF"] = [
			{
				"type": "url",
				"base_url": "./",
				"value": item["id"]+".ttl"
			}

		]
		# generate CSV serialization
		generate_csv_item(item,nodegoat2faam_kb,os.path.join(out_dir,"pages",item["id"]+".csv"),separator="|")
		item["resources"]["CSV"] = [
			{
				"type": "url",
				"base_url": "./",
				"value": item["id"]+".csv"
			}

		]

	return faam_kb

"""generate Turtle RDF serialization of metadata according to Nodegoat2LOD mapping"""
def generate_rdf_item(item,nodegoat2faam_kb,file_path):
	# TO BE CONTINUED
	pass

def generate_csv_item(item,nodegoat2faam_kb,file_path,separator): # TO BE TESTED
	# serialize JSON item to CSV
	csv_dict = []
	for category in item.keys():
		for faam_property in item[category].keys():
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
						csv_dict.append({
							"category": category,
							"faam_property": faam_property,
							"type": statement["type"],
							"value": statement["value"],
							"base_url": statement["base_url"]
							})
					elif statement["type"] == "item":
						csv_dict.append({
							"category": category,
							"faam_property": faam_property,
							"type": statement["type"],
							"value": statement["value"],
							"label": statement["label"]
							})
					elif statement["type"] == "statement":
						qualifiers = ""
						for qual in statement["qualifiers"]:
							qualifiers = qualifiers + qual["value"] + separator
						# get rid of last separator
						if len(qualifiers) > 1:
							qualifiers = qualifiers[:-1]
						csv_dict.append({
							"category": category,
							"faam_property": faam_property,
							"type": statement["type"],
							"value": statement["value"],
							"label": statement["label"],
							"qualifiers": qualifiers
							}) 
				except IndexError: # case of not list keys such as id and uuid_num
					pass

	# generate CSV file
	dict2csv(csv_dict,file_path)

# Image Carousel using GitHub API

def generate_image_carousel(faam_kb,github_repo_url): # TO BE CONTINUED 
	for item in faam_kb["items"]:
		if item["metadata"]["object_type"][0]["value"] == "manifestation":
			# get GitHub repository from resources
			GitHub_path = item["resources"]["GitHub"][0]["value"].replace("https://github.com/nicholascornia89/","")
			print(f"GitHub path: {GitHub_path}")

			# call API for list of images.

			# render raw images form GitHub https://raw.githubusercontent.com/nicholascornia89/{repoName}/main/{path}/{image_name}.jpg

			# add images to carousel using HTML code

			# Have a look at https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28

			pass







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
					for button in block["content"]:
						if "GitHub" in button["label"]:
							githuburl = item["resources"]["GitHub"][0]["value"]
							doc.add_raw(f"""[{button["label"]} {button["icon"]}]({githuburl}){{.md-button}}""") 
						else: # file serializations
							doc.add_raw(f"""[{button["label"]} {button["icon"]}](./{item["id"]}{button["extension"]}){{.md-button}}""")

				elif block["format"] == "embed":
					for embed in block["content"]:
						doc.add_raw(f"""<iframe src="{embed["base_url"]}{item[embed["category"]["property"]]["value"]}{embed["extension"]}" height="{block["attributes"]["heigth"]}" width="{block["attributes"]["width"]}" title="{item[embed["category"]["property"]]["value"]}"></iframe>""")

				# statements
				elif block["format"] == "quote":
					doc.add_raw(f"""{block["collapse"]} {block["icon"]} "{block["label"]}" """)
					if block["data_format"] == "list":
						statements = item[block["content"][0]["category"]][block["content"][0]["property"]]
						statements_list = []
						for statement in statements:
							if statement["value"] != "":
								# check if item (hyperlink needed), otherwise only string
								if statement["type"] == "item":
									# I am assuming all items have FAAM UUID
									statements_list.append(sneakmd.Inline(statement["label"]).link(f"./{statement["id"]}.md"))
								elif statement["type"] == "externalid":
									statements_list.append(sneakmd.Inline(statement["label"]).link(f"{statement[base_url]}{statement["value"]}"))
								else:
									statements_list.append(sneakmd.Inline(statement["value"]))

						# create unordered list. p.s. Tab is fundamental for layout structuring
						for element in statements_list:
							doc.add_raw(f"""	- {element}""")
					elif block["data_format"] == "table":
						headings = []
						for element in block["content"]:
							if element["type"] == "statement":
								headings.append(element["label"])
								# append qualifiers in `qualifiers` key
								for qual in element["qualifiers"]:
									headings.append(qual)

						# I am assuming uniform length statements!
						table_raws = []
						for statement in item[block["content"][0]["category"]][block["content"][0]["property"]]:
							raw = []
							for heading in headings: # assume heading = property and qualifiers key
								if statement["value"] != "":
									if statement["type"] == "statement":
										raw.append(sneakmd.Inline(statement["label"]).link(f"./{statement["id"]}.md"))
										for qual in statement["qualifiers"]:
											if qual in headings:
												if qual["type"] == "item":
													raw.append(sneakmd.Inline(qual["label"]).link(f"./{qual["value"]}.md"))
												else:
													raw.append(sneakmd.Inline(qual["value"]))
							table_raws.append(raw)

						# alignment (center)
						table_align = [snakemd.Table.Align.CENTER for i in range(len(headings))]

						# append table to document

						doc.add_table(headings,table_raws,aling=table_align)



						
						
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
