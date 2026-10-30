"""Validate ALL data files (cto_data*.ttl) together against cto_shapes.ttl.

Usage:  python validate.py
Needs:  pip install pyshacl

The files are validated together so that links between them are checked:
an IRI used in the operations data (d:french, d:trekTMB...) must be declared
in the catalogue, and nothing may be declared twice.
Exit code 0 = conforms (warnings allowed), 1 = violations.
"""
import glob
import sys

from pyshacl import validate
from rdflib import Graph

files = sorted(glob.glob("cto_data*.ttl"))
if not files:
    print("No cto_data*.ttl file yet: nothing to validate.")
    sys.exit(0)

data = Graph()
for f in files:
    data.parse(f, format="turtle")
    print(f"loaded {f}")
print(f"{len(data)} triples in total\n")

conforms, _, report = validate(
    data,
    shacl_graph="cto_shapes.ttl",
    ont_graph="cto_schema.ttl",
    inference="rdfs",
    allow_warnings=True,   # sh:Warning results do not make the data invalid
)
print(report)
sys.exit(0 if conforms else 1)
