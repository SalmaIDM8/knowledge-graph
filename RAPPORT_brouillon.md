# Graphe de connaissances instrumenté pour une agence de trekking

*Mini-projet Web sémantique (EIENWD9), Université Côte d'Azur. Binôme : Imane AMRAOUI, Salma IDMANSOUR.*

## 1. Sujet, démarche et répartition

L'énoncé parle d'une *trekking company* dans son titre et d'un *cycling tour operator* dans son texte. Nous avons choisi le trekking et gardé les noms de fichiers imposés (`cto_*`). Notre agence fictive vend des treks réels (Tour du Mont-Blanc, GR20, camp de base de l'Everest, Chemin de l'Inca…) et organise des départs datés, encadrés par ses guides, avec location de matériel.

Nous n'avons pas commencé par le vocabulaire mais par les **questions que l'agence se pose** : un vendeur cherche un trek pour un client, le responsable du planning cherche un guide libre, le magasin vérifie son stock, la direction regarde son chiffre d'affaires. Nous en avons retenu quinze (section 3). Chaque classe, chaque règle et chaque donnée du graphe doit servir à au moins une de ces questions. Quand une requête donnait un résultat vide ou sans intérêt, nous avons complété les données plutôt que de modifier la question.

Salma a écrit le vocabulaire RDFS et les requêtes SPARQL. Imane a écrit les shapes SHACL, le catalogue et le générateur de données opérationnelles. Le travail est passé par des *issues* et des *pull requests* sur GitHub : chacune relisait la PR de l'autre, et une validation SHACL automatique tournait à chaque PR.

## 2. Modélisation RDFS (`cto_schema.ttl`)

Le vocabulaire `cto:` compte 28 classes et 53 propriétés, labellisées en anglais et en français. Nous réutilisons FOAF pour les personnes (`foaf:Person`, `foaf:givenName`, `foaf:mbox`), schema.org pour la date de naissance et WGS84 pour les coordonnées. Nos classes s'y rattachent par `rdfs:subClassOf` (`cto:Client` et `cto:Guide` sont des `foaf:Person`) : un outil qui ne connaît que FOAF comprend donc déjà une partie de nos données.

**Le choix le plus important est de séparer `Trek` et `Departure`.** Un trek est un produit du catalogue, par exemple le Tour du Mont-Blanc. Un départ est une session datée de ce trek, avec sa capacité et son équipe. Les réservations portent sur un départ, pas sur un trek. Sans cette séparation, il serait impossible de compter les places restantes ou de vérifier qu'un guide n'est pas à deux endroits à la fois. Nous avons hésité à faire la même chose pour le matériel (un objet par casque physique). Nous avons gardé un modèle par stock (« 10 casques »), plus simple, mais qui ne permet pas de suivre un casque précis.

Les autres choix de modélisation :
- **Hiérarchies utiles aux requêtes** : `Trek` a trois sous-classes (`HutToHutTrek`, `CampingTrek`, `SummitAscent`), et un trek peut en avoir plusieurs (le GR20 se fait en refuge et en bivouac). Les lieux ont aussi une hiérarchie (`MountainRange`, `Summit`, `Settlement`…), ainsi que le matériel (`CampingGear`, `TechnicalGear`).
- **Un seul domaine par propriété.** Deux `rdfs:domain` signifient « les deux à la fois », et non « l'un ou l'autre ». Pour `cto:speaks`, utilisée par les clients comme par les guides, nous avons donc mis `foaf:Person` en domaine.
- **`cto:leadGuide` est une sous-propriété de `cto:hasGuide`** : le guide principal fait automatiquement partie de l'équipe du départ.
- **L'itinéraire est une `rdf:List`** d'étapes, car l'ordre des jours compte et un simple ensemble de triplets le perdrait.
- **Les indisponibilités sont une relation n-aire** (`cto:Unavailability` : un guide, deux dates, un motif). Un guide peut avoir plusieurs périodes d'absence, ce qu'on ne peut pas exprimer avec deux propriétés posées directement sur le guide.
- **Calculer plutôt que stocker.** La note moyenne d'un guide ou le nombre de places libres ne sont pas écrits dans les données : ils sont calculés par les requêtes, et restent ainsi toujours justes.

RDFS ne permet pas de déclarer `cto:locatedIn` transitive. Les requêtes utilisent donc le chemin `cto:locatedIn*` (Chamonix → massif du Mont-Blanc → Alpes grées → Alpes).

## 3. Scénarios et questions de compétence (`cto_query.txt`)

Les quinze questions sont regroupées par utilisateur. Chacune s'exécute seule, sur l'union du schéma et des données. Ses paramètres (client, départ, période) se changent dans un `VALUES`. La dernière colonne donne le résultat obtenu sur nos données.

| | Question | Ce qu'elle mobilise | Résultat |
|---|---|---|---|
| **Vente** | Q1 Treks faciles (difficulté ≤ 3) de moins de 5 jours, label en français sinon en anglais | `subClassOf*`, `COALESCE` | 3 treks |
| | Q2 Départs de juillet 2027 qui ont encore des places | sous-requête avec `SUM`, `FILTER` | 2 départs (8 et 9 places) |
| | Q3 Treks qui dépassent 4 000 m, avec l'altitude donnée par DBpedia | requête fédérée `SERVICE` | (en ligne) |
| | Q4 Treks des Alpes ou de l'Himalaya les plus proches de chez un client | `BIND` d'une distance | 5 treks classés |
| | Q5 Étapes d'un trek, dans l'ordre, et lieu de chaque nuit | parcours d'une `rdf:List` | 11 étapes |
| **Clients** | Q6 Réservations actives et montant payé par client, y compris ceux qui n'ont jamais voyagé | `OPTIONAL`, agrégats | 20 clients |
| | Q12 Ce client peut-il partir sur ce départ ? | `ASK` | vrai |
| **Planning** | Q7 Guides qui ont *toutes* les certifications exigées, connaissent la zone et sont libres | double `FILTER NOT EXISTS`, `MINUS` | Keller, Rossi |
| | Q8 Groupes encadrés, note moyenne et certifications de chaque guide | trois sous-requêtes | 9 guides |
| | Q9 Participants sans langue commune avec leur guide | `FILTER NOT EXISTS` | 7 participants |
| **Matériel** | Q10 Stock restant en août 2026 par catégorie, et articles épuisés | sous-requêtes imbriquées | 10 articles, baudriers épuisés |
| | Q11 Matériel loué par chaque participant d'un départ, et son coût | coût calculé dans `SUM` | 4 lignes |
| **Direction** | Q13 Chiffre d'affaires et taux de remplissage par massif | agrégats sur `locatedIn*` | 6 massifs |
| | Q14 Massif préféré de chaque nationalité (avec les égalités) | « le maximum de chaque groupe » | 11 lignes |
| | Q15 Fiche complète d'un départ | `CONSTRUCT` | sous-graphe de 61 triplets |

La question la plus intéressante est **Q7**, car c'est une quantification universelle. Un guide convient s'il n'existe **aucune** certification exigée par le trek qu'il n'ait pas. SPARQL n'a pas de « pour tout ». Nous l'écrivons donc avec deux `FILTER NOT EXISTS` imbriqués, puis nous retirons avec `MINUS` les guides déjà pris ou indisponibles à ces dates. Q10 a aussi demandé de la réflexion. Le nombre de baudriers sortis varie d'un jour à l'autre, et c'est le pic qui compte. Ce pic tombe toujours un jour de début de départ, car c'est le seul moment où des locations s'ajoutent. Il suffit donc de compter les locations en cours à chaque date de début.

Nous avons vérifié la plausibilité de chaque résultat. Q6, Q8 et Q13 ont été recalculées en Python à partir des mêmes données. Q12 a aussi été testée sur des cas où la réponse doit être « non » : contre-indication médicale, conflit de dates.

## 4. Contraintes SHACL (`cto_shapes.ttl`)

RDFS déduit des faits mais ne refuse jamais rien : une difficulté de 12 ou une réservation pour 0 personne passent sans erreur. Les 24 shapes ajoutent ce contrôle, à trois niveaux.

1. **Des contraintes de forme** : cardinalités, types, bornes (difficulté entre 1 et 5, note entre 1 et 5), formats (`sh:pattern` pour les `mailto:`, les `tel:` et les IRI DBpedia), un seul label par langue (`sh:uniqueLang`), un statut choisi dans une liste (`sh:in`), et une date de début antérieure ou égale à la date de fin. Nous avions d'abord mis `sh:lessThan`, qui interdisait les treks d'une journée : `sh:lessThanOrEquals` les accepte.
2. **Des contraintes logiques** : un client doit avoir un e-mail **ou** un téléphone (`sh:or`), et un guide ne peut pas être un client (`sh:not`).
3. **Quinze règles métier en SHACL-SPARQL**, que la forme seule ne peut pas exprimer. Par exemple :
   - pas de surréservation ;
   - pas de guide sur deux départs qui se chevauchent, ni pendant une indisponibilité ;
   - le guide principal a les certifications exigées ;
   - le stock de matériel suffit ;
   - une réservation est faite avant le départ ;
   - un avis n'est donné qu'après un voyage terminé avec ce guide ;
   - pas de cycle dans `cto:locatedIn` ;
   - une étape par jour d'itinéraire.

Nous distinguons ce qui est **faux** (`sh:Violation`) de ce qui est **possible mais à surveiller** (`sh:Warning`). Un guide qui ne connaît pas la région, ou un client asthmatique inscrit pour l'Everest, ne sont pas des erreurs de données, mais l'agence doit être prévenue. SHACL est aussi plus strict que notre schéma sur un point voulu. En RDFS, le point culminant d'un trek peut être n'importe quel lieu (le col du Thorong La par exemple). En SHACL, une `SummitAscent` doit viser un `Summit`.

Une shape protège aussi le lien entre nos deux fichiers de données. Elle signale deux ressources de même classe qui portent le même label. Si le fichier des opérations redéclarait la langue « French » au lieu de réutiliser `d:french` du catalogue, l'erreur serait détectée.

**Test des shapes.** Sur les données réelles, nous avons injecté quatorze erreurs, une par règle à tester : départ qui finit avant de commencer, réservation pour 0 personne, statut écrit en texte au lieu d'une valeur de la liste, surréservation, guide placé pendant son congé, baudrier en rupture de stock, note de 6/5, séjour qui ne contient pas le trek réservé, cycle dans les lieux, langue déclarée deux fois, durée en double, e-mail écrit comme une chaîne, guide déclaré client, départ sans date de fin. Les quatorze sont détectées par la règle attendue. Un cas témoin (la même surréservation, mais sur une réservation annulée) ne déclenche rien, comme il se doit. Ce test a aussi montré une limite : l'erreur de stock est signalée sur une location déjà existante, et non sur celle qui vient d'être ajoutée et qui a causé le dépassement.

## 5. Données et liens LOD (`cto_data_catalog.ttl`, `cto_data_operations.ttl`)

Le **catalogue** est écrit à la main à partir de données réelles : 10 treks, 3 séjours, 10 articles de matériel et une hiérarchie de massifs. Nous avons relié 85 lieux et sentiers à DBpedia par `owl:sameAs`, et un script a vérifié que chaque IRI existe (en suivant les redirections). Les coordonnées et les altitudes viennent de DBpedia. Nous ne mettons `owl:sameAs` qu'entre choses vraiment identiques. Le sentier du Tour du Mont-Blanc est lié à `dbr:Tour_du_Mont_Blanc`, mais notre trek ne l'est pas, car c'est un produit commercial (prix, durée, guides), pas le sentier lui-même. Affirmer qu'ils sont identiques donnerait au sentier DBpedia un prix et des départs.

Les **opérations** sont produites par un script Python (`generate_operations.py`, rdflib, graine aléatoire fixe). Les situations importantes sont écrites à la main : 9 guides, 15 départs et 4 indisponibilités. Le volume est généré : 20 clients, 54 réservations, 28 locations et 15 avis. Le générateur lit les durées, les prix et le matériel dans le catalogue, et respecte les règles SHACL. Nous avons ajouté exprès les cas dont les requêtes avaient besoin : un départ complet en juillet 2027 (Q2), deux guides déjà pris aux dates du Tre Cime (Q7), six baudriers loués en même temps en août 2026 (Q10). Nous avons aussi ajouté des cas limites : un départ sans réservation, des clients qui n'ont jamais voyagé, un client joignable seulement par téléphone, un trek d'un jour.

Au total, le graphe compte 1 931 triplets. La validation ne donne **aucune violation et deux avertissements voulus** (les deux situations à surveiller décrites en section 4). Selon la spécification SHACL, un avertissement suffit pour que le rapport indique `sh:conforms false`. Notre script `validate.py` considère donc les avertissements comme acceptables, mais pyshacl lancé sans option affichera `Conforms: False`.

## 6. Recul : outils, limites et améliorations

**Les résultats dépendent de l'outil.** Nous avons développé avec rdflib et pyshacl, puis tout relancé dans Corese 4.5, l'outil des TD. Trois différences sont apparues :
- **Q2** était refusée par Corese, qui n'accepte pas un `ORDER BY` après `HAVING`. Nous l'avons réécrite avec une sous-requête et un `FILTER`, une forme acceptée partout.
- **Q10** : quand le schéma est chargé, l'inférence RDFS de Corese ajoute à chaque baudrier le type `cto:Equipment`, en plus de `cto:TechnicalGear`. Q10 affichait alors chaque article dans deux catégories (17 lignes au lieu de 10). Nous gardons maintenant seulement la catégorie la plus précise. La requête donne 10 lignes avec ou sans inférence.
- **Les contraintes `sh:sparql` ne sont pas évaluées par la validation SHACL de Corese.** Un guide placé pendant son congé n'est détecté que par pyshacl. Nos quinze règles métier ne sont donc vérifiées que par pyshacl, qui est aussi l'outil de notre intégration continue.

De plus, **Q3** interroge DBpedia en direct : elle demande un accès Internet et échoue si DBpedia est indisponible. rdflib n'envoie pas nos variables locales au service distant, c'est pourquoi la liste des points à interroger est écrite dans un `VALUES`.

**Limites du modèle :**
- le matériel est géré par stock et non par objet ;
- une location reprend les dates du départ ;
- la « distance » de Q4 est le carré d'une distance en degrés, car SPARQL n'a pas de trigonométrie : elle suffit pour classer, pas pour donner des kilomètres ;
- le client n'a pas de niveau physique, alors que ce serait le premier critère réel pour choisir un trek ;
- nos IRI (`http://ns.cto-trekking.org/…#`) suivent les principes Linked Data pour le nommage et les liens. Mais elles ne sont publiées sur aucun serveur : on ne peut pas les déréférencer, et le troisième principe n'est donc pas respecté.

Un dernier point pratique : comme le générateur part d'une graine aléatoire, changer une seule ligne de ses listes modifie toutes les données générées. Il faut donc figer les données avant de recopier des résultats dans le rapport.

**Ce qu'OWL apporterait :**
- `cto:locatedIn` transitive, au lieu des chemins `*` ;
- des propriétés inverses (`cto:hasBooking` / `cto:bookedBy`) ;
- `owl:disjointWith` entre `Client` et `Guide` ;
- des classes définies (« départ complet », « guide éligible ») calculées par le raisonneur.

OWL **déduirait** ces faits, mais il ne remplacerait pas SHACL, qui **refuse** les données fausses. Avec OWL, un guide déclaré client rendrait le graphe incohérent. Avec SHACL, il produit un message précis qui dit quoi corriger.

## 7. Utilisation de l'IA

**Imane : Claude Code (Anthropic), un assistant en ligne de commande avec accès au dépôt.**
- *Ce que l'outil a fait :*
  - il m'a expliqué les notions que je maîtrisais mal (listes RDF, SHACL-SPARQL, inférence), avec des exemples ;
  - il a proposé une première version des shapes, du catalogue et du générateur ;
  - il a lancé les tests (pyshacl, rdflib) et vérifié les IRI DBpedia par script.
- *Ce que j'ai décidé :*
  - la règle selon laquelle les données suivent les questions, et non l'inverse ;
  - l'organisation du binôme : on s'attribue une issue avant de travailler dessus, et l'assistant ne touche pas au travail de Salma ;
  - en relisant Q7, j'ai vu que le départ utilisé n'existait pas dans nos données.
- *Ce qui était faux dans ses propositions :*
  - `sh:lessThan` interdisait les treks d'un jour ;
  - la première règle de stock donnait de fausses alertes, et c'est Salma qui l'a corrigée ;
  - des requêtes qui marchaient dans rdflib échouaient ou se dédoublaient dans Corese.

  Aucun de ces problèmes n'était visible à la lecture. C'est en exécutant le code sur les outils du cours que nous les avons trouvés. Nous en concluons que la validation SHACL et les tests ont servi de garde-fou contre les erreurs de l'IA autant que contre les erreurs de saisie.

**Salma : [outil].** [À COMPLÉTER par Salma : pour quoi elle l'a utilisé, ce qu'elle a vérifié ou corrigé elle-même.]
