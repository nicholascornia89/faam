"""
Scritpts to enhance missing fields using SPARQL query to Wikidata.

"""

import sys

sys.path.append(".")
from utilities import *
from nodegoat import *

# modules for interacting with Wikidata via SPARQL
from wikibase_api import Wikibase
from SPARQLWrapper import SPARQLWrapper, JSON

# Load Wikidata (as default)
wb = Wikibase()

# Import fields to Wikidata properties mapping

nodegoat2wd_filename = os.path.join("mapping", "nodegoat2wd_mapping.csv")
nodegoat2wd = csv2dict(nodegoat2wd_filename)

def wikidata_objects_list(
	d
):  # generates a list of all objects with a Wikidata QID
	wikidata_object_list = []
	for object_type in d.keys():
		if "Wikidata QID" in d[object_type][0]:
			for obj in d[object_type]:
				if obj["Wikidata QID"][0] != "":
					wikidata_object_list.append(
						{
							"id": obj["id"],
							"nodegoat_id": int(obj["nodegoat_id"][0]),
							"Wikidata QID": obj["Wikidata QID"][0],
							"Wikidata id": int(obj["Wikidata QID"][0][1:]),
							"type": object_type,
						}
					)
		else: # no wikidata element
			for obj in d[object_type]:
				wikidata_object_list.append(
						{
							"id": obj["id"],
							"nodegoat_id": int(obj["nodegoat_id"][0]),
							"Wikidata QID": "",
							"Wikidata id": 0,
							"type": object_type,
						}
					)

	return sorted(wikidata_object_list, key=lambda x: x["Wikidata id"])

def enhance_nodegoat_fields(d,out_dir):
	# generate wikidata object list and their ids for bisect search
	wikidata_object_list = wikidata_objects_list(d)
	wikidata_ids = []
	for obj in wikidata_object_list:
		wikidata_ids.append(obj["Wikidata id"])

	# list of new Wikidata IDs not previously present in the database.
	new_wikidata_items = []

	# Wikimedia redirect base url:
	wikimedia_base_url = "https://commons.wikimedia.org/wiki/Special:Redirect/file/"

	# get all objects according to type, assuming each object has a field called "Wikidata QID"
	countdown_start = time.time()
	for object_type in d.keys():
		print(f"Current object type: {object_type} (It might take a while...)")
		if "Wikidata QID" in d[object_type][0].keys():
			print(f"Enhancing {object_type} statements via SPARQL query...")
			# generate list of fields to be queried to Wikidata for the object type
			fields_to_be_queried = []
			for field in d[object_type][0].keys():
				query = list(filter(lambda x: x["nodegoat_field"] == field, nodegoat2wd))
				if len(query) > 0:
					fields_to_be_queried.append(query[0])
			for obj in d[object_type]:  # enhance every object
				countdown_check = time.time()
				if countdown_check - countdown_start > 20: # backup data until now
					#print("Backing up new data until now...")
					nodegoat_export2JSON(d, out_dir)
					countdown_start = time.time()

				#print(f"Current object: {obj["Wikidata QID"][0]}")
				if obj["Wikidata QID"][0] != "":  # check if Wikidata QID is present
					qid = obj["Wikidata QID"][0]
					#print(f"Current object {qid}:")
					for field in fields_to_be_queried:
						if obj[field["nodegoat_field"]][0] == "":  # if field is empty
							query = wb_get_property_data(
								qid, field["wd_property"]
							)  # query property data
							if len(query) >= 1:
								values_list = []
								for statement in query:
									# print(statement)
									# input()
									try:
										if statement != "": # skip empty statements
											if statement["mainsnak"]["datatype"] == "external-id":
												values_list.append(statement["mainsnak"]["datavalue"]["value"])
											#if "id" in statement["mainsnak"]["datavalue"]["value"].keys(): # item case
											elif statement["mainsnak"]["datatype"] == "wikibase-item":
												values_list.append(
												statement["mainsnak"]["datavalue"]["value"]["id"]
											)
											elif statement["mainsnak"]["datatype"] == "time":
												values_list.append(
														statement["mainsnak"]["datavalue"]["value"][
															"time"
														][1:11]
													)
											elif statement["mainsnak"]["datatype"] == "commonsMedia": # image case
												values_list.append(wikimedia_base_url + statement["mainsnak"]["datavalue"]["value"].replace(" ","_"))

											else:
												print(f"Unknown type for {statement} for {obj} ")
												input()
									except Exception:
										print (f"Error for {statement} for {obj} ")
										values_list.append("")
										#input()

									
								# update object fields with new list
								if len(values_list) >0:
									obj[field["nodegoat_field"]] = values_list
									print(f"Updating object {obj["Wikidata QID"][0]} values of {field} to {obj[field["nodegoat_field"]]}")
									''' check if the Wikidata QIDs are present in the Nodegoat database already
									for qid in obj[field["nodegoat_field"]]:
										try:
											if qid != "" and qid[0] == "Q":
												# bisect search
												index = bisect_left(wikidata_ids,int(qid[1:]))
												query = wikidata_object_list[index]
												if query == qid:
													pass 
												else:
													# if not present, add to new Wikidata items list
													new_wikidata_items.append(qid)
										except KeyError:
											print(f"Error for values list: {values_list} for {obj} ")
											input()
									'''

								
			#print(f"Current number of new Wikidata items = {len(new_wikidata_items)}")
			#print(new_wikidata_items)

	return d


# If QIDs are in fields, change them to corresponding FAAM UUID.
def qid2uuid_mapping(d):
	new_wikidata_qids = []
	new_wikidata_objects = []
	# import object_list
	object_list = load_latest_JSON(os.path.join("tmp","objects_list"))
	# generate wikdiata_ids list
	wikidata_ids_list = []
	for item in object_list:
		wikidata_ids_list.append(item["Wikidata id"])

	# check every object type
	for object_type in d.keys():
		#print(f"Current object type: {object_type}")
		fields_to_be_checked = []
		for item in nodegoat2wd:
			if item["nodegoat_field"] in d[object_type][0].keys():
				fields_to_be_checked.append(item["nodegoat_field"])
		#print(f"Fields to be checked: {fields_to_be_checked}")
		if len(fields_to_be_checked) >0:
			# check every object
			for obj in d[object_type]:
				for field in fields_to_be_checked:
					for i in range(len(obj[field])):
						statement = obj[field][i]
						# check if the reference is a QID
						try:
							if statement != "" and statement[0] == "Q":
								# search UUID corresponding to QID
								index = bisect_left(wikidata_ids_list,int(statement[1:]))
								qid = object_list[index]["Wikidata QID"]
								#print(f"Retrieved QID:{qid}")
								if qid == statement:
									# if QID is present, replace it with UUID
									obj[field][i] = object_list[index]["id"]
									#print(f"Replacing QID {qid} with UUID {statement} in object {obj['id']} for field {field}")
								else: # qid not present in FAAM knowledge base
									#print(f"QID {statement} not present in FAAM knowledge base for object {obj['id']} for field {field}")
									if statement not in new_wikidata_qids:
										new_wikidata_qids.append(statement)
										field_info = list(filter(lambda x: x["nodegoat_field"] == field,nodegoat2wd))
										statement_type = field_info[0]["object_type"]
										new_wikidata_objects.append({"id": "", "nodegoat_id": 0, "Wikidata QID": statement, "Wikidata id": int(statement[1:]), "type": statement_type })
						except Exception:
							#print(f'Error for {statement}')
							pass

	print(f"Export missing QIDs...")
	dict2csv(
		new_wikidata_qids,
		os.path.join(
			"tmp",
			"new_wikidata_ids",
			"new_wikidata_ids-" + get_current_date() + ".csv",
		),
	)
	dict2json(
		new_wikidata_objects,
		os.path.join(
			"tmp",
			"new_wikidata_objects",
			"new_wikidata_objects-" + get_current_date() + ".json",
		),
	)

	return d
								

def import_new_objects_from_wd(d,objects_list,out_dir):
	objects_wikidata_ids = []
	for item in objects_list:
		objects_wikidata_ids.append(item["Wikidata id"])

	# import new_wikidata_objects file
	new_wikidata_objects = load_latest_JSON(os.path.join(out_dir,"new_wikidata_objects"))

	for item in new_wikidata_objects:
		# check if object is already present
		index = bisect_left(objects_wikidata_ids,item["Wikidata id"])
		if objects_list[index]["Wikidata QID"] != item["Wikidata QID"]:
			# add new object to objects_list
			uuid = generate_short_uuid4(length=8)
			objects_list.append({
								    "id": uuid,
								    "nodegoat_id": 0,
								    "Wikidata QID": item["Wikidata QID"],
								    "Wikidata id": item["Wikidata id"],
								    "type": item["type"]
								  },)
			# add new item to dictionary NOT WORKING
			for field in d[item["type"]][0].keys():
				# reset all fields
				d[item["type"]][-1][field] = [""]

			# update id and QID of new object
			d[item["type"]][-1]["id"] = uuid
			d[item["type"]][-1]["nodegoat_id"] = ["0"]
			d[item["type"]][-1]["Wikidata QID"] = [item["Wikidata QID"]]
			print(f"New object {d[item["type"]][-1]} imported.")


	# Sort according to wikidata id

	return d,sorted(objects_list, key=lambda x: x["Wikidata id"])


# This script redirects the Wikidata image URL to the corresponing Wikimedia raw image.
def change_wikimedia_image_url(d,base_url,old_base_url):
	print("Changing Wikimedia image URLs...")
	for object_type in d:
		if "image" in d[object_type][0].keys():
			for obj in d[object_type]:
				for img in obj["image"]:
					if old_base_url in img and base_url not in img:
						# get image filename
						filename = img.split(old_base_url)[1]
						# change space to underscore
						filename = filename.replace(" ", "_")
						# update image URL
						print(f"Updated image URL for {obj['id']} to {base_url + filename}")
						img = base_url + filename

	return d

def query_externalid(extid,pid):
	#Returns QID associated with External ID with property PID
	sparql = SPARQLWrapper("https://query.wikidata.org/sparql",agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11")
	#sparql.setCredentials("Nicholas.cornia","Nby%cmt8")
	sparql.setQuery(
	"""SELECT ?item ?itemLabel ?extid
		WHERE {
		?item wdt:"""+pid+""" ?extid .
		VALUES ?extid { \""""+extid+"""\" }
		
		SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
		}
	""")
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	try:
		qid = results["results"]["bindings"][0]["item"]["value"][31:]
		label = results["results"]["bindings"][0]["itemLabel"]["value"]
	except Exception:
		qid = ""
		label = ""
	return qid,label

# Get Wikidata qid and label from External ID field
def external2wikidataqid(d,out_dir,mapping_filename):
	# import mapping of external IDs
	mapping = csv2dict(mapping_filename)
	countdown_start = time.time()
	# get all objects according to type, assuming each object has a field called "GeoNames ID"
	for object_type in d.keys():
		if "Wikidata QID" in d[object_type][0].keys():
			# mapping fields
			mapping_fields = []
			for field in mapping:
				if field["nodegoat_field"] in d[object_type][0].keys():
					mapping_fields.append(field)
			# enhance objects with Wikidata QID from external identifiers
			if len(mapping_fields) > 0:
				for obj in d[object_type]:
					countdown_check = time.time()
					if countdown_check - countdown_start > 20: # backup data until now
						print("Backing up new data until now...")
						nodegoat_export2JSON(d, out_dir)
						countdown_start = time.time()
					if obj["Wikidata QID"][0] == "":  # empty QID
						for field in mapping_fields:
							if obj[field["nodegoat_field"]][0] != "":
								# Adjust external ID in case of IMSLP string
								extid = obj[field['nodegoat_field']][0].replace(" ","_")
								extid = extid.replace("'","\'")
								pid = field['pid']
								#print(f"Querying Wikidata for {extid} with property {pid}")
								qid, label = query_externalid(extid,pid)
							if qid != "":
								obj["Wikidata QID"] = [qid]
								obj["Wikidata Label"] = [label]
								print(f"Updated object {obj['id']} with Wikidata QID {qid} and label {label}")

				

	return d

def test_wb_query():
	# Example: Adolf Ruthardt data
	qid = "Q4401191"
	return wb.entity.get(qid)["entities"][qid]["labels"]

def wb_get_property_data(qid, pid):
	# get entity profile given property
	try:
		entity = wb.entity.get(qid)["entities"][qid]
		properties_list = entity["claims"].keys()
		# look for property
		if pid in properties_list:
			return entity["claims"][pid]
		else:
			return [""]
	# no qid case
	except Exception:
		return [""]
