# Trekking company knowledge graph

This project presents an RDF knowledge graph for a trekking company: its treks and the places they cross (linked to DBpedia), its guides, clients, departures, bookings and equipment rentals, described with an RDFS vocabulary, checked with SHACL shapes and queried with SPARQL.

**Authors:** Imane AMRAOUI, Salma IDMANSOUR

| File | Content |
|---|---|
| `cto_schema.ttl` | RDFS vocabulary (28 classes, 53 properties) |
| `cto_shapes.ttl` | SHACL shapes |
| `cto_data_catalog.ttl` | Catalogue: places and trails from DBpedia, treks, packages, equipment |
| `cto_data_operations.ttl` | Fictional operations data (guides, clients, bookings…) |
| `cto_query.txt` | 15 competency questions and their SPARQL queries |
| `generate_operations.py` | Generates `cto_data_operations.ttl` |
| `validate.py` | SHACL validation with pyshacl |
| `.github/workflows/validate.yml` | GitHub Actions workflow that runs `validate.py` |

The data is validated automatically: on every pull request and every push to `main`, the workflow runs `validate.py`, and fails if the data does not conform to the shapes.

The queries were tested in Corese; the full explanation is in the report.
