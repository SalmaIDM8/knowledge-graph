# Notes pour le rapport (brouillon)

Brouillon à compléter au fur et à mesure (issues #9 et #10). On note ici les **choix** et leur **pourquoi** pendant qu'on s'en souvient. Le rapport final fait 5 pages maximum.

Légende : ✅ fait · 📝 à compléter · ⏳ pas encore commencé

---

## 1. Sujet et périmètre ✅

- L'énoncé mélange *trekking company* (titre) et *cycling tour operator* (le préfixe `cto_` des fichiers). On a choisi le **trekking** et gardé les noms de fichiers `cto_*` demandés.
- Entités couvertes : lieux, sentiers, treks (types de treks), étapes, séjours (*tour packages*), départs, clients, guides, réservations, matériel, locations, avis.
- 📝 Qui a fait quoi dans le binôme.

## 2. Vocabulaire RDFS (`cto_schema.ttl`) — partie Salma ✅

Détails dans `VOCABULAIRE.md`. Points à mettre en avant :

- **Deux namespaces** : `cto:` pour le vocabulaire, `d:` pour les instances.
- **Réutilisation + vocabulaire propre** : `foaf:Person`, `foaf:givenName`, `schema:birthDate`, `geo:lat/long`, et 27 classes / 49 propriétés `cto:` à nous.
- **Trek ≠ Departure** : un trek est un produit du catalogue, un départ est une session datée (dates, places, guide). Les réservations portent sur un départ.
- **`owl:sameAs` vers DBpedia** seulement entre choses identiques : sentiers (`dbr:Tour_du_Mont_Blanc`) et lieux. Pas sur un trek, qui est notre produit commercial.
- **Un seul `rdfs:domain`** : plusieurs domaines = intersection, pas union → domaine `foaf:Person` pour `cto:speaks`, super-classe `cto:Offer` pour `cto:basePrice`.
- **Transitivité** : RDFS ne peut pas déclarer `cto:locatedIn` transitif → les requêtes utilisent le chemin `cto:locatedIn+`.
- **`rdf:List`** pour l'itinéraire, car l'ordre des étapes compte.
- **Sous-propriété** : `cto:leadGuide rdfs:subPropertyOf cto:hasGuide`.
- **Données calculées plutôt que stockées** : note d'un guide (moyenne des avis), guides éligibles pour un trek (requête) → toujours à jour.
- **Indisponibilités des guides** (ajout #5) : classe `cto:Unavailability` (relation n-aire : guide, du, au, motif) plutôt que deux propriétés sur le guide, car un guide peut avoir plusieurs périodes. Le sujet demande de coordonner l'équipe de guides.
- 📝 Non retenus faute de temps (→ limites) : niveau physique du client, avis sur les départs/treks, sous-classes de matériel plus fines.

## 3. Shapes SHACL (`cto_shapes.ttl`) — partie Imane ✅

- **RDFS décrit, SHACL contraint** : `rdfs:range xsd:integer` n'empêche pas une difficulté de 12 ; `sh:minInclusive 1 ; sh:maxInclusive 5` l'empêche.
- **Trois niveaux de règles :**
  1. *simples* : `sh:minCount`/`sh:maxCount`, `sh:datatype`, `sh:class`, `sh:pattern` (mailto, IRI DBpedia), `sh:uniqueLang`, `sh:in` (statut d'une réservation), `sh:lessThanOrEquals` (date de début ≤ date de fin, égales pour un trek d'un jour) ;
  2. *logiques* : `sh:or` (un client a un e-mail **ou** un téléphone), `sh:not` (un guide n'est pas un client) ;
  3. *métier en SPARQL* (`sh:sparql`) : surréservation, guide sur deux départs qui se chevauchent, certifications exigées par le trek, stock de matériel le jour de chaque départ (le pic de location tombe toujours sur une date de début), réservation avant le départ, avis seulement après la fin d'un voyage avec le guide (`cto:reviewDate`), pas de cycle dans `cto:locatedIn`, une étape par jour.
- **Chemins de propriétés** sur la liste RDF : `cto:itinerary/rdf:rest*/rdf:first` → chaque élément est une `cto:Stage`.
- **Violation vs Warning** : certaines règles bloquent (`sh:Violation`), d'autres préviennent seulement (`sh:Warning`) : guide qui ne connaît pas la région, client avec une condition médicale déconseillée.
- **Difficulté rencontrée** : pyshacl refuse les sous-requêtes (`SELECT` imbriqué) qui utilisent `$this` → réécrites avec `GROUP BY … HAVING`.
- **Méthode de test** : un petit jeu de données correct → `Conforms: True` ; puis 13 erreurs ajoutées volontairement → les 13 sont détectées (+ 1 warning).
- **Pièges pour les données** (voir `DATA_RULES.md`) : décimaux avec un point (`990.0`), noms de personnes sans langue, labels avec `@en`/`@fr`.
- 📝 Limite : SHACL valide mais ne corrige pas ; les règles SPARQL dépendent de l'outil (testé avec pyshacl, à vérifier avec Corese).

## 4. Données (`cto_data_*.ttl`) ✅

- **Deux fichiers** : `cto_data_catalog.ttl` (ce que l'agence vend : lieux, sentiers, treks, séjours, matériel) et `cto_data_operations.ttl` (son activité : guides, clients, départs, réservations, locations, avis, indisponibilités). Les opérations **réutilisent** les IRI du catalogue (vérifié par SHACL : pas de doublon, pas de ressource inconnue).
- **Catalogue écrit à la main**, avec de vraies données : 10 treks réels (TMB, GR20, Everest, Chemin de l'Inca…), hiérarchie de massifs, ~60 lieux liés à DBpedia par `owl:sameAs`. Chaque IRI DBpedia a été **vérifiée automatiquement** (existence, redirections suivies) ; coordonnées et altitudes copiées de DBpedia.
- **Opérations générées par un script** (`generate_operations.py`, graine aléatoire fixe → toujours le même résultat) : le cœur métier (9 guides, 21 départs, indisponibilités) est écrit à la main dans le script ; les 30 clients, 76 réservations, 73 locations et 35 avis sont générés **en respectant les règles métier** (capacité, stock, réservation avant le départ, avis après la fin du voyage, un client pas sur deux voyages en même temps). Les durées, prix et matériel requis sont **lus dans le catalogue** → cohérence garantie.
- **Cas limites voulus** : départ complet (12/12), départ sans réservation, clients sans réservation, guide sans départ et sans e-mail, client joignable seulement par téléphone, réservations annulées / en attente, trek d'un seul jour, lieux sans coordonnées (Paris, Cusco, Imlil), massif sans lien DBpedia, matériel en rupture de stock, avertissements SHACL (guide qui ne connaît pas la région, client asthmatique sur le trek de l'Everest).
- **Taille** : 2 505 triplets au total ; `python validate.py` → `Conforms: True` (4 warnings attendus).

## 5. Requêtes SPARQL (`cto_query.txt`) ⏳

- 📝 Les 15 questions de compétence, regroupées par besoin (recherche de treks, réservation, matériel, guides, analyses).
- 📝 Tableau « requête → fonctionnalités SPARQL utilisées » (OPTIONAL, UNION, MINUS, FILTER NOT EXISTS, chemins, GROUP BY/HAVING, sous-requêtes, BIND, VALUES, CONSTRUCT, ASK, DESCRIBE, SERVICE DBpedia…).

## 6. Recul : limites et améliorations ⏳

- 📝 Simplifications assumées : le matériel est géré par modèle (stock), pas par objet individuel ; une location n'a pas de dates propres (elle prend celles du départ).
- 📝 Ce qu'on ferait avec OWL (transitivité, propriétés inverses, cardinalités inférées).

## 7. Utilisation de l'IA (section obligatoire) 📝

Chaque membre complète sa partie honnêtement : **quel outil**, **pour quoi**, **ce qu'on a vérifié ou modifié soi-même**.

**Imane** — assistant IA utilisé pour :
- analyser l'énoncé et l'état du dépôt ;
- expliquer le vocabulaire et les notions (SHACL, RDF lists) avec des exemples ;
- proposer et écrire une première version de `cto_shapes.ttl` et de `DATA_RULES.md`, et les tester avec pyshacl.
- Ce que j'ai fait moi-même : 📝 (choix, relecture, compréhension de chaque règle, modifications…)
- 📝 Nommer l'outil précisément dans le rapport final.

**Salma** — 📝
