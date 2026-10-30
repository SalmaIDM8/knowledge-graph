# Notes pour le rapport (brouillon)

Brouillon à compléter au fur et à mesure (issues #9 et #10). On note ici les **choix** et leur **pourquoi** pendant qu'on s'en souvient. Le rapport final fait 5 pages maximum.

---

## 1. Sujet et périmètre 

- L'énoncé mélange *trekking company* (titre) et *cycling tour operator* (le préfixe `cto_` des fichiers). On a choisi le **trekking** et gardé les noms de fichiers `cto_*` demandés.
- Entités couvertes : lieux, sentiers, treks (types de treks), étapes, séjours (*tour packages*), départs, clients, guides, réservations, matériel, locations, avis.
- 📝 Qui a fait quoi dans le binôme.

## 2. Vocabulaire RDFS (`cto_schema.ttl`)

Détails dans `VOCABULAIRE.md`. Points à mettre en avant :

- **Deux namespaces** : `cto:` pour le vocabulaire, `d:` pour les instances.
- **Réutilisation + vocabulaire propre** : `foaf:Person`, `foaf:givenName`, `schema:birthDate`, `geo:lat/long`, et 28 classes / 53 propriétés `cto:` à nous.
- **Trek ≠ Departure** : un trek est un produit du catalogue, un départ est une session datée (dates, places, guide). Les réservations portent sur un départ.
- **`owl:sameAs` vers DBpedia** seulement entre choses identiques : sentiers (`dbr:Tour_du_Mont_Blanc`) et lieux. Pas sur un trek, qui est notre produit commercial.
- **Un seul `rdfs:domain`** : plusieurs domaines = intersection, pas union → domaine `foaf:Person` pour `cto:speaks`, super-classe `cto:Offer` pour `cto:basePrice`.
- **Transitivité** : RDFS ne peut pas déclarer `cto:locatedIn` transitif → les requêtes utilisent le chemin `cto:locatedIn+`.
- **`rdf:List`** pour l'itinéraire, car l'ordre des étapes compte.
- **Sous-propriété** : `cto:leadGuide rdfs:subPropertyOf cto:hasGuide`.
- **Données calculées plutôt que stockées** : note d'un guide (moyenne des avis), guides éligibles pour un trek (requête) → toujours à jour.
- **Indisponibilités des guides** (ajout #5) : classe `cto:Unavailability` (relation n-aire : guide, du, au, motif) plutôt que deux propriétés sur le guide, car un guide peut avoir plusieurs périodes. Le sujet demande de coordonner l'équipe de guides.
- 📝 Non retenus faute de temps (→ limites) : niveau physique du client, avis sur les départs/treks, sous-classes de matériel plus fines.

## 3. Shapes SHACL (`cto_shapes.ttl`)

- **RDFS décrit, SHACL contraint** : `rdfs:range xsd:integer` n'empêche pas une difficulté de 12 ; `sh:minInclusive 1 ; sh:maxInclusive 5` l'empêche.
- **Trois niveaux de règles :**
  1. *simples* : `sh:minCount`/`sh:maxCount`, `sh:datatype`, `sh:class`, `sh:pattern` (mailto, IRI DBpedia), `sh:uniqueLang`, `sh:in` (statut d'une réservation), `sh:lessThanOrEquals` (date de début ≤ date de fin, égales pour un trek d'un jour) ;
  2. *logiques* : `sh:or` (un client a un e-mail **ou** un téléphone), `sh:not` (un guide n'est pas un client) ;
  3. *métier en SPARQL* (`sh:sparql`) : surréservation, guide sur deux départs qui se chevauchent, certifications exigées par le trek, stock de matériel le jour de chaque départ (le pic de location tombe toujours sur une date de début), réservation avant le départ, avis seulement après la fin d'un voyage avec le guide (`cto:reviewDate`), pas de cycle dans `cto:locatedIn`, une étape par jour.
- **SHACL plus strict que RDFS** : `cto:highestPoint` a pour range `cto:Place` (un col comme le Thorong La est accepté), mais une `cto:SummitAscent` doit viser un `cto:Summit`.
- **Chemins de propriétés** sur la liste RDF : `cto:itinerary/rdf:rest*/rdf:first` → chaque élément est une `cto:Stage`.
- **Violation vs Warning** : certaines règles bloquent (`sh:Violation`), d'autres préviennent seulement (`sh:Warning`) : guide qui ne connaît pas la région, client avec une condition médicale déconseillée.
- **Difficulté rencontrée** : pyshacl refuse les sous-requêtes (`SELECT` imbriqué) qui utilisent `$this` → réécrites avec `GROUP BY … HAVING`.
- **Méthode de test** : un petit jeu de données correct → `Conforms: True` ; puis 13 erreurs ajoutées volontairement → les 13 sont détectées (+ 1 warning).
- **Pièges pour les données** (voir `DATA_RULES.md`) : décimaux avec un point (`990.0`), noms de personnes sans langue, labels avec `@en`/`@fr`.
- 📝 Limite : SHACL valide mais ne corrige pas ; les règles SPARQL dépendent de l'outil (testé avec pyshacl, à vérifier avec Corese).

## 4. Données (`cto_data_*.ttl`)

- **Deux fichiers** : `cto_data_catalog.ttl` (ce que l'agence vend : lieux, sentiers, treks, séjours, matériel) et `cto_data_operations.ttl` (son activité : guides, clients, départs, réservations, locations, avis, indisponibilités). Les opérations **réutilisent** les IRI du catalogue (vérifié par SHACL : pas de doublon, pas de ressource inconnue).
- **Catalogue écrit à la main**, avec de vraies données : 10 treks réels (TMB, GR20, Everest, Chemin de l'Inca…), hiérarchie de massifs, ~60 lieux liés à DBpedia par `owl:sameAs`. Chaque IRI DBpedia a été **vérifiée automatiquement** (existence, redirections suivies) ; coordonnées et altitudes copiées de DBpedia.
- **Opérations générées par un script** (`generate_operations.py`, graine aléatoire fixe → toujours le même résultat) : le cœur métier (9 guides, 15 départs, indisponibilités, scénarios précis) est écrit à la main dans le script ; les 20 clients, 54 réservations, 28 locations et 15 avis sont générés **en respectant les règles métier** (capacité, stock, réservation avant le départ, avis après la fin du voyage, un client pas sur deux voyages en même temps). Les durées, prix et matériel requis sont **lus dans le catalogue** → cohérence garantie.
- **Cas limites voulus** : départ complet (12/12), départ sans réservation, clients sans réservation, guide sans départ et sans e-mail, client joignable seulement par téléphone, réservations annulées / en attente, trek d'un seul jour, lieux sans coordonnées (Paris, Cusco, Imlil), massif sans lien DBpedia, matériel épuisé (les 6 baudriers sortis en même temps en août 2026) et stock nul (lampes frontales), avertissements SHACL (guide qui ne connaît pas la région, client asthmatique sur le trek de l'Everest).
- **Taille** : 1 931 triplets au total ; `python validate.py` → `Conforms: True` (2 warnings attendus).
- **Limite du script** : le moindre changement dans ses listes modifie toutes les données aléatoires. Les données sont donc figées avant d'écrire les résultats dans le rapport.

## 5. Requêtes SPARQL (`cto_query.txt`)

15 questions de compétence regroupées par besoin (recherche de treks, clients, guides, matériel, analyses), plus 2 bonus.

| Requête | Fonctionnalités SPARQL |
|---|---|
| Q1 | `rdfs:subClassOf*`, `LANG`, `OPTIONAL`, `COALESCE`, `BIND`, `GROUP_CONCAT` |
| Q2 | `VALUES`, `YEAR`, `MONTH`, `FILTER NOT EXISTS`, `SUM`, `HAVING` |
| Q3 | `SERVICE` (DBpedia), `UNION`, chemin alternatif sur la `rdf:List`, `DISTINCT` |
| Q4 | `VALUES`, `cto:locatedIn*`, calcul avec `BIND`, `ORDER BY`, `LIMIT` |
| Q5 | parcours de `rdf:List` (`rdf:rest*`, `rdf:first`), `COUNT`, `GROUP_CONCAT` |
| Q6 | `OPTIONAL`, `CONCAT`, `COUNT`, `SUM` |
| Q7 | double `FILTER NOT EXISTS` (« pour tout »), `FILTER EXISTS`, `MINUS` |
| Q8 | sous-requêtes, `AVG`, `ROUND`, `GROUP_CONCAT` |
| Q9 | `FILTER NOT EXISTS`, chemin alternatif, `DISTINCT` |
| Q10 | sous-requêtes imbriquées, `MAX`, `IF`, `COALESCE` |
| Q11 | calcul dans `SUM`, `CONCAT`, `STR`, `GROUP_CONCAT` |
| Q12 | `ASK` |
| Q13 | sous-requête, `AVG`, `ROUND`, `cto:locatedIn*` |
| Q14 | « top 1 par groupe » : deux sous-requêtes et `MAX` |
| Q15 | `CONSTRUCT`, `OPTIONAL` imbriqués |
| B1 | `INSERT … WHERE`, `IRI`, `STRAFTER` |
| B2 | `DESCRIBE` |

- **Tests** : toutes les requêtes sont exécutées avec rdflib ; Q6, Q8 et Q13 sont recoupées par un calcul en Python ; Q12 et B1 sont aussi testées sur leurs cas négatifs (contre-indication, conflit de dates, départ complet), et les données restent conformes à SHACL après B1.
- **Difficultés avec rdflib** : `SERVICE SILENT` n'est pas exécuté et les valeurs locales ne sont pas transmises au `SERVICE` → liste des ressources dans un `VALUES` ; les variables d'une sous-requête ne sont pas isolées → variables renommées dans Q14.
- 📝 Limite : Q4 utilise une distance approximative (carré de la distance en degrés), car SPARQL n'a pas de fonctions trigonométriques.
- 📝 À vérifier avec Corese.

## 6. Recul : limites et améliorations 

- 📝 Simplifications assumées : le matériel est géré par modèle (stock), pas par objet individuel ; une location n'a pas de dates propres (elle prend celles du départ).
- 📝 Ce qu'on ferait avec OWL (transitivité, propriétés inverses, cardinalités inférées).

## 7. Utilisation de l'IA (section obligatoire)

Chaque membre complète sa partie honnêtement : **quel outil**, **pour quoi**, **ce qu'on a vérifié ou modifié soi-même**.
