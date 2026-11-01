# Graphe de connaissances instrumenté pour une agence de trekking

*Mini-projet Web sémantique (EIENWD9), Université Côte d'Azur. Binôme : Imane AMRAOUI, Salma IDMANSOUR.*

> Brouillon : à mettre en page (5 pages max). Les passages [À COMPLÉTER] sont à écrire par chacune.

## 1. Sujet et périmètre

L'énoncé parle d'une *trekking company* dans le titre et d'un *cycling tour operator* dans le texte, d'où le préfixe `cto_` des fichiers. Nous avons choisi le **trekking** et gardé les noms de fichiers demandés.

Le graphe couvre deux côtés de l'agence :
- **le catalogue**, c'est-à-dire ce qu'elle vend : lieux, sentiers, treks, étapes, séjours, matériel ;
- **les opérations**, c'est-à-dire son activité : guides, clients, départs, réservations, locations, avis, indisponibilités.

Notre méthode : partir de **15 questions de compétence**, puis construire le vocabulaire, les règles et les données dont ces questions ont besoin.

**Répartition :** Salma a écrit le vocabulaire RDFS et les requêtes SPARQL. Imane a écrit les shapes SHACL, le catalogue et le générateur de données. Chacune a relu et corrigé le travail de l'autre par pull requests sur GitHub. [À COMPLÉTER / ajuster]

## 2. Vocabulaire RDFS (`cto_schema.ttl`)

Le vocabulaire `cto:` compte **28 classes et 53 propriétés**, avec des labels en anglais et en français. Il réutilise des vocabulaires standard quand c'est possible : `foaf:Person`, `foaf:givenName`, `foaf:mbox`, `schema:birthDate`, `geo:lat` et `geo:long`. Les instances utilisent un autre namespace (`d:`).

Nos principaux choix :
- **Trek ≠ Departure.** Un trek, comme le Tour du Mont-Blanc, est un produit du catalogue. Un départ est une session datée de ce trek, avec ses dates, son nombre de places et son équipe de guides. Les réservations portent sur un départ. Sans cette distinction, on ne pourrait ni calculer les places libres, ni vérifier le planning des guides.
- **Une hiérarchie de classes utile aux requêtes** : `Offer` → `Trek` (→ `HutToHutTrek`, `CampingTrek`, `SummitAscent`) et `TourPackage` ; `Place` → `MountainRange`, `Country`, `Settlement`, `Summit` ; `Equipment` → `CampingGear`, `TechnicalGear`.
- **Un seul `rdfs:domain` par propriété.** Plusieurs domaines signifient leur intersection, pas leur union. Pour une propriété partagée, nous mettons donc une super-classe en domaine : `foaf:Person` pour `cto:speaks`, `cto:Offer` pour `cto:basePrice`.
- **L'itinéraire est une `rdf:List`** d'étapes, parce que l'ordre compte.
- **Sous-propriété** : `cto:leadGuide rdfs:subPropertyOf cto:hasGuide`. Le guide principal fait aussi partie de l'équipe.
- **Une relation n-aire pour les indisponibilités** : la classe `cto:Unavailability` relie un guide, une date de début, une date de fin et un motif. Deux propriétés posées directement sur le guide ne suffiraient pas, car un guide peut avoir plusieurs périodes d'absence.
- **Calculer plutôt que stocker** : la note d'un guide et la liste des guides éligibles sont calculées par des requêtes, pour qu'elles restent toujours à jour.

**Limite de RDFS :** on ne peut pas déclarer `cto:locatedIn` transitif. Les requêtes utilisent donc le chemin `cto:locatedIn*` (Chamonix → massif du Mont-Blanc → Alpes grées → Alpes).

## 3. Contraintes SHACL (`cto_shapes.ttl`)

RDFS **décrit** les données, SHACL les **contraint**. Par exemple, `rdfs:range xsd:integer` n'empêche pas une difficulté de 12, alors que `sh:minInclusive 1 ; sh:maxInclusive 5` l'empêche. Le fichier contient **24 shapes**, sur trois niveaux :

1. **Contraintes simples** :
   - cardinalités (`sh:minCount`, `sh:maxCount`) ;
   - types (`sh:datatype`, `sh:class`) ;
   - formats (`sh:pattern` pour `mailto:`, `tel:` et les IRI DBpedia) ;
   - une seule étiquette par langue (`sh:uniqueLang`) ;
   - liste de valeurs autorisées pour le statut d'une réservation (`sh:in`) ;
   - date de début ≤ date de fin (`sh:lessThanOrEquals` : égales pour un trek d'un jour).
2. **Contraintes logiques** : un client a un e-mail **ou** un téléphone (`sh:or`) ; un guide n'est pas un client (`sh:not`).
3. **Règles métier en SPARQL** (15 contraintes `sh:sparql`) :
   - pas de surréservation ;
   - un guide n'est pas sur deux départs qui se chevauchent, ni sur un départ pendant son indisponibilité ;
   - le guide principal a les certifications exigées par le trek ;
   - le stock de matériel suffit, en comptant les unités sorties le jour où commence chaque départ (le pic de location tombe toujours sur une date de début) ;
   - la réservation est faite avant le départ, et le séjour réservé contient bien le trek ;
   - un avis n'est donné qu'après la fin d'un voyage confirmé avec ce guide ;
   - il n'y a pas de cycle dans `cto:locatedIn` ;
   - l'itinéraire contient une étape par jour, numérotée dans l'ordre de la liste.

**Violation ou Warning ?** Une règle bloque (`sh:Violation`) quand la donnée est fausse. Elle prévient seulement (`sh:Warning`) quand la situation est possible mais à surveiller : un guide qui ne connaît pas la région, un client asthmatique inscrit sur le trek de l'Everest.

**SHACL est plus strict que RDFS** : `cto:highestPoint` accepte n'importe quel lieu (le col de Thorong La par exemple), mais une `cto:SummitAscent` doit viser un `cto:Summit`.

**Nous avons aussi utilisé SHACL pour protéger les liens entre fichiers.** Une shape détecte deux ressources de même classe qui ont le même label, par exemple une deuxième langue « French ». On oblige ainsi les données des opérations à **réutiliser** les IRI du catalogue. Une faute de frappe (`d:englsh`) est aussi détectée, car cette ressource n'a ni type ni label.

**Comment nous l'avons testé :**
- un jeu de données correct donne `Conforms: True` ;
- nous avons ensuite ajouté 13 erreurs volontaires, et les 13 sont détectées ;
- la validation est automatique sur chaque pull request (GitHub Actions + pyshacl, avec inférence RDFS).

## 4. Données et liens LOD (`cto_data_catalog.ttl`, `cto_data_operations.ttl`)

**Le catalogue est écrit à la main, à partir de vraies données :**
- 10 treks réels (TMB, GR20, camp de base de l'Everest, Chemin de l'Inca, Toubkal…), 3 séjours, 10 articles de matériel ;
- une hiérarchie de massifs ;
- 85 ressources (lieux, sentiers) liées à DBpedia par `owl:sameAs`.

Chaque IRI DBpedia a été vérifiée par un script : la ressource existe, et les redirections ont été suivies. Les coordonnées et altitudes sont copiées depuis DBpedia. Nous mettons `owl:sameAs` **seulement entre choses identiques** : un sentier ou un lieu, jamais un trek, car un trek est notre produit commercial et non la montagne elle-même.

**Les opérations sont générées par un script Python** (`generate_operations.py`, rdflib, graine fixe, donc toujours le même résultat) :
- le cœur métier est écrit à la main dans le script : 9 guides, 15 départs, 4 indisponibilités ;
- le volume est généré : 20 clients, 54 réservations, 28 locations, 15 avis ;
- le générateur respecte les règles SHACL ;
- les durées, prix et matériel requis sont lus dans le catalogue.

**Les données sont pilotées par les questions.** Pour chaque requête, nous avons vérifié qu'elle donne un résultat non vide et parlant, et nous avons ajouté les cas qui manquaient :
- un départ complet en juillet 2027 (Q2) ;
- deux guides déjà pris aux dates du départ des Tre Cime (Q7) ;
- les 6 baudriers loués en même temps en août 2026 (Q10).

Nous avons aussi prévu d'autres cas limites : un départ sans réservation, des clients sans réservation, un client joignable seulement par téléphone, un trek d'un seul jour, des lieux sans coordonnées, un massif sans lien DBpedia.

**Total : 1 931 triplets.** La validation donne `Conforms: True`, avec 2 warnings voulus.

## 5. Requêtes SPARQL (`cto_query.txt`)

Les 15 requêtes sont regroupées par besoin : recherche de treks, clients, guides, matériel, analyses. Chacune s'exécute seule sur l'union du schéma et des données. Leurs paramètres (client, départ, période) se changent dans un `VALUES`.

| Besoin | Requêtes et fonctionnalités principales |
|---|---|
| Recherche de treks | Q1 `rdfs:subClassOf*`, repli de langue avec `COALESCE` ; Q2 `YEAR`/`MONTH`, `SUM`, places libres ; Q3 requête fédérée `SERVICE` sur DBpedia et `UNION` ; Q4 distance approchée calculée avec `BIND` ; Q5 parcours ordonné d'une `rdf:List` |
| Clients | Q6 `OPTIONAL`, pour garder les clients qui n'ont jamais voyagé ; Q12 `ASK` « ce client peut-il partir ? » |
| Guides | Q7 « pour tout » avec deux `FILTER NOT EXISTS` imbriqués, plus `MINUS` (planning et indisponibilités) ; Q8 trois sous-requêtes ; Q9 aucune langue commune avec le guide |
| Matériel | Q10 sous-requêtes imbriquées : pic de location par jour, puis maximum ; Q11 coût calculé dans `SUM` |
| Analyses | Q13 chiffre d'affaires et taux de remplissage par massif principal ; Q14 « le premier de chaque groupe » ; Q15 `CONSTRUCT`, la fiche d'un départ sous forme de sous-graphe |

**Comment nous les avons testées :**
- toutes sont exécutées avec rdflib, et nous avons vérifié la plausibilité de chaque résultat ;
- Q6, Q8 et Q13 sont recoupées par un calcul en Python ;
- Q12 est aussi testée sur ses cas négatifs : contre-indication médicale, conflit de dates.

[À COMPLÉTER par Salma : B1 / B2 s'ils sont gardés]

## 6. Recul : outils, limites et améliorations

**Les résultats dépendent du moteur SPARQL.** Nous avons développé avec rdflib et pyshacl, puis tout relancé dans **Corese 4.5**, l'outil utilisé en TD :
- 14 requêtes sur 15 donnent le même nombre de résultats dans les deux outils ;
- **Q2** est refusée par Corese, qui n'accepte pas un `ORDER BY` placé après `HAVING`. Nous l'avons réécrite avec une sous-requête et un `FILTER`, une forme standard acceptée par les deux outils ;
- avec **l'inférence RDFS de Corese** (activée quand on charge aussi le schéma), un article de matériel reçoit aussi le type `cto:Equipment`. Q10 affiche alors chaque article sous deux catégories (17 lignes au lieu de 10). Il faut donc soit garder seulement la classe la plus précise, soit lancer la requête sans inférence [À COMPLÉTER selon la correction choisie] ;
- **Q3** interroge DBpedia en direct. Elle demande un accès à Internet et échoue si DBpedia est lent ou indisponible : il faut la tester à part. rdflib ne transmet pas nos valeurs locales au `SERVICE`, c'est pourquoi la liste des ressources est écrite dans un `VALUES` ;
- **SHACL : dans Corese 4.5, les contraintes `sh:sparql` ne sont pas évaluées.** Un guide placé sur un départ pendant son indisponibilité n'est détecté que par pyshacl. Nos règles métier dépendent donc de l'outil : nous validons avec pyshacl, qui est aussi celui de notre intégration continue.

**Simplifications assumées :**
- le matériel est géré par modèle et par stock, pas par objet individuel ;
- une location n'a pas de dates à elle : elle prend celles du départ ;
- la distance de Q4 est le carré d'une distance en degrés. Elle suffit pour classer des treks, mais ce n'est pas une distance en kilomètres, car SPARQL n'a pas de fonctions trigonométriques ;
- pas de niveau physique pour le client, et pas d'avis sur un trek (seulement sur un guide).

**Ce que OWL apporterait :**
- `cto:locatedIn` déclaré `owl:TransitiveProperty`, ce qui éviterait les chemins `*` ;
- des propriétés inverses (`cto:hasBooking` / `cto:bookedBy`) ;
- `owl:disjointWith` entre `Client` et `Guide`, au lieu d'un `sh:not` ;
- des classes définies comme « départ complet » ou « guide éligible », que le raisonneur calculerait lui-même.

Il faut cependant garder en tête que OWL **déduit** de nouveaux faits, alors que SHACL **refuse** les données invalides. Les deux sont complémentaires.

**Limite du générateur :** changer une seule ligne de ses listes modifie toutes les données aléatoires. Les données doivent donc être figées avant d'écrire les résultats dans le rapport.

## 7. Utilisation de l'IA

Chacune décrit honnêtement l'outil utilisé, pour quoi, et ce qu'elle a vérifié ou décidé elle-même.

**Imane : outil Claude Code (Anthropic)
  - [À COMPLÉTER]

**Salma : outil [À COMPLÉTER].** [À COMPLÉTER]
