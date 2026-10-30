"""Generate cto_data_operations.ttl (guides, clients, departures, bookings,
rentals, reviews, guide unavailabilities).

Usage:  python generate_operations.py      (then: python validate.py)

- Guides, departures and unavailabilities are written by hand below: they are
  the business core and contain the edge cases used by the queries.
- Clients, bookings, rentals and reviews are generated with a FIXED random
  seed, so the file is the same at every run.
- Trek durations, prices, required equipment and stocks are read from
  cto_data_catalog.ttl, so both files stay consistent.
- The generator respects the SHACL business rules (capacity, stock, booking
  before departure, review after the trip...): the output must conform.
"""
import random
from datetime import date, timedelta

from rdflib import Graph, Namespace

random.seed(2026)
TODAY = date(2026, 10, 30)          # reference date: past vs future departures

CTO = Namespace("http://ns.cto-trekking.org/schema#")
D = "http://ns.cto-trekking.org/data#"
local = lambda iri: "d:" + str(iri)[len(D):]

# --------------------------------------------------------------------------
# 1. Read the catalogue
# --------------------------------------------------------------------------
cat = Graph().parse("cto_data_catalog.ttl")
treks = {}
for t, dur, price, maxg in cat.query("""
        PREFIX cto: <http://ns.cto-trekking.org/schema#>
        SELECT ?t ?d ?p ?m WHERE { ?t cto:durationDays ?d ; cto:basePrice ?p ; cto:maxGroupSize ?m }"""):
    treks[local(t)] = {
        "days": int(dur), "price": float(price), "max": int(maxg),
        "equipment": [local(e) for e in cat.objects(t, CTO.requiresEquipment)],
        "avoid": [local(c) for c in cat.objects(t, CTO.notRecommendedFor)],
    }
stock = {local(e): int(q) for e, q in cat.subject_objects(CTO.stockQuantity)}
rental_price = {local(e): float(p) for e, p in cat.subject_objects(CTO.dailyRentalPrice)}
packages = {}                        # trek -> [(package, supplement)]
for p, t in cat.subject_objects(CTO.includesTrek):
    packages.setdefault(local(t), []).append((local(p), float(cat.value(p, CTO.basePrice))))

# --------------------------------------------------------------------------
# 2. Guides (hand-written)
# --------------------------------------------------------------------------
GUIDES = {
    "d:guidePaul":   dict(given="Paul", family="Martin", born="1980-04-12", town="d:chamonix", nat="d:france",
                          langs=["d:french", "d:english", "d:italian"], certs=["d:certIFMGA", "d:certIML", "d:certWFR"],
                          areas=["d:alps", "d:pyrenees"], mail="paul.martin@cto-trekking.org"),
    "d:guideSophie": dict(given="Sophie", family="Bernard", born="1988-09-03", town="d:annecy", nat="d:france",
                          langs=["d:french", "d:english"], certs=["d:certIML", "d:certWFR"],
                          areas=["d:alps", "d:corsicanMountains"], mail="sophie.bernard@cto-trekking.org"),
    "d:guideMarco":  dict(given="Marco", family="Rossi", born="1976-01-22", town="d:courmayeur", nat="d:italy",
                          langs=["d:italian", "d:english", "d:german"], certs=["d:certIFMGA", "d:certIML"],
                          areas=["d:alps"], mail="marco.rossi@cto-trekking.org"),
    "d:guideAnna":   dict(given="Anna", family="Keller", born="1985-06-30", town="d:zermatt", nat="d:switzerland",
                          langs=["d:german", "d:english", "d:french"], certs=["d:certIFMGA", "d:certIML", "d:certWFR"],
                          areas=["d:alps"], mail="anna.keller@cto-trekking.org"),
    "d:guidePemba":  dict(given="Pemba", family="Sherpa", born="1983-03-15", town="d:namcheBazaar", nat="d:nepal",
                          langs=["d:nepali", "d:english"], certs=["d:certWFR", "d:certHighAltitude", "d:certIML"],
                          areas=["d:himalayas"], mail="pemba.sherpa@cto-trekking.org"),
    "d:guideDawa":   dict(given="Dawa", family="Tamang", born="1991-11-08", town="d:kathmandu", nat="d:nepal",
                          langs=["d:nepali", "d:english"], certs=["d:certWFR", "d:certHighAltitude"],
                          areas=["d:himalayas"], mail="dawa.tamang@cto-trekking.org"),
    "d:guideLucia":  dict(given="Lucía", family="Quispe", born="1990-02-19", town="d:cusco", nat="d:peru",
                          langs=["d:spanish", "d:english"], certs=["d:certWFR", "d:certIML"],
                          areas=["d:andes"], mail="lucia.quispe@cto-trekking.org"),
    "d:guideYoussef": dict(given="Youssef", family="Amrani", born="1987-07-27", town="d:marrakesh", nat="d:morocco",
                          langs=["d:arabic", "d:french", "d:english"], certs=["d:certIML", "d:certWFR"],
                          areas=["d:atlas"], mail="youssef.amrani@cto-trekking.org"),
    # Edge case: a new guide, no e-mail, never assigned to a departure
    "d:guideThomas": dict(given="Thomas", family="Petit", born="1998-12-01", town="d:toulouse", nat="d:france",
                          langs=["d:french"], certs=["d:certIML"], areas=["d:pyrenees"], mail=None),
}

UNAVAILABILITIES = [
    ("d:unavPaul2026",   "d:guidePaul",  "2026-08-10", "2026-08-20", "summer holidays"),
    ("d:unavMarco2026",  "d:guideMarco", "2026-06-01", "2026-06-07", "rescue training"),
    ("d:unavPemba2026",  "d:guidePemba", "2026-12-01", "2027-01-31", "winter season off"),
    ("d:unavSophie2027", "d:guideSophie", "2027-05-01", "2027-05-20", "knee surgery recovery"),
]

# --------------------------------------------------------------------------
# 3. Departures (hand-written): id, trek, start, capacity, lead, other guides, fill rate
# --------------------------------------------------------------------------
DEPARTURES = [
    # past departures (2025 and summer 2026): reviews are possible
    ("d:dep2025TMB",        "d:trekTMB",        "2025-07-05", 12, "d:guidePaul",   ["d:guideSophie"], 0.8),
    ("d:dep2025MontBlanc",  "d:trekMontBlanc",  "2025-07-20",  2, "d:guideAnna",   [], 1.0),
    ("d:dep2025EBC",        "d:trekEBC",        "2025-10-05", 12, "d:guidePemba",  [], 0.7),
    ("d:dep2025Inca",       "d:trekIncaTrail",  "2025-05-10", 16, "d:guideLucia",  [], 0.6),
    ("d:dep2025Toubkal",    "d:trekToubkal",    "2025-09-13", 12, "d:guideYoussef", [], 0.5),
    ("d:dep2025GR20",       "d:trekGR20",       "2025-06-15", 10, "d:guideSophie", [], 0.7),
    ("d:dep2026TMBJuly",    "d:trekTMB",        "2026-07-04", 12, "d:guidePaul",   ["d:guideMarco"], 1.0),   # fully booked
    ("d:dep2026TMBExpress", "d:trekTMBExpress", "2026-08-22", 10, "d:guideSophie", [], 0.6),
    ("d:dep2026MontBlanc1", "d:trekMontBlanc",  "2026-07-25",  2, "d:guideAnna",   [], 1.0),
    ("d:dep2026MontBlanc2", "d:trekMontBlanc",  "2026-08-01",  2, "d:guideMarco",  [], 0.5),
    ("d:dep2026TreCime",    "d:trekTreCime",    "2026-07-18", 15, "d:guideMarco",  [], 0.6),   # one-day trek
    ("d:dep2026Annapurna",  "d:trekAnnapurna",  "2026-04-01", 12, "d:guideDawa",   [], 0.6),
    ("d:dep2026EBCSpring",  "d:trekEBC",        "2026-04-05", 12, "d:guidePemba",  [], 0.8),
    # Anna does not know the Pyrenees (Paul does but is on holidays) -> SHACL warning
    ("d:dep2026Vignemale",  "d:trekVignemale",  "2026-08-10",  6, "d:guideAnna",   [], 0.7),
    ("d:dep2026TMBSept",    "d:trekTMB",        "2026-09-05", 12, "d:guidePaul",   [], 0.5),
    # future departures: pending bookings, no review yet
    ("d:dep2026EBCAutumn",  "d:trekEBC",        "2026-11-01", 12, "d:guideDawa",   [], 0.5),
    ("d:dep2026Inca",       "d:trekIncaTrail",  "2026-11-14", 16, "d:guideLucia",  [], 0.4),
    ("d:dep2026Toubkal",    "d:trekToubkal",    "2026-12-05",  8, "d:guideYoussef", [], 0.3),
    ("d:dep2027Annapurna",  "d:trekAnnapurna",  "2027-03-20", 12, "d:guidePemba",  [], 0.2),
    ("d:dep2027TMB",        "d:trekTMB",        "2027-07-03", 12, "d:guidePaul",   ["d:guideSophie"], 0.3),
    ("d:dep2027GR20",       "d:trekGR20",       "2027-06-14", 10, "d:guideSophie", [], 0.0),   # no booking yet
]

# --------------------------------------------------------------------------
# 4. Clients (generated)
# --------------------------------------------------------------------------
TOWNS = {  # town -> (country, main language)
    "d:paris": ("d:france", "d:french"), "d:lyon": ("d:france", "d:french"), "d:nice": ("d:france", "d:french"),
    "d:marseille": ("d:france", "d:french"), "d:grenoble": ("d:france", "d:french"), "d:lille": ("d:france", "d:french"),
    "d:annecy": ("d:france", "d:french"), "d:london": ("d:unitedKingdom", "d:english"),
    "d:manchester": ("d:unitedKingdom", "d:english"), "d:madrid": ("d:spain", "d:spanish"),
    "d:barcelona": ("d:spain", "d:spanish"), "d:milan": ("d:italy", "d:italian"), "d:turin": ("d:italy", "d:italian"),
    "d:geneva": ("d:switzerland", "d:french"), "d:berlin": ("d:germany", "d:german"),
    "d:munich": ("d:germany", "d:german"), "d:brussels": ("d:belgium", "d:french"),
    "d:montreal": ("d:canada", "d:french"), "d:casablanca": ("d:morocco", "d:arabic"), "d:lima": ("d:peru", "d:spanish"),
}
GIVEN = ["Marie", "Lucas", "Emma", "Hugo", "Chloé", "Louis", "Léa", "Nathan", "Camille", "Jules", "Sarah", "Adam",
         "Olivia", "James", "Sofia", "Mateo", "Giulia", "Lukas", "Mia", "Omar", "Inès", "Noah", "Clara", "Leo",
         "Alice", "Ethan", "Laura", "Samuel", "Nora", "Elias"]
FAMILY = ["Dupont", "Moreau", "Laurent", "Garcia", "Smith", "Müller", "Bianchi", "Fernández", "Lefebvre", "Dubois",
          "Brown", "Schmidt", "Romano", "López", "Benali", "Girard", "Wilson", "Fischer", "Ricci", "Martín",
          "Roux", "Fontaine", "Taylor", "Weber", "Conti", "Ruiz", "Mercier", "Haddad", "Clark", "Vidal"]
INSURERS = ["d:insurerAlpineAssist", "d:insurerTrekSafe", "d:insurerWorldCover"]
CONDITIONS = ["d:asthma", "d:kneeProblems", "d:heartCondition", "d:vertigo", "d:altitudeSickness"]

clients = {}
for i, (given, family) in enumerate(zip(GIVEN, FAMILY), start=1):
    town = random.choice(list(TOWNS))
    country, lang = TOWNS[town]
    langs = [lang] + ([] if lang == "d:english" or random.random() < 0.4 else ["d:english"])
    c = dict(given=given, family=family, town=town, nat=country, langs=langs,
             born=date(random.randint(1955, 2004), random.randint(1, 12), random.randint(1, 28)).isoformat(),
             mail=f"{given.lower()}.{family.lower()}@example.org".translate(str.maketrans("éèëüíáóö", "eeeuiaoo")),
             phone=None, insurer=random.choice(INSURERS) if random.random() < 0.85 else None,
             conditions=random.sample(CONDITIONS, 1) if random.random() < 0.2 else [])
    if random.random() < 0.3:
        c["phone"] = "+33" + "".join(random.choice("0123456789") for _ in range(9))
    clients[f"d:client{i:02d}"] = c
# Edge cases
clients["d:client05"].update(mail=None, phone="+33612345678")    # phone only
clients["d:client12"].update(conditions=["d:asthma"])            # will book the Everest trek -> warning
NO_BOOKING = {"d:client29", "d:client30"}                         # clients who never booked
LOYAL = "d:client01"                                              # client with many trips

# --------------------------------------------------------------------------
# 5. Bookings, rentals, reviews (generated under the business rules)
# --------------------------------------------------------------------------
day = lambda s: date.fromisoformat(s)
dep_info = {}
for dep, trek, start, cap, lead, others, fill in DEPARTURES:
    s = day(start)
    dep_info[dep] = dict(trek=trek, start=s, end=s + timedelta(days=treks[trek]["days"] - 1),
                         cap=cap, lead=lead, guides=[lead] + others, fill=fill)

client_trips = {c: [] for c in clients}           # (start, end) of the client's active bookings
rentals_out = []                                  # (start, end, item, quantity) of active rentals
bookings, rentals, reviews = [], [], []

def overlaps(a, b):
    return a[0] <= b[1] and b[0] <= a[1]

def stock_ok(item, period, q):
    """Units out at each start date (the peak is always on a start date) <= stock."""
    out = [r for r in rentals_out if r[2] == item] + [(period[0], period[1], item, q)]
    for s, _, _, _ in out:
        if sum(qq for ss, ee, it, qq in out if ss <= s <= ee) > stock[item]:
            return False
    return True

def add_booking(dep, client, n, status, n_book):
    info, trek = dep_info[dep], treks[dep_info[dep]["trek"]]
    latest = min(info["start"] - timedelta(days=7), TODAY)
    bdate = latest - timedelta(days=random.randint(0, 150))
    pkg = None
    if info["trek"] in packages and random.random() < 0.35:
        pkg = random.choice(packages[info["trek"]])
    total = n * (trek["price"] + (pkg[1] if pkg else 0.0))
    paid = {"d:Confirmed": total, "d:Pending": round(total * 0.3, 2),
            "d:Cancelled": 0.0}[status]
    bid = f"d:booking{n_book:03d}"
    bookings.append(dict(id=bid, client=client, dep=dep, date=bdate, n=n, status=status, paid=paid,
                         pkg=pkg[0] if pkg else None))
    if status == "d:Cancelled":
        return bid
    client_trips[client].append((info["start"], info["end"]))
    # rentals: required equipment for some clients, plus optional poles / jacket
    period = (info["start"], info["end"])
    wanted = [e for e in trek["equipment"] if random.random() < 0.5]
    wanted += [e for e in ("d:trekkingPoles", "d:downJacket") if e not in wanted and random.random() < 0.15]
    for item in wanted:
        q = random.randint(1, n)
        if stock_ok(item, period, q):
            rentals_out.append((info["start"], info["end"], item, q))
            rentals.append(dict(id=f"d:rental{len(rentals) + 1:03d}", booking=bid, item=item, q=q))
    # reviews: only after the end of a confirmed trip, before TODAY
    if status == "d:Confirmed" and info["end"] < TODAY and random.random() < 0.6:
        rdate = min(info["end"] + timedelta(days=random.randint(1, 20)), TODAY)
        for g in info["guides"][: 1 + (random.random() < 0.3)]:
            reviews.append(dict(id=f"d:review{len(reviews) + 1:03d}", client=client, guide=g, date=rdate,
                                rating=random.choices([5, 4, 3, 2], weights=[45, 35, 15, 5])[0]))
    return bid

n_book = 0
bookable = [c for c in clients if c not in NO_BOOKING]
for dep, info in sorted(dep_info.items(), key=lambda kv: kv[1]["start"]):
    target, seats = round(info["cap"] * info["fill"]), 0
    # the loyal client goes on every TMB departure
    free = lambda c: not any(overlaps((info["start"], info["end"]), p) for p in client_trips[c])
    if info["trek"] == "d:trekTMB" and info["start"] < TODAY and free(LOYAL):
        n_book += 1; add_booking(dep, LOYAL, 1, "d:Confirmed", n_book); seats += 1
    if dep == "d:dep2026EBCSpring" and free("d:client12"):
        n_book += 1; add_booking(dep, "d:client12", 1, "d:Confirmed", n_book); seats += 1
    tries = 0
    while seats < target and tries < 200:
        tries += 1
        client = random.choice(bookable)
        period = (info["start"], info["end"])
        if any(overlaps(period, p) for p in client_trips[client]):
            continue                                   # a client cannot be on two trips at once
        n = min(random.choice([1, 1, 1, 2, 2, 3, 4]), target - seats)
        if info["start"] > TODAY:
            status = random.choice(["d:Confirmed", "d:Pending", "d:Pending"])
        else:
            status = "d:Confirmed"
        n_book += 1; add_booking(dep, client, n, status, n_book); seats += n
    # a few cancellations (they do not take seats)
    if info["fill"] > 0 and random.random() < 0.5:
        n_book += 1; add_booking(dep, random.choice(bookable), random.randint(1, 2), "d:Cancelled", n_book)

# --------------------------------------------------------------------------
# 6. Write Turtle
# --------------------------------------------------------------------------
lit = lambda s: '"' + s.replace('"', '\\"') + '"'
dt = lambda x: f'"{x}"^^xsd:date'
out = ["""###############################################################################
#  CTO - Operations data  (GENERATED by generate_operations.py - do not edit)
#
#  Guides, unavailabilities, insurers, clients, departures, bookings, rentals
#  and reviews. All catalogue resources (treks, places, languages,
#  certifications, equipment...) are reused from cto_data_catalog.ttl.
#  Reference date for past / future departures: """ + TODAY.isoformat() + """
###############################################################################

@prefix cto:    <http://ns.cto-trekking.org/schema#> .
@prefix d:      <http://ns.cto-trekking.org/data#> .
@prefix rdfs:   <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:    <http://www.w3.org/2001/XMLSchema#> .
@prefix foaf:   <http://xmlns.com/foaf/0.1/> .
@prefix schema: <http://schema.org/> .
"""]

def person(iri, cls, p, extra):
    lines = [f"{iri} a {cls} ;",
             f"    foaf:givenName {lit(p['given'])} ; foaf:familyName {lit(p['family'])} ;",
             f"    schema:birthDate {dt(p['born'])} ;"]
    if p.get("mail"):
        lines.append(f"    foaf:mbox <mailto:{p['mail']}> ;")
    if p.get("phone"):
        lines.append(f"    foaf:phone <tel:{p['phone']}> ;")
    lines.append(f"    cto:livesIn {p['town']} ; cto:nationality {p['nat']} ;")
    lines.append(f"    cto:speaks {' , '.join(p['langs'])} ;")
    lines += extra
    lines[-1] = lines[-1].rstrip(" ;") + " ."
    return "\n".join(lines) + "\n"

out.append("\n# ----------------------------------------------------------------- GUIDES\n")
for g, p in GUIDES.items():
    out.append(person(g, "cto:Guide", p, [f"    cto:hasCertification {' , '.join(p['certs'])} ;",
                                          f"    cto:knowsArea {' , '.join(p['areas'])} ;"]))

out.append("\n# --------------------------------------------------- GUIDE UNAVAILABILITIES\n")
for u, g, f, t, why in UNAVAILABILITIES:
    out.append(f"{u} a cto:Unavailability ; cto:unavailableGuide {g} ;\n"
               f"    cto:fromDate {dt(f)} ; cto:toDate {dt(t)} ; cto:reason {lit(why)} .\n")

out.append("\n# --------------------------------------------------------------- INSURERS\n")
for ins, label in zip(INSURERS, ["Alpine Assist", "TrekSafe Insurance", "WorldCover Travel"]):
    out.append(f'{ins} a cto:Insurer ; rdfs:label "{label}"@en .\n')

out.append("\n# ---------------------------------------------------------------- CLIENTS\n")
for c, p in clients.items():
    extra = []
    if p["insurer"]:
        extra.append(f"    cto:insuredBy {p['insurer']} ;")
    if p["conditions"]:
        extra.append(f"    cto:hasMedicalCondition {' , '.join(p['conditions'])} ;")
    out.append(person(c, "cto:Client", p, extra))

out.append("\n# ------------------------------------------------------------- DEPARTURES\n")
for dep, info in sorted(dep_info.items(), key=lambda kv: kv[1]["start"]):
    others = [g for g in info["guides"] if g != info["lead"]]
    out.append(f"{dep} a cto:Departure ; cto:ofTrek {info['trek']} ;\n"
               f"    cto:startDate {dt(info['start'])} ; cto:endDate {dt(info['end'])} ;\n"
               f"    cto:capacity {info['cap']} ; cto:leadGuide {info['lead']}"
               + (f" ;\n    cto:hasGuide {' , '.join(others)}" if others else "") + " .\n")

out.append("\n# --------------------------------------------------------------- BOOKINGS\n")
for b in bookings:
    out.append(f"{b['id']} a cto:Booking ; cto:bookedBy {b['client']} ; cto:forDeparture {b['dep']} ;\n"
               f"    cto:bookingDate {dt(b['date'])} ; cto:numberOfParticipants {b['n']} ;\n"
               f"    cto:status {b['status'].replace('d:', 'cto:')} ; cto:amountPaid {b['paid']:.2f}"
               + (f" ;\n    cto:withPackage {b['pkg']}" if b["pkg"] else "") + " .\n")

out.append("\n# ---------------------------------------------------------------- RENTALS\n")
for r in rentals:
    out.append(f"{r['id']} a cto:Rental ; cto:forBooking {r['booking']} ; "
               f"cto:rentedItem {r['item']} ; cto:quantity {r['q']} .\n")

out.append("\n# ---------------------------------------------------------------- REVIEWS\n")
for r in reviews:
    out.append(f"{r['id']} a cto:Review ; cto:author {r['client']} ; cto:aboutGuide {r['guide']} ;\n"
               f"    cto:rating {r['rating']} ; cto:reviewDate {dt(r['date'])} .\n")

with open("cto_data_operations.ttl", "w", encoding="utf-8") as f:
    f.write("".join(out))
print(f"cto_data_operations.ttl: {len(GUIDES)} guides, {len(clients)} clients, {len(dep_info)} departures, "
      f"{len(bookings)} bookings, {len(rentals)} rentals, {len(reviews)} reviews")
