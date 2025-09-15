# Code documentation

This documentation describes the different functions and scripts for the FAAM project.

## Objectives

- [x ] Import metadata from Nodegoat publication export or export CSV function into JSON file.
- [x ] Map FAAM fields to external vocabularies.
- [x ] Convert Nodegoat data to RDF ontology using RDFlib.
- [x ] Enrich metadata using Wikidata SPARQL endpoint.
- [ ] Create FAAM Ontology using RDFlib or Protegé.
- [x ] Assign permanent URI to ontology using w3id.org or purl.org.
- [ ] Export the knowledge base into [Wikibase.cloud](https://www.wikibase.cloud/).
- [ ] Tropy integration using [Canopy IIIF](https://canopy-iiif.github.io/docs/setup-a-collection-with-tropiiify) and Tropiiify plugin.
- [x ] Static site generation using Mkdocs.
- [x ] Image viewer carousel using https://raw.githubusercontent.com/nicholascornia89/{repoName}/main/{path}/{image_name}.jpg

## Mkdocs scripts

### TO-DO

- [x ] Import metadata from `nodegoat_export` and `object-list`
- [ ] Generate pages (.md) for each item in `faam_kb` and save it in `docs/kb/` 
- [x ] For each page add tag = object_type, title = id
- [x ] Use [Markdown generator library](https://github.com/TheRenegadeCoder/SnakeMD) to record information according to template.
- [x ] Record each page metadata in separate `id`.json file.

### Data Types

| name | description | markdown serialization |
|------|-------------|------------------------|
| id | identifier for FAAM | reference for page name |
| string | general text | paragraph |
| externalid | hyperlink with base url | [externalid](baseurl/id) |
| date | date | YYYY-MM-DD |
| image | image url | ![alt text](imageurl) |
| item | link to another page | [item](item.md) |
| html | HTML code | <div> code </div> |
| statement | table with multiple values | only for agent, including role, date and location |
| qualifier | column associated with statement table | only for agent, including role, date and location |

### Object types

| name | description |
| ---- | ---- |
| city | item used for the `place` property |
| country | item used for the `nationality` property |
| music_organization | item similar to agent, but tighted to a physical location |
| keyword | subjects linked to Wikidata |
| agent | persons and organizations acting on a manifestation |
| score_complexity | level of complexity of a manifestation |
| score_format | format of a manifestation |
| manifestation | a score, or collection of scores tied to a library record, with unique identifier |
| musical_instrument | music instrument or voice involved in a manifestation |

### Templates

Templates are organized by object type and provide a ordered list of appereance of statements and cross-references


Extra

- [ ] Integrate JavaScript to populate lists in pages programmatically, with seach filter.

Some ideas about layout and presentation of data

- [x ] Test [generic grids](https://squidfunk.github.io/mkdocs-material/reference/grids/#using-generic-grids) or [card grids](https://squidfunk.github.io/mkdocs-material/reference/grids/#using-generic-grids)
- [x ] Include graph representation of metadata using pyvis or similar library
- [ ] Geolocalization
- [x ] Simple image carousel tool like [Glide](https://glidejs.com/docs/) or [Swiper](https://swiperjs.com/get-started) (see [Demos](https://swiperjs.com/demos))
- [ ] Zoomable images using [pyvips](https://libvips.github.io/pyvips/) and render them using [OpenSeadragon](https://openseadragon.github.io/docs/)

## Tropy scripts

All scripts to programmatically interact with tropy are available in the `tropy.py` file. I successfully made some test already to export each table to CSV formats via Pandas.

You can more easily import metadata and hierarchy (lists,items,photos,selections) [directly from JSON-LD file](https://docs.tropy.org/using-tropy/add_files#importing-json-ld-files). This will make my life easier for batch import of metadata and selections for annotations recorded in PAGEXML or COCO.

### TO-DO

- [ ] Create a JSON-LD tropy import where image paths are URLs (test on a FAAM-manifestation)
- [ ] Have a look at [Canopy IIIF](https://github.com/canopy-iiif/canopy-iiif) and [Tropiiify](https://github.com/arkalab/tropiiify) documentations to set up multiple `IIIF base URLs` for the collection. 
- [ ] Assign programmatically UUIDs to each item in tropy using the UUID python library. This will become the manifest id later on.
- [ ] ...

## Nodegoat scripts

We have exported all data from Nodegoat using the CSV export function for each Object type, available in the `nodegoat_data` folder. The `nodegoat.py` script parses these CSV files into a unique JSON structure available in the `tmp` folder.
References between objects are constructed by the Nodegoat Object IDs, unique to each entry of the database.

### Note: Concerning Sub-Objects alignment

When working with sub-objects, like locations and dates associated with a given object, make sure to align the statements by changing the `elif` formulation on line 37 to the Object type you need to exclude from the other metadata. This option allows you to repeat values that otherwise would be omitted. The final result will produce lists of equal length for the object and its sub-objects. 

### TO-DO

- [x ] Batch import metadata from CSV exports and parse everything into JSON.
- [x ] Generate unique short UUIDs for each object
- [x ] Enhance metadata using python Wikibase API (SPARQL)

## FAAM Knowledge base scripts

### TO-DO

- [x ] Generate for each item a dedicated JSON, CSVs and RDF serializations for download and query.
- [x ] Map Nodegoat fields into RDF, using appropriate ontologies and vocabularies.
- [ ] Convert JSON metadata to Turtle (and XML) RDF.
- [ ] Consider the creation of custom ontology for specific properties. 

### Item data structure

__TO DO__

```json
```

## RDF serialization

### TO-DO

- [ ] Generate full LOD serialization from FAAM KB JSON dictionary
- [ ] Generate single serializations for each entity/item
- [ ] Describe specific FAAM properties to GitHub page URL http://nicholascornia89.github.io/faam/property/{property_name}
- [ ] FAAM entities to http://nicholascornia89.github.io/faam/entity/{id}

## JavaScript visualizations

### TO-DO

- [ ] GitHub API -> list of images form folder associated to FAAM manifestation ID
- [ ] Image carousel as separate HTML file for each manifestation. Then embedded via `<iframe>`
- [ ] Network graph visualization via pyvis also from external HTML file.
- [ ] Filter option for Cross-references using javascript code and FAAM UUID JSON file.