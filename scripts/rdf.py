from rdflib import Graph, URIRef, BNode, Literal, Namespace

# Import functions from other scripts
import sys

sys.path.append(".")
from utilities import *

# Import standard namespaces
from rdflib.namespace import RDF, XSD

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
FAAM = Namespace("http://nicholascornia89.github.io/faam/entity")
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
    FAAM,
]


"""generate Turtle RDF serialization of metadata according to Nodegoat2LOD mapping"""


def generate_rdf_item(item, nodegoat2faam_kb, file_path):  # TO BE CONTINUED
    # initialization graph

    for category in item.keys():
        for prop in item[category]:
            pass

    # I need to add each statement in the faam_kb item to the RDF Graph
    # make sure to correctly state subject, predicate and object and their datatype

    # Considere reification for qualifiers!

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
