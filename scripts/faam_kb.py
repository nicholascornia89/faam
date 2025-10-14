"""
Generate the FAAM knowedge graph
"""
import sys

sys.path.append(".")
from utilities import *
from nodegoat import *
from wikidata import *

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
				for image in item["resources"]["image"]:
					image["base_url"] = wikimedia_common_base_url
					if wikimedia_common_base_url in image["value"]:
						# keep only filename
						image["value"] = image["value"].replace(wikimedia_common_base_url, "")
					else:
						image["value"] = image["value"].replace(" ", "_")
	return faam_kb


def external_ids_base_url(faam_kb, faam_kb_mapping):
	# externalid
	for item in faam_kb["items"]:
		for key in item["metadata"].keys():
			for statement in item["metadata"][key]:
				if statement["type"] == "externalid":
					# lookup base url for statement
					query = list(
						filter(lambda x: x["faam_property"] == key, faam_kb_mapping)
					)
					base_url = query[0]["base_url"]
					statement["base_url"] = base_url

		for key in item["statements"].keys():
			for statement in item["statements"][key]:
				if statement["type"] == "externalid":
					# lookup base url for statement
					query = list(
						filter(lambda x: x["faam_property"] == key, faam_kb_mapping)
					)
					base_url = query[0]["base_url"]
					statement["base_url"] = base_url

	return faam_kb

def generate_qid_list(faam_kb):
	# generate list ordered according to QID 
	qid_list = []
	item_list = []
	for item in faam_kb["items"]:
		if "qid" in item["metadata"].keys():
			for qid in item["metadata"]["qid"]:
				if qid["value"] != "":
					qid_list.append(int(qid["value"][1:]))
					item_list.append(
						{"id": item["id"], "qid": qid["value"], "qid_number": int(qid["value"][1:]), "label": item["metadata"]["label"][0]["value"] }
					)

	# order list
	qid_list = sorted(qid_list)
	item_list = sorted(item_list,key=lambda x: x["qid_number"])

	#print(f"Lists has been ordered by QID value (see first 10 values): \n {qid_list[0:9]} \n {item_list[0:9]} \n Press enter to continue...")
	#input()

	return qid_list,item_list

def generate_nodegoat_list(faam_kb):
	# generate list ordered according to nodegoat Object ID
	nodegoat_list = []
	item_list = []
	for item in faam_kb["items"]:
		if "nodegoat_id" in item["metadata"].keys():
			if item["metadata"]["nodegoat_id"][0]["value"] != "0":
				nodegoat_list.append(int(item["metadata"]["nodegoat_id"][0]["value"]))
				item_list.append(
					{"id": item["id"], "nodegoat_id": nodegoat_list[-1]}
				)

	# order list
	nodegoat_list = sorted(nodegoat_list)
	item_list = sorted(item_list,key=lambda x: x["nodegoat_id"])

	#print(f"Lists has been ordered by nodegoat Object ID value (see first 10 values): \n {nodegoat_list[0:9]} \n {item_list[0:9]} \n Press enter to continue...")
	#input()

	return nodegoat_list,item_list

def generate_uuid_list(faam_kb):

	# generate UUID list
	uuid_list = []
	item_list = []
	for item in faam_kb["items"]:
		# record the integer version of the UUID
		uuid_list.append(shortuuid.decode(item["id"]).int)
		item_list.append(
			{"id": item["id"],
			"uuid_int": uuid_list[-1], 
			"label": item["metadata"]["label"][0]["value"] }
		)

	# order list
	uuid_list = sorted(uuid_list)
	item_list = sorted(item_list,key=lambda x: x["uuid_int"])

	#print(f"Lists has been ordered by UUID value (see first 10 values): \n {uuid_list[0:9]} \n {item_list[0:9]}")

	return uuid_list,item_list

def fix_subobjects_statements(d,nodegoat_csv_path,nodegoat2faam_kb_filename):
	# homogenization and fixing order for Objects with Sub-Objects, like Agent with location and point in time

	# import mapping
	faam_kb_mapping = csv2dict(nodegoat2faam_kb_filename)

	# 1. Import a new data from nodegoat_csv path with function `nodegoat.import_csv_nodegoat`
	nodegoat_import = import_csv_nodegoat(nodegoat_csv_path)

	# import nodegoat_object list for fast bisect query
	nodegoat_object_list = nodegoat_objects_list(d)
	nodegoat_list = []
	for obj in nodegoat_object_list:
		nodegoat_list.append(obj["nodegoat_id"])


	# 2. Convert nodegoat IDs to FAAM UUIDs
	# set list of fields to be manipulated
	fix_fields = []
	for element in faam_kb_mapping:
		if element["data_type"] == "statement" or element["data_type"] == "qualifier":
			# exclude time
			if "Date Start" in element["nodegoat_field"]:
				fix_fields.append(element["nodegoat_field"])
			else: # add Object ID not needed?	
				fix_fields.append(element["nodegoat_field"]+" - Object ID")

	print(f"Fields to be fixed: {fix_fields}")

	for obj in nodegoat_import:
		# get object FAAM UUID
		index = bisect_left(nodegoat_list,int(obj['nodegoat_id'][0]))
		obj_uuid = nodegoat_object_list[index]["id"]
		object_type = nodegoat_object_list[index]["type"]

		#retrieve position of object within object_type list
		d_object = list(filter(lambda x: x[1]["id"] == obj_uuid, enumerate(d[object_type])))
		object_index = d_object[0][0]

		print(f"Previous version object: {d[object_type][object_index]}")

		# substitute all statements in
		for key in fix_fields:
			# main statements
			statements_list = []
			for statement in obj[key]:
				if statement != "":
					if "Date Start" in key:
						statements_list.append(statement)
					else:
						index = bisect_left(nodegoat_list,int(statement))
						uuid = nodegoat_object_list[index]["id"]
						statements_list.append(uuid)
				else:
					statements_list.append("")


			nodegoat_field = key.replace(" - Object ID","")
			# update dictionary d
			d[object_type][object_index][nodegoat_field] = statements_list


		#print(f"Updated version object: {d[object_type][object_index]}")
		#input()


	return d	

def add_label_to_statement(faam_kb):

	# generate UUID list

	uuid_list,item_list = generate_uuid_list(faam_kb)
	starting_time = time.time()

	# add labels to statements and qualifiers

	for item in faam_kb["items"]:
		#print(f"Current item: {item["id"]}")
		current_time = time.time()
		if current_time - starting_time > 10:
			print("Backing up new data until now...")
			faam_kb_filename = os.path.join(
				"tmp", "faam_kb", "faam_kb-" + get_current_date() + ".json"
			)

			dict2json(faam_kb, faam_kb_filename)
			starting_time = time.time()
		for category in ["metadata","statements"]:
			for key in item[category].keys():
					if len(item[category][key]) > 0:
						#print(f"Current property: {key} \n statements: {item[category][key]}")
						for statement in item[category][key]:
							if "label" not in statement.keys():
								if statement["value"] != "":
									if statement["type"] == "item":
										try:
											#convert uuid to integer
											uuid_int = shortuuid.decode(statement["value"]).int
											# perform bisect_left search
											index = bisect_left(uuid_list,uuid_int)
											try:
												if item_list[index]["id"] == statement["value"]:
													statement["label"] = item_list[index]["label"]
												else:
													print(f"UUID not found for {item["id"]}, statement {statement}. Getting label from Wikidata... ")
													entity = wb.item.get(statement["value"])
													statement["label"] = entity.labels.get('en').value
													statement["type"] = "externalid"
													statement["base_url"] = "http://www.wikidata.org/entity/"
													#print(f"New statement: {statement}")
													#input()
											except IndexError:
												print(f"UUID not found for {item["id"]}, statement {statement}. Getting label from Wikidata... ")
												entity = wb.item.get(statement["value"])
												statement["label"] = entity.labels.get('en').value
												statement["type"] = "externalid"
												statement["base_url"] = "http://www.wikidata.org/entity/"
												#print(f"New statement: {statement}")
												#input()
										except ValueError:
											print(f"Error for {item["id"]}, statement {statement}. Getting label from Wikidata...")
											entity = wb.item.get(statement["value"])
											statement["label"] = entity.labels.get('en').value
											statement["type"] = "externalid"
											statement["base_url"] = "http://www.wikidata.org/entity/"
											#print(f"New statement: {statement}")
											#input()

									elif statement["type"] == "externalid":
										if statement["value"] != "":
											if statement["value"][0] == "Q": # wikidata
												try:
													entity = wb.item.get(statement["value"])
													statement["label"] = entity.labels.get('en').value
												except Exception:
													pass
											else: # other external id, use value as label
												statement["label"] = statement["value"]


									elif statement["type"] == "statement":
										# adapt statement
										if statement["value"] != "":
											#convert uuid to integer
											uuid_int = shortuuid.decode(statement["value"]).int
											# perform bisect_left search
											index = bisect_left(uuid_list,uuid_int)
											if item_list[index]["id"] == statement["value"]:
												statement["label"] = item_list[index]["label"]
											else:
												print(f"UUID not found for {item["id"]}, statement {statement}. Getting label from Wikidata... ")
												entity = wb.item.get(statement["value"])
												statement["label"] = entity.labels.get('en').value
												statement["type"] = "externalid"
												statement["base_url"] = "http://www.wikidata.org/entity/"
												#print(f"New statement: {statement}")
												#input()
												pass

											# adapt qualifiers
											for qualifier in statement["qualifiers"]:
												if qualifier["value"] != "":
													#convert uuid to integer
													if qualifier["type"] == "item":
														try:
															uuid_int = shortuuid.decode(qualifier["value"]).int
															# perform bisect_left search
															index = bisect_left(uuid_list,uuid_int)
															if item_list[index]["id"] == qualifier["value"]:
																qualifier["label"] = item_list[index]["label"]
															else:
																print(f"UUID not found for {item["id"]}, statement {statement} ")
																entity = wb.item.get(qualifier["value"])
																qualifier["label"] = entity.labels.get('en').value
																qualifier["type"] = "externalid"
																qualifier["base_url"] = "http://www.wikidata.org/entity/"
																#input()
																pass
														except ValueError: # QID case
															print(f"UUID not found for {item["id"]}, qualifier {qualifier}. Getting label from Wikidata... ")
															entity = wb.item.get(qualifier["value"])
															qualifier["label"] = entity.labels.get('en').value
															qualifier["type"] = "externalid"
															qualifier["base_url"] = "http://www.wikidata.org/entity/"
															#print(f"New qualifier: {qualifier}")
															#input()


		for key in ["label","description","aliases"]: # retrieve Descriptions, Labels and Aliases if not present
			try:
				if item["metadata"][key][0]["value"] == "": # Wikidata query
					try:
						qid = item["metadata"]["qid"][0]["value"]
						if qid != "":
							entity = wb.item.get(qid)
							if key == "label":
								try:
									label = entity.labels.get('en').value
									#print(f"Label retrieved: {label}")
									item["metadata"]["label"] = [{"type": "string", "value": label}]
								except AttributeError: # None type
									pass
							elif key == "description":
								try:  
									description = entity.descriptions.get('en').value
									#print(f"Description retrieved: {description}")
									item["metadata"]["description"] = [{"type": "string", "value": description}]
								except AttributeError: # None value
									pass
							else: # aliases case
								aliases_query = entity.aliases.get('en')
								try:
									aliases = [alias.value for alias in aliases_query]
									#print(f"Aliases retrieved: {aliases}")
									item["metadata"]["aliases"] = []
									for alias in aliases:
										item["metadata"]["aliases"].append({
											"type": "string",
											"value": alias
											})

								except AttributeError: # None value
									pass

								except TypeError: # None value
									pass
					except IndexError: # no QID
						pass
			except IndexError: # empty metadata, it shoud be aliases
				if key != "aliases":
					print(f"Error for {item["metadata"]}")
				pass

			except KeyError:
				pass		


		#print(f"Getting metadata from Wikidata for {item["metadata"]} ")
		#input()




	return faam_kb	

def add_label_to_qid_metadata(faam_kb):

	starting_time = time.time()

	for item in faam_kb["items"]:
		current_time = time.time()
		if current_time - starting_time > 10:
			print("Backing up new data until now...")
			faam_kb_filename = os.path.join(
				"tmp", "faam_kb", "faam_kb-" + get_current_date() + ".json"
			)

			dict2json(faam_kb, faam_kb_filename)
			starting_time = time.time()
		try:
			qid = item["metadata"]["qid"][0]["value"]
			if qid != "":
				if "label" in item["metadata"]["qid"][0].keys():
					pass
				else:
					entity = wb.item.get(qid)
					label = entity.labels.get('en').value
					# append new label
					item["metadata"]["qid"][0]["label"] = label[0]
		except Exception:
			pass
	return faam_kb


def remove_empty_statements(faam_kb):
	for item in faam_kb["items"]:
		for category in item.keys():
			if category not in ["id","uuid_num"]:
				for prop in item[category].keys():
					if prop not in ["label","description","aliases","qid","image"]:
						for statement in item[category][prop]:
							if statement["value"] == "":
								item[category][prop].remove(statement)
					else:
						for statement in item[category][prop]:
							if statement["value"] == "":
								if len(item[category][prop]) > 1: # keep at least one empty statement
									item[category][prop].remove(statement)


	return faam_kb

def qids2faamuudis(faam_kb):
	
	# Ordered lists for bisect query filter
	qid_list,item_list = generate_qid_list(faam_kb)

	print(f"QID list length: {len(qid_list)}, {len(item_list)}")

	changed_qids = []

	# Check if items statements have QIDs instead of FAAM UUIDs.
	for item in faam_kb["items"]:
		for key in item["statements"].keys():
			for statement in item["statements"][key]:
				if statement["type"] == "item":
					# check if value is Wikidata QID
					if statement["value"] != "":
						if statement["value"][0] == "Q":
							try:
								qid_number = int(statement["value"][1:])
								index = bisect_left(qid_list, qid_number)
								qid = "Q" + str(qid_number)
								#print(f"Query {qid} with result {item_list[index]}")
								#input()
								if item_list[index]["qid"] == "Q" + str(qid_number):
									# replace QID with FAAM UUID
									statement["value"] = item_list[index]["id"]
									changed_qids.append(item_list[index]["qid"])
							except ValueError:
								#print(f"Error for {item["id"]}, statement {statement}")
								#input()
								pass
							except IndexError:
								print(f"Error for {item["id"]}, statement {statement}")
								print(f"Index: {index}")
								pass

							

	print(f"Changed QID statements {len(changed_qids)}: \n {changed_qids}")

	return faam_kb

def import_qids_from_openrefinecsv(faam_kb): # TO BE CONTINUED
	pass

def export_category_with_missing_qid_to_csv(faam_kb,category,out_dir):
	# filter according to category
	items = list(filter(lambda x: x["metadata"]["object_type"][0]["value"] == category, faam_kb["items"]))
	# export list of items with missing QID
	items_csv = []
	for item in items:
		if len(item["metadata"]["qid"]) == 0:
			items_csv.append({
				"id": item["id"],
				"label": item["metadata"]["label"][0]["value"]
				})
	dict2csv(items_csv,os.path.join(out_dir,f"{category}_missing_qid.csv"))


def add_country_to_cities(faam_kb,pid="P17"):
	# filter cities
	cities = list(filter(lambda x: x["metadata"]["object_type"][0]["value"] == "city", faam_kb["items"]))

	# generate QID list for fast retrieval
	qid_list,item_list = generate_qid_list(faam_kb)

	countries_not_in_faam = 0
	progress = 0
	number_of_countries = len(list(filter(lambda x: x["metadata"]["object_type"][0]["value"] == "country", faam_kb["items"])))
	number_of_cities = len(cities)
	print(f"Total number of cities: {number_of_cities} \n Totale number of countries: {number_of_countries}")

	starting_time = time.time()

	for city in cities:
		#print(f'Current city: {city["metadata"]["label"][0]["value"]} ')
		current_time = time.time()
		if current_time - starting_time > 10:
			print("Backing up new data until now...")
			faam_kb_filename = os.path.join(
				"tmp", "faam_kb", "faam_kb-" + get_current_date() + ".json"
			)

			dict2json(faam_kb, faam_kb_filename)
			starting_time = time.time()
		progress +=1
		# get qid
		country = {"type": "item", "value": ""}
		try:
			qid = city["metadata"]["qid"][0]["value"]
		except IndexError:
			print(f"Missing qid property for {city["id"]}")
		if qid != "":
			if "country" in city["statements"].keys():
				pass
			else:
				# retrieve QID and add country
				try:
					country_qid = wb_get_property_data(qid,pid)[-1]
					#print(f'Retrieved country: {country_qid}')
					if country_qid != "":
						# retrive country FAAM UUID, if not found keep Wikidata
						try:
							index = bisect_left(qid_list,int(country_qid[1:]))
							if item_list[index]["qid"] == country_qid:
								country["value"] = item_list[index]["id"]
								country["label"] = list(filter(lambda x: x["id"] == country["value"], faam_kb["items"]))[0]["metadata"]["label"][0]["value"]
								# add country statement
								city["statements"]["country"] = [country]
								print(f"Added country {country} to city {city["metadata"]["label"][0]["value"]}")
							else:
								countries_not_in_faam +=1
								entity = wb.item.get(country_qid)
								label = entity.labels.get("en").value
								city["statements"]["country"] = [{"type": "externalid", "value": country_qid, "base_url": "http://wwww.wikidata.org/entity/", "label": label }]
						except IndexError:
							countries_not_in_faam +=1
							entity = wb.item.get(country_qid)
							label = entity.labels.get("en").value
							city["statements"]["country"] = [{"type": "externalid", "value": country_qid, "base_url": "http://wwww.wikidata.org/entity/", "label": label }]
		
				except IndexError:
					print(f"No country for {qid}")
								
		print(f"Progress: {100*float(progress)/number_of_cities}%")

	print(f"Countries not in FAAM kb ratio: {100*float(countries_not_in_faam)/number_of_countries}%")

	return faam_kb


def cross_references(faam_kb,cross_reference_mapping): # adding cross-references according to object_type

	# filter faam kb according to category to ease search
	faam_categories = {}
	for category in cross_reference_mapping.keys():
		faam_categories[category] = list(filter(lambda x: x["metadata"]["object_type"][0]["value"] == category, faam_kb["items"]))
	number_of_items = len(faam_kb["items"])
	print(f"FAAM categories: {faam_categories.keys()} \n Number of items in each category: {[len(faam_categories[cat]) for cat in faam_categories.keys()]}")
	progress = 0
	for item in faam_kb["items"]:
		print(f"Current item: {item["id"]}")
		progress +=1
		cross_reference_types = cross_reference_mapping[item["metadata"]["object_type"][0]["value"]]
		cross_reference = {}
		for cross_ref in cross_reference_types:
			# retrieve items that have the current item as reference in a statement or metadata
			#print(f"Current cross-reference {cross_ref}")
			for prop in cross_ref["property"]:
				#print(f"Current property: {prop}")
				if "qualifier" in cross_ref.keys(): # qualifiers version
					# search match through filtered faam kb
					for cat_item in faam_categories[cross_ref["object_type"]]:
						for statement in cat_item[cross_ref["category"]][prop]:
							for qualifier in statement["qualifiers"]:
								if qualifier["property"] == cross_ref["qualifier"]:
									if qualifier["value"] == item["id"]:
										try:
											cross_reference[cross_ref["object_type"]].append({
												"id": cat_item["id"],
												"type": "item",
												"label": cat_item["metadata"]["label"][0]["value"],
												"description": cat_item["metadata"]["description"][0]["value"]
												})
											if cross_ref["object_type"] == "manifestation":
												cross_reference[cross_ref["object_type"]][-1]["thumb"] = {"base_url": cat_item["resources"]["thumb"][0]["base_url"], "value": cat_item["resources"]["thumb"][0]["value"] }
											if cross_ref["object_type"] == "agent":
												cross_reference[cross_ref["object_type"]][-1]["image"] = {"base_url": cat_item["resources"]["image"][0]["base_url"], "value": cat_item["resources"]["image"][0]["value"] }
										except Exception:
											cross_reference[cross_ref["object_type"]] = [{
												"id": cat_item["id"],
												"type": "item",
												"label": cat_item["metadata"]["label"][0]["value"],
												"description": cat_item["metadata"]["description"][0]["value"]
												}]
											if cross_ref["object_type"] == "manifestation":
												cross_reference[cross_ref["object_type"]][-1]["thumb"] = {"base_url": cat_item["resources"]["thumb"][0]["base_url"], "value": cat_item["resources"]["thumb"][0]["value"] }
											if cross_ref["object_type"] == "agent":
												cross_reference[cross_ref["object_type"]][-1]["image"] = {"base_url": cat_item["resources"]["image"][0]["base_url"], "value": cat_item["resources"]["image"][0]["value"] }
					
					
				else: # normal item version
					# search match through filtered faam kb
					for cat_item in faam_categories[cross_ref["object_type"]]:
						try:
							for statement in cat_item[cross_ref["category"]][prop]:
								if statement["value"] == item["id"]:
									try:
										cross_reference[cross_ref["object_type"]].append({
											"id": cat_item["id"],
											"type": "item",
											"label": cat_item["metadata"]["label"][0]["value"],
											"description": cat_item["metadata"]["description"][0]["value"]
											})
										if cross_ref["object_type"] == "manifestation":
											cross_reference[cross_ref["object_type"]][-1]["thumb"] = {"base_url": cat_item["resources"]["thumb"][0]["base_url"], "value": cat_item["resources"]["thumb"][0]["value"] }
										if cross_ref["object_type"] == "agent":
											cross_reference[cross_ref["object_type"]][-1]["image"] = {"base_url": cat_item["resources"]["image"][0]["base_url"], "value": cat_item["resources"]["image"][0]["value"] }
									except Exception:
										cross_reference[cross_ref["object_type"]] = [{
											"id": cat_item["id"],
											"type": "item",
											"label": cat_item["metadata"]["label"][0]["value"],
											"description": cat_item["metadata"]["description"][0]["value"]
											}]
										if cross_ref["object_type"] == "manifestation":
											cross_reference[cross_ref["object_type"]][-1]["thumb"] = {"base_url": cat_item["resources"]["thumb"][0]["base_url"], "value": cat_item["resources"]["thumb"][0]["value"] }
										if cross_ref["object_type"] == "agent":
											cross_reference[cross_ref["object_type"]][-1]["image"] = {"base_url": cat_item["resources"]["image"][0]["base_url"], "value": cat_item["resources"]["image"][0]["value"] }
						except KeyError:
							#print(f"Key not found for {cat_item["id"]}")
							pass
		#print(f"Generated cross-references: {cross_reference}")
		item["cross-references"] = cross_reference

		print(f"Progress: {100*float(progress)/number_of_items}%")
	return faam_kb

def retrieve_properties_from_wikidata(faam_kb,faam_kb_mapping): # TO BE TESTED

	wikidata_base_url = "http://www.wikidata.org/entity/"

	wikidata_mapping = list(filter(lambda x: wikidata_base_url in x["lod_url"],faam_kb_mapping ))

	wikidata_properties = [prop["faam_property"] for prop in wikidata_mapping]

	# get qid list and item list for matching new QIDs
	qid_list,item_list = generate_qid_list(faam_kb)

	starting_time = time.time()

	for item in faam_kb["items"]:
		# make recurrent backups
		current_time = time.time()
		if current_time - starting_time > 10:
			print("Backing up new data until now...")
			faam_kb_filename = os.path.join(
				"tmp", "faam_kb", "faam_kb-" + get_current_date() + ".json"
			)

			dict2json(faam_kb, faam_kb_filename)
			starting_time = time.time()
		if item["metadata"]["qid"][0]["value"] != "":
			qid = item["metadata"]["qid"][0]["value"]
			for key in item["statements"].keys():
				if len(item["statements"][key]) == 0:
					if key in wikidata_properties:
						# retrieve property from wikidata
						try:
							pid = list(filter(lambda x: x["faam_property"] == key,wikidata_mapping))[0]["lod_url"].split("/")[-1]
							data_type = list(filter(lambda x: x["faam_property"] == key,wikidata_mapping))[0]["data_type"]
							property_data = wb_get_property_data(qid,pid )
							if len(property_data) > 0:
								item["statements"][key] = []
								for statement in property_data:
									# convert QID to FAAM UUID if possible
									if data_type == "item":
										try:
											# bisect search converting QID to FAAM UUID
											index = bisect_left(qid_list,int(statement[1:]))
											if item_list[index]["qid"] == statement:
												value = item_list[index]["id"]
												label = item_list[index]["label"]
												item["statements"][key].append({
													"type": "item",
													"value": value,
													"label": label
												})
											else: # item not found, use Wikidata QID
												value = statement
												entity = wb.item.get(statement)
												label = entity.labels.get('en').value
												item["statements"][key].append({
													"type": "externalid",
													"value": value,
													"base_url": "http://www.wikidata.org/entity/",
													"label": label
												})
										except IndexError: # index error, use QID
											value = statement
											entity = wb.item.get(statement)
											label = entity.labels.get('en').value
											item["statements"][key].append({
												"type": "externalid",
												"value": value,
												"base_url": "http://www.wikidata.org/entity/",
												"label": label
											})
										except AttributeError: # return query with None Type.
											pass

									elif data_type in ["string","date"]:
										value = statement
										item["statements"][key].append({
											"type": "string",
											"value": value,
											"label": value
										})
									elif data_type == "externalid":
										base_url = list(filter(lambda x: x["faam_property"] == key,wikidata_mapping))[0]["base_url"]
										value = statement
										label = value
										item["statements"][key].append({
											"type": "externalid",
											"value": value,
											"base_url": base_url,
											"label": label
										})
									else:
										pass


							print(f"Added property {key} from Wikidata to {item["metadata"]["label"][0]["value"]}")
						except IndexError:
							print(f"Property {key} not found for {item["metadata"]["label"][0]["value"]}")
							pass

				else: 
					pass


	return faam_kb





# Generate FAAM Knowledge Base JSON from latest Nodegoat export
def generate_faam_kb(d,nodegoat2faam_kb_filename):
	count_no_label = 0
	# Import mapping
	faam_kb_mapping = csv2dict(nodegoat2faam_kb_filename)
	faam_kb = {"items": []}
	for object_type in d.keys():
		for obj in d[object_type]:
			item = {
				"id": obj["id"],
				"uuid_num": shortuuid.decode(obj["id"]).int,
				"metadata": {"label": [{"type": "string", "value": ""}], 
							 "description": [{"type": "string", "value": ""}],
							 "aliases": [], 
							 "qid": [{"type": "externalid", "value": "", "base_url": "http://wwww.wikidata.org/entity/"}]
							 }, # setting basic metadata to empty
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
				elif field_mapping["data_type"] == "statement":
					# append qualifiers
					qualifier_keys = field_mapping["qualifiers"].split(",")
					#print(f'Qualifiers keys: {qualifier_keys}')
					for i in range(len(obj[field])):
						try:
							qualifiers = []
							for qualifier_key in qualifier_keys:
								qualifier_field_mapping = list(
										filter(lambda x: x["nodegoat_field"] == qualifier_key, faam_kb_mapping))[0]
								qualifiers.append({
												"type": qualifier_field_mapping["data_type"].split("|")[1],
												"property": qualifier_field_mapping["faam_property"], 
												"value": obj[qualifier_key][i]
												})
						except IndexError:
							print(f"Not aligned qualifiers for id {obj["id"]}")
							input()
						# append statement with qualifiers to item in FAAM kb
						try:
							# check for duplicates
							check_statement = list(filter(lambda x: x["value"] == obj[field][i],item[field_mapping["category"]][field_mapping["faam_property"]]))
							if len(check_statement) == 0: # no duplicate, append
								item[field_mapping["category"]][field_mapping["faam_property"]].append(
									{"type": field_mapping["data_type"], "value": obj[field][i], "qualifiers": qualifiers})
							else:
								if qualifiers not in [quals["qualifiers"] for quals in check_statement]: # same statement, but different qualifiers
									item[field_mapping["category"]][field_mapping["faam_property"]].append(
									{"type": field_mapping["data_type"], "value": obj[field][i], "qualifiers": qualifiers})
								else:
									# avoid duplicate
									pass

								
						except KeyError:
							# key not yet created
							item[field_mapping["category"]][field_mapping["faam_property"]] = [{"type": field_mapping["data_type"], "value": obj[field][i], "qualifiers": qualifiers}]




								
				elif "qualifier" in field_mapping["data_type"] :
					# qualifiers are already appended to the corresponding statement
					pass

				else: # not nested data type statement
					# I am appending multiple nodegoat fields that maps to a unique faam property
					for statement in obj[field]:
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


			"""# assign label value from Wikidata Label if absent (causing some issues?)
			if item["metadata"]["label"][0]["value"] == "":
				try:
					item["metadata"]["label"][0] = {
						"type": "string",
						"value": obj["Wikidata Label"][0],
					}

				except KeyError:
					count_no_label += 1
			"""
			# append item to knowledge base
			faam_kb["items"].append(item)
			#print(faam_kb["items"][-1])
			#input()

	#print(f"Items without label: {count_no_label}")

	# extra scripts


	print(f"Improving MediaWiki image URLs...")
	faam_kb = images_base_url(faam_kb)

	print(f"Improving External ID URLs...")
	faam_kb = external_ids_base_url(faam_kb, faam_kb_mapping)


	print(f"Mapping QIDs to FAAM UUIDs...")
	faam_kb = qids2faamuudis(faam_kb)

	print(f"Remove empty statements...")
	faam_kb = remove_empty_statements(faam_kb)

	print(f"Adding labels to each statement and qualifier...")
	faam_kb = add_label_to_statement(faam_kb)

	return faam_kb
