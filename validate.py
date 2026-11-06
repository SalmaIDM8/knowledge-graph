# Validates all cto_data*.ttl files against cto_shapes.ttl with pyshacl.

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
    allow_warnings=True,
)
print(report)
sys.exit(0 if conforms else 1)
