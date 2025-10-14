from rdflib import Graph, URIRef, BNode, Literal, Namespace

# Import functions from other scripts
import sys

sys.path.append(".")
from utilities import *

# Import standard namespaces
from rdflib.namespace import RDF, XSD, RDFS

# definition of FAAM external ID namespaces
WD = Namespace("http://www.wikidata.org/entity/")
GNames = Namespace("https://www.geonames.org/")
IMSLP = Namespace("https://imslp.org/wiki/")
RISM = Namespace("https://rism.online/")
VIAF = Namespace("https://viaf.org/viaf/")
CPDL = Namespace("https://www.cpdl.org/wiki/index.php/")  # Choral Wiki
SCHEMA = Namespace("http://schema.org/")
SKOS_ref = Namespace("http://www.w3.org/2009/08/skos-reference/skos.html#")
SKOS_core = Namespace("http://www.w3.org/2004/02/skos/core#")
DCELEM = Namespace("http://purl.org/dc/elements/1.1/")
DCTERMS = Namespace("http://purl.org/dc/terms/")
CIDOM_CRM = Namespace("http://cidoc-crm.org/cidoc-crm/7.1.3/")
FAAM_entity = Namespace("http://nicholascornia89.github.io/faam/entity/")
FAAM_property = Namespace("http://nicholascornia89.github.io/faam/property/")
FAAM_NAMESPACES = [
    WD,
    GNames,
    IMSLP,
    RISM,
    VIAF,
    CPDL,
    SCHEMA,
    SKOS_ref,
    SKOS_core,
    DCELEM,
    DCTERMS,
    CIDOM_CRM,
    FAAM_entity,
    FAAM_property,
]


"""generate Turtle RDF serialization of metadata according to Nodegoat2LOD mapping"""

def generate_rdf_kb(faam_kb,nodegoat2faam_kb,file_path):

    #initialize whole knowledge graph

    kb_g = Graph()
    number_of_items = len(faam_kb["items"])
    progress = 0
    for item in faam_kb["items"]:
        kb_g = kb_g + generate_rdf_item(item,nodegoat2faam_kb,file_path,save=False)
        progress +=1
        print(f"RDF generation progress: {100*float(progress)/number_of_items}% items processed",end="\r")


    # save whole graph to disk
    kb_g.serialize(format="turtle",destination=file_path)



def generate_rdf_item(item, nodegoat2faam_kb, file_path,save=True): 
    # initialization graph
    g = Graph()
    # Bind prefixes to Namespace
    for ns in FAAM_NAMESPACES:
        if ns == WD:
            g.bind("wd", WD)
        elif ns == GNames:
            g.bind("gn", GNames)
        elif ns == IMSLP:
            g.bind("imslp", IMSLP)
        elif ns == RISM:
            g.bind("rism", RISM)
        elif ns == VIAF:
            g.bind("viaf", VIAF)
        elif ns == CPDL:
            g.bind("cpdl", CPDL)
        elif ns == SCHEMA:
            g.bind("schema", SCHEMA)
        elif ns == SKOS_ref:
            g.bind("skosref", SKOS_ref)
        elif ns == SKOS_core:
            g.bind("skos", SKOS_core)
        elif ns == DCELEM:
            g.bind("dcelem", DCELEM)
        elif ns == DCTERMS:
            g.bind("dcterms", DCTERMS)
        elif ns == CIDOM_CRM:
            g.bind("crm", CIDOM_CRM)
        elif ns == FAAM_entity:
            g.bind("faamentity", FAAM_entity)
        elif ns == FAAM_property:
            g.bind("faamprop", FAAM_property)

    #print(f"Current item: {item}")
    # generating local graph from statements
    s = URIRef(f"{FAAM_entity}{item["id"]}")
    g.add((s,RDF.type,RDFS.Resource))
    for category in item.keys():
        if category in ["metadata", "statements"]:
            for prop in item[category]:
                #print(f"Current property: {prop}")
                # get faam property and corresponding LOD URI
                p = URIRef(list(
                    filter(lambda x: x["faam_property"] == prop, nodegoat2faam_kb)
                )[0]["lod_url"])
                #print(f"LOD URL: {p}")

                # create RDF statement according to statement type

                for statement in item[category][prop]:
                    if statement["value"] != "":
                        if statement["type"] in ["string", "id", "date","schema"]:
                            o = Literal(statement["value"], datatype=XSD["string"])
                               
                        elif statement["type"] == "html":
                            o = Literal(
                                statement["value"], datatype=RDF.HTML
                            )
                        elif statement["type"] == "url":
                            o = Literal(statement["value"], datatype=SCHEMA.url)
                        elif statement["type"] == "externalid":
                            # add object using correct namespace
                            o = URIRef(f"{statement["base_url"]}{statement["value"].replace(" ","_")}")
                        elif statement["type"] == "item":
                            # add object via FAAM_entity
                            o = URIRef(f"{FAAM_entity}{statement["value"]}")
                        elif statement["type"] == "statement":
                            # add statement to graph
                            o = URIRef(f"{FAAM_entity}{statement["value"]}")
                            uuid_statement = Literal(item["id"] + "-" + str(uuid.uuid4()), datatype=XSD["string"])
                            g.add((s,RDF.type,RDF.subject))
                            g.add((p,RDF.type,RDF.predicate))
                            g.add((o,RDF.type,RDF.object))
                            g.add((uuid_statement,RDF.type,RDF.Statement))
                            # reification
                            for qual in statement["qualifiers"]:
                                # use RDF object, subject, predicate and statement types
                                if qual["value"] != "":
                                    if qual["type"] == "item":
                                        q = URIRef(f"{FAAM_entity}{qual["value"]}")
                                    
                                    elif qual["type"] == "externalid":
                                        q= URIRef(f"{qual["base_url"]}{qual["value"].replace(" ","_")}")

                                    elif qual["type"] == "date":
                                        q = Literal(qual["value"], datatype=XSD["string"])

                                    elif qual["type"] == "string":
                                        q = Literal(qual["value"], datatype=XSD["string"])
                                    elif qual["type"] == "url":
                                        q = Literal(qualt["value"], datatype=SCHEMA.url)

                                    pq = list(filter(lambda x: x["faam_property"] == qual["property"], nodegoat2faam_kb))[0]["lod_url"]
                                    g.add((uuid_statement,URIRef(pq),q))

                        # adding original statement
                        g.add((s,p,o))


    # save graph in Turtle serialization
    if save:
        g.serialize(format="turtle",destination=file_path)

    return g




                        



### TO BE CONTINUED ###

"""
Date: Literal("1990-07-04", datatype=XSD["date"])
String: Literal("Mona Lisa", lang="en")

# define custom namespace
EX = Namespace("http://example.org/")

bob = EX["Bob"]
alice = EX["Alice"]

# definition of Wikidata namespace
WD = Namespace("http://www.wikidata.org/entity/")

mona_lisa = WD["Q12418"]

# XSD allows you to easily define datatypes such as XSD['date']
birth_data = Literal("1990-07-04", datatype=XSD["date"])
title = Literal("Mona Lisa", lang="en")
# get value from Literal
print(title.value)

# generate a new graph
g = Graph()

# some examples (subject,predicate,object)
g.add((bob, RDF.type, FOAF.Person))
g.add((bob, FOAF.knows, alice))

# Bind prefixes to Namespaces
g.bind("ex", EX)
g.bind("wd", WD)
g.bind("foaf", FOAF)

# Replace values
# g.set((bob, SDO["birthDate"], Literal("1990-01-01", datatype=XSD.date)))

# remove all tuples from given node
# g.remove((bob, None, None))

# print Graph Serialization in Turtle
# print(g.serialize(format="ttl"))
save_graph(g, "ttl", "test.ttl")
save_graph(g, "json-ld", "test.json")

"""
