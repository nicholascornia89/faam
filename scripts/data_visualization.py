"""
Scripts for pyvis network visualization and image carousel
"""

# Import functions from other scripts
import sys

sys.path.append(".")
from utilities import *
from faam_kb import *

# graph visualization modules 
from pyvis.network import Network
import networkx as nx
import matplotlib
import matplotlib.pyplot

# GitHub API
from github import Github, Auth

# Dominate Generate HTML page
import dominate
from dominate.tags import *
from dominate.util import raw

### Pyvis graph network visualization

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
			for statement in item["statements"][prop]:
				if statement["type"] == "item":
					net.add_edge(item["id"], statement["value"], weight=10)

				if statement["type"] == "statement":
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
					"gravitationalConstant": -120050
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
	#print("Generating subgraph...")
	for node in distances[center_node]:
			sub_net_nodes.append(node)
	sub_net = net.subgraph(sub_net_nodes)
	#print("Getting labels...")
	labels = nx.get_node_attributes(sub_net, "label")
	#print("Render visualization...")
	#print(sub_net.nodes())
	#print(sub_net.edges())
	pyvis_visualization(sub_net,os.path.join(base_path,str(center_node)))

def generate_faam_graphs(faam_kb,graph_attributes_type_filename,out_dir):
	# generate whole network
	print("Generating network...")
	net = generate_network(faam_kb,graph_attributes_type_filename,out_dir)
	# generate distance matrix
	print("Generating distance matrix. It might take a while!")
	distances = generate_distance_matrix(net,max_dist=1)
	print("Generating individual graph visualizations in HTML using pyvis...It might take a while.")

	number_of_nodes = len(net.nodes())
	print(f"Number of nodes: {number_of_nodes}")
	networks = glob(os.path.join(out_dir,"networks","*.html"))
	print(f"Number of existing networks: {len(networks)} \n Example network: {networks[0:3]}")
	processed = 0
	for node in net:
		processed +=1
		print(f"Processing node: {node}")
		#if "tmp/networks/"+str(node)+".html" not in networks:
		pyvis_visualization_local(node,net,distances,os.path.join(out_dir,"networks"))
		# else:
			#print(f"Skip graph for {node}")
		print(f"Processed {100*float(processed)/number_of_nodes}%")




### Image carousel visualization

def generate_image_carousel(faam_kb,github_repo_url,repo_name):
	# get GitHub credentials
	credentials = json2dict(os.path.join("credentials","github_credentials.json"))
	auth = Auth.Token(credentials["access_token"])
	g = Github(auth=auth)

	for item in faam_kb["items"]:
		if item["metadata"]["object_type"][0]["value"] == "manifestation":
			# get GitHub repository from resources
			GitHub_path = item["resources"]["GitHub"][0]["value"].replace("https://github.com/","")
			user_name = GitHub_path.split("/")[0]
			repo_name = GitHub_path.split("/")[1]
			path_name = GitHub_path.replace(f"{user_name}/{repo_name}/tree/main/","")
			faam_manifestation_id = item["metadata"]["FAAM manifestation ID"][0]["value"]
			#print(f"GitHub path: {GitHub_path}")
			# repo = g.get_repo(f"{user_name}/{repo_name}")
			repo = g.get_repo(f"{user_name}/{repo_name}")
			#contents = repo.get_contents(path_name)
			contents = repo.get_contents(f"images/{faam_manifestation_id}/images")

			raw_images = [] # generate raw images URL for carousel
			for image in contents:
				# version for original JPGs
				#raw_images.append(f"https://raw.githubusercontent.com/{user_name}/{repo_name}/main/{image.path}")

				#version for WEBP images
				raw_images.append(f"https://raw.githubusercontent.com/{user_name}/{repo_name}/main/data/images/{image.path}")

			#print(f"Raw URL for images: {raw_images}")

			# generate a HTML page with image carousel using Dominate

			# generate new page
			doc = dominate.document(title=faam_manifestation_id)


			# generate head
			with doc.head:
				meta(charset="utf-8")
				meta(name="viewport", content="width=device-width, initial-scale=1")
				link(
					href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css",
					rel="stylesheet",
				)
				link(href="https://getbootstrap.com/docs/5.2/assets/css/docs.css", rel="stylesheet")
				script(src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js")

			# generate style

			doc.add(style(raw(""".background-faam {
									background-color: #1e1d1d;
						}""")))

			# generate body

			with doc:
				with div(cls="background-faam"):
					img(src="https://raw.githubusercontent.com/nicholascornia89/faam/main/overrides/assets/images/faam-logo_full-gold.png", width="200" ,height="100")

					with div(id="carouselExampleIndicators", cls="carousel slide", data_interval="false"):
						with div(cls="carousel-indicators"):
							for i in range(len(raw_images)):
								if i == 0:
									button(
										type="button",
										cls="active",
										data_bs_target="#carouselExampleIndicators",
										data_bs_slide_to=f"{i}",
										aria_current="true",
										aria_label=f"Slide {i+1}",
									)
								else:
									button(
										type="button",
										cls="",
										data_bs_target="#carouselExampleIndicators",
										data_bs_slide_to=f"{i}",
										aria_current="false",
										aria_label=f"Slide {i+1}",
									)

						with div(cls="carousel-inner"):
							for i in range(len(raw_images)):
								if i == 0:
									with div(cls="carousel-item active"):
										img(src=raw_images[i], cls="d-block w-100", alt=f"Slide {i+1}")
								else:
									with div(cls="carousel-item"):
										img(src=raw_images[i], cls="d-block w-100", alt=f"Slide {i+1}")

						with button(
							cls="carousel-control-prev",
							type="button",
							data_bs_target="#carouselExampleIndicators",
							data_bs_slide="prev",
						):
							span(cls="carousel-control-prev-icon", aria_hidden="true")
							span("Previous", cls="visually-hidden")

						with button(
							cls="carousel-control-next",
							type="button",
							data_bs_target="#carouselExampleIndicators",
							data_bs_slide="next",
						):
							span(cls="carousel-control-next-icon", aria_hidden="true")
							span("Next", cls="visually-hidden")


			# save HTML page

			with open(os.path.join("tmp","image_carousels",f"{item["id"]}.html"), "w") as f:
				f.write(doc.render(pretty=True))
