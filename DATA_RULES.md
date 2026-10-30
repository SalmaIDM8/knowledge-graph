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
| `cto:startDate`, `cto:endDate`, `cto:fromDate`, `cto:toDate`, `cto:bookingDate`, `cto:reviewDate`, `schema:birthDate` | `"2026-07-05"^^xsd:date` |
| `foaf:mbox` | `<mailto:marie@example.org>` (un lien, pas un texte) |
| `foaf:phone` | `<tel:+33612345678>` (un lien, pas un texte) |
| `owl:sameAs` | `dbr:Tour_du_Mont_Blanc` (uniquement DBpedia) |
| `cto:status` | `cto:Pending`, `cto:Confirmed` ou `cto:Cancelled` |

## 4. Réutiliser les IRI du catalogue (ne jamais les recréer)

Les données des opérations (`cto_data_operations.ttl`) **pointent vers** les ressources déclarées dans `cto_data_catalog.ttl`. On ne les redéclare pas.

| Pour… | On réutilise | ❌ À ne pas faire |
|---|---|---|
| `cto:speaks` | `d:french`, `d:english`, `d:italian`, `d:spanish`, `d:german`, `d:nepali`, `d:arabic` | `d:francais a cto:Language` |
| `cto:hasCertification` | `d:certIFMGA`, `d:certIML`, `d:certWFR`, `d:certHighAltitude` | `d:ifmga a cto:Certification` |
| `cto:hasMedicalCondition` | `d:heartCondition`, `d:asthma`, `d:kneeProblems`, `d:vertigo`, `d:altitudeSickness` | |
| `cto:knowsArea` | `d:alps`, `d:montBlancMassif`, `d:himalayas`, `d:andes`, `d:highAtlas`, `d:pyrenees`, `d:dolomites`… | |
| `cto:livesIn`, `cto:nationality` | villes (`d:chamonix`…) et pays (`d:france`…) du catalogue, ou une **nouvelle** ville si elle n'existe pas encore | redéclarer `d:france` |
| `cto:ofTrek` | `d:trekTMB`, `d:trekTMBExpress`, `d:trekMontBlanc`, `d:trekGR20`, `d:trekEBC`, `d:trekAnnapurna`, `d:trekIncaTrail`, `d:trekToubkal`, `d:trekTreCime`, `d:trekVignemale` | |
| `cto:withPackage` | `d:packTMBComfort`, `d:packEverestKathmandu`, `d:packMachuPicchu` | |
| `cto:rentedItem` | `d:tent2p`, `d:sleepingBag`, `d:sleepingMat`, `d:crampons`, `d:iceAxe`, `d:harness`, `d:helmet`, `d:trekkingPoles`, `d:downJacket`, `d:headlamp` | |

La liste complète est dans `cto_data_catalog.ttl`, rangée par sections.

**C'est vérifié automatiquement :**
- **faute de frappe** (`d:englsh`) → erreur, car la ressource n'existe pas (pas de label, pas de type) ;
- **doublon** (une 2ᵉ langue « French ») → erreur *« Duplicate of d:french … reuse the existing IRI »*.

## 5. Le fichier des opérations est généré

`cto_data_operations.ttl` est **produit par** `generate_operations.py` : ne pas le modifier à la main (les changements seraient perdus). Pour ajouter un guide, un départ ou une indisponibilité, modifier les listes en haut du script puis :

```bash
python generate_operations.py
python validate.py
```

## 6. Vérifier avant chaque commit

```bash
python validate.py
```

Le script valide **tous les fichiers `cto_data*.ttl` ensemble** (c'est indispensable pour vérifier les liens entre fichiers). Le résultat doit être `Conforms: True`. Sinon, le message indique la ressource fautive (`Focus Node`) et la règle non respectée (`Message`).

Cette même validation est lancée **automatiquement par GitHub sur chaque Pull Request** (onglet *Checks*) : ✅ = données valides, ❌ = cliquer sur *Details* pour voir l'erreur.
