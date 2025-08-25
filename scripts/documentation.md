# Code documentation

This documentation describes the different functions and scripts for the FAAM project.

## Objectives

- [x ] Import metadata from Nodegoat publication export or export CSV function into JSON file.
- [ ] Map FAAM fields to external vocabularies.
- [ ] Convert Nodegoat data to RDF ontology using RDFlib.
- [x ] Enrich metadata using Wikidata SPARQL endpoint.
- [ ] Create FAAM Ontology using RDFlib or Protegé.
- [ ] Assign permanent URI to ontology using w3id.org or purl.org.
- [ ] Export the knowledge base into [Wikibase.cloud](https://www.wikibase.cloud/).
- [ ] Tropy integration using [Canopy IIIF](https://canopy-iiif.github.io/docs/setup-a-collection-with-tropiiify) and Tropiiify plugin.
- [ ] Static site generation using Mkdocs (or Starlight).
- [ ] Image viewer carousel using https://raw.githubusercontent.com/nicholascornia89/{repoName}/main/{path}/{image_name}.jpg

## Mkdocs scripts

### TO-DO

- [ ] Import metadata from `nodegoat_export` and `object-list`
- [ ] Generate pages (.md) for each item in `object-list` and save it in `docs/kb/` 
- [ ] For each page add tag = object_type, title = id
- [ ] Use [Markdown generator library](https://github.com/TheRenegadeCoder/SnakeMD) to record information according to template.
- [ ] Record each page metadata in separate `id`.json file.

Extra

- [ ] Integrate JavaScript to populate lists in pages programmatically, with seach filter.

Some ideas about layout and presentation of data

- [x ] Test [generic grids](https://squidfunk.github.io/mkdocs-material/reference/grids/#using-generic-grids) or [card grids](https://squidfunk.github.io/mkdocs-material/reference/grids/#using-generic-grids)
- [ ] Include graph representation of metadata using pyvis or similar library
- [ ] Geolocalization
- [ ] Simple image carousel tool like [Glide](https://glidejs.com/docs/) or [Swiper](https://swiperjs.com/get-started) (see [Demos](https://swiperjs.com/demos))
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

### TO-DO

- [x ] Batch import metadata from CSV exports and parse everything into JSON.
- [x ] Generate unique short UUIDs for each object
- [x ] Enhance metadata using python Wikibase API (SPARQL)

## RDF scripts

### TO-DO

- [ ] Map Nodegoat fields into RDF, using appropriate ontologies and vocabularies.
- [ ] Convert JSON metadata to Turtle (and XML) RDF.
- [ ] Consider the creation of custom ontology for specific properties. 