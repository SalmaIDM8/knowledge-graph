# Règles d'écriture des données (à lire avant d'écrire `cto_data_*.ttl`)

Les règles SHACL (`cto_shapes.ttl`) vérifient le **type exact** des valeurs.
Ces pièges font échouer la validation :

## 1. Nombres : entier ou décimal ?

| Propriété | Type | ✅ Correct | ❌ Refusé |
|---|---|---|---|
| `cto:basePrice`, `cto:amountPaid`, `cto:dailyRentalPrice` | décimal | `990.0` | `990` |
| `cto:altitude`, `cto:lengthKm` | décimal | `4806.0` | `4806` |
| `geo:lat`, `geo:long` | décimal | `45.9237` | `45` |
| `cto:difficulty`, `cto:rating` (1 à 5) | entier | `3` | `3.0` |
| `cto:durationDays`, `cto:capacity`, `cto:maxGroupSize`, `cto:quantity`, `cto:stockQuantity`, `cto:numberOfParticipants`, `cto:dayNumber` | entier | `12` | `12.0` |

👉 **Argent, altitude, distance, coordonnées → avec un point.**
👉 **On compte quelque chose → sans point.**

## 2. Textes : avec ou sans langue ?

| Propriété | ✅ Correct | ❌ Refusé |
|---|---|---|
| `rdfs:label` (lieux, treks, sentiers, matériel, langues, certifications…) | `"Mont Blanc"@en` , `"Alpes"@fr` | `"Mont Blanc"` |
| `foaf:givenName`, `foaf:familyName` | `"Paul"` | `"Paul"@fr` |

👉 **Un nom de personne ne se traduit pas → sans langue.**
👉 **Un nom de chose peut se traduire → avec `@en` / `@fr`** (une seule étiquette par langue).

## 3. Dates, emails, liens

| Propriété | ✅ Correct |
|---|---|
| `cto:startDate`, `cto:endDate`, `cto:bookingDate`, `schema:birthDate` | `"2026-07-05"^^xsd:date` |
| `foaf:mbox` | `<mailto:marie@example.org>` (un lien, pas un texte) |
| `owl:sameAs` | `dbr:Tour_du_Mont_Blanc` (uniquement DBpedia) |
| `cto:status` | `cto:Pending`, `cto:Confirmed` ou `cto:Cancelled` |

## 4. Vérifier avant chaque commit

```bash
pyshacl -s cto_shapes.ttl -e cto_schema.ttl -i rdfs cto_data_xxx.ttl
```

Le résultat doit être `Conforms: True`. Sinon, le message indique la ressource fautive (`Focus Node`) et la règle non respectée (`Message`).
