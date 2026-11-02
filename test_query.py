"""Run one SPARQL query on the schema and all data files.

Usage:  python test_query.py
Paste the query to test in QUERY below (SELECT, ASK, CONSTRUCT or DESCRIBE).
Needs:  pip install rdflib
"""
import glob
import sys

from rdflib import Graph

QUERY = """
PREFIX cto: <http://ns.cto-trekking.org/schema#>

SELECT ?trek ?difficulty ?days WHERE {
    ?trek cto:difficulty ?difficulty ;
          cto:durationDays ?days .
    FILTER (?difficulty <= 3 && ?days < 5)
}
"""

sys.stdout.reconfigure(encoding="utf-8")   # accents in the Windows terminal

g = Graph()
for f in ["cto_schema.ttl"] + sorted(glob.glob("cto_data*.ttl")):
    g.parse(f, format="turtle")
print(f"{len(g)} triples loaded\n")

result = g.query(QUERY)

if result.type == "ASK":
    print(result.askAnswer)
else:
    rows = list(result)
    for row in rows:
        print(" | ".join("-" if x is None else x.n3(g.namespace_manager) for x in row))
    print(f"\n{len(rows)} result(s)")
