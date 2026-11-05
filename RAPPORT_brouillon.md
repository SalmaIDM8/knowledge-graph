# Graphe de connaissances instrumenté pour une agence de trekking

*Mini-projet Web of Linked Data (EIENWD9), Université Côte d'Azur, Parcours IA & Data. Binôme : Imane AMRAOUI, Salma IDMANSOUR.*

## 1. Contexte, objectifs et démarche

Dans ce mini-projet, nous avons conçu et exploité un graphe de connaissances qui représente l'activité d'une agence fictive de trekking : treks, départs, itinéraires, lieux, clients, guides, réservations, locations de matériel et avis.

L'énoncé parle de « trekking company » dans son titre et de « cycling tour operator » dans sa description. Nous avons retenu le trekking et conservé les noms de fichiers `cto_*` demandés. Le catalogue s'appuie sur des destinations réelles, comme le Tour du Mont-Blanc, le GR20, le camp de base de l'Everest et le Chemin de l'Inca. Chaque départ a des dates, une capacité et une équipe de guides. L'agence loue aussi du matériel.

Notre démarche est partie des besoins de l'agence plutôt que d'une liste de classes. Nous avons identifié quatre profils d'utilisateurs :
- un conseiller, qui cherche une offre adaptée à un client ;
- un responsable, qui planifie les départs et affecte les guides ;
- un gestionnaire, qui suit les stocks de matériel ;
- la direction, qui analyse l'activité.

Ces besoins sont devenus quinze questions de compétence. Chaque classe, chaque règle et chaque donnée du graphe sert au moins à l'une d'elles. Quand une requête donnait un résultat vide, nous avons complété les données plutôt que de changer la question.

Salma a pris en charge le vocabulaire RDFS et les requêtes SPARQL. Imane a réalisé les shapes SHACL, le catalogue et le générateur de données opérationnelles. Le travail a été organisé avec des issues et des pull requests GitHub. Chacune a relu les modifications de l'autre, et une validation SHACL automatique était exécutée à chaque pull request.

## 2. Conception du vocabulaire RDFS

Le fichier `cto_schema.ttl` définit 28 classes et 53 propriétés, avec des libellés en français et en anglais. Il réutilise des vocabulaires établis quand c'est pertinent : FOAF pour les personnes, schema.org pour la date de naissance, WGS84 pour les coordonnées. `cto:Client` et `cto:Guide` sont déclarées sous-classes de `foaf:Person`. Ainsi, un outil qui connaît FOAF interprète déjà une partie de nos ressources.

Le choix structurant du modèle est la distinction entre `cto:Trek` et `cto:Departure` :
- un trek est une offre du catalogue, par exemple le Tour du Mont-Blanc ;
- un départ est une session concrète de cette offre, avec des dates, une capacité et une équipe.

Les réservations portent sur le départ, pas sur le trek. Cette séparation permet d'avoir plusieurs sessions d'un même trek, de calculer les places restantes et de détecter les conflits de planning des guides.

Le matériel est modélisé par catégorie et par quantité en stock, et non par objet physique. C'est plus simple pour gérer les disponibilités, mais on ne peut pas suivre l'historique d'un équipement précis.

Les treks sont spécialisés en `HutToHutTrek`, `CampingTrek` et `SummitAscent`. Un trek peut avoir plusieurs de ces types : le GR20 se fait à la fois en refuge et en bivouac. Les lieux (`MountainRange`, `Summit`, `Settlement`…) et le matériel (`CampingGear`, `TechnicalGear`) ont aussi leurs hiérarchies.

Plusieurs décisions évitent des interprétations incorrectes de RDFS. Déclarer deux `rdfs:domain` sur une même propriété signifie que le sujet appartient aux deux classes à la fois (intersection), et non à l'une ou l'autre. Nous déclarons donc un seul domaine, et pour une propriété partagée nous choisissons une super-classe : `cto:speaks`, utilisée par les clients comme par les guides, a pour domaine `foaf:Person`. Le guide principal est relié par `cto:leadGuide`, déclarée sous-propriété de `cto:hasGuide` : il fait donc aussi partie de l'équipe du départ.

L'itinéraire est une `rdf:List`, pour garder l'ordre des étapes. Les indisponibilités des guides sont des ressources `cto:Unavailability` qui regroupent le guide, une période et un motif. C'est une relation n-aire, car un guide peut avoir plusieurs absences. Enfin, les valeurs dérivées, comme la note moyenne d'un guide ou les places restantes, sont calculées par les requêtes au lieu d'être stockées. Elles ne peuvent donc pas se contredire avec les données sources.

RDFS ne permet pas de déclarer `cto:locatedIn` transitive. Les requêtes utilisent donc le chemin `cto:locatedIn*` (de Chamonix au massif du Mont-Blanc, puis aux Alpes).

## 3. Questions de compétence et requêtes SPARQL

Les quinze requêtes de `cto_query.txt` sont regroupées par profil. Chacune est précédée de sa question métier. Ses paramètres (client, départ, période) sont réunis dans un `VALUES`, ce qui permet de tester d'autres cas facilement. La dernière colonne du tableau donne le résultat obtenu sur nos données.

| | Question | Ce qu'elle mobilise | Résultat |
|---|---|---|---|
| **Vente** | Q1 Treks de difficulté ≤ 3 et de moins de 5 jours, libellé en français sinon en anglais | `subClassOf*`, `COALESCE` | 3 treks |
| | Q2 Départs de juillet 2027 qui ont encore des places | sous-requête, `SUM`, `FILTER` | 2 départs (8 et 9 places) |
| | Q3 Treks qui dépassent 4 000 m, avec l'altitude donnée par DBpedia | requête fédérée `SERVICE` | en ligne |
| | Q4 Treks des Alpes ou de l'Himalaya les plus proches d'un client | `BIND` d'une distance | 5 treks classés |
| | Q5 Étapes d'un trek, dans l'ordre, et lieu de chaque nuit | parcours d'une `rdf:List` | 11 étapes |
| **Clients** | Q6 Réservations actives et montant payé, y compris pour les clients qui n'ont jamais voyagé | `OPTIONAL`, agrégats | 20 clients |
| | Q12 Ce client peut-il partir sur ce départ ? | `ASK` | vrai |
| **Planning** | Q7 Guides qui ont toutes les certifications, connaissent la zone et sont libres | double `FILTER NOT EXISTS`, `MINUS` | Keller, Rossi |
| | Q8 Groupes encadrés, note moyenne et certifications de chaque guide | trois sous-requêtes | 9 guides |
| | Q9 Participants sans langue commune avec leur guide | `FILTER NOT EXISTS` | 7 participants |
| **Matériel** | Q10 Stock restant en août 2026, par catégorie, et articles épuisés | sous-requêtes imbriquées | 10 articles, baudriers épuisés |
| | Q11 Matériel loué par chaque participant d'un départ, et coût | calcul dans `SUM` | 4 lignes |
| **Direction** | Q13 Chiffre d'affaires et taux de remplissage par massif | agrégats sur `locatedIn*` | 6 massifs |
| | Q14 Massif préféré de chaque nationalité, ex æquo compris | maximum par groupe | 11 lignes |
| | Q15 Fiche complète d'un départ | `CONSTRUCT` | sous-graphe de 61 triplets |

Q7 illustre une quantification universelle. Un guide est éligible s'il n'existe aucune certification exigée par le trek qu'il ne possède pas. SPARQL n'a pas d'opérateur « pour tout » : cette condition s'écrit avec deux `FILTER NOT EXISTS` imbriqués. Les guides déjà affectés à un autre départ, ou indisponibles sur la période, sont ensuite retirés avec `MINUS`.

Q10 demande aussi un raisonnement. Ce qui compte, c'est le nombre maximal d'articles loués en même temps. Ce pic tombe toujours sur une date de début de départ, puisque c'est le seul moment où de nouvelles locations commencent. Il suffit donc de compter les locations en cours à ces dates.

Nous avons vérifié la plausibilité de chaque résultat. Q6, Q8 et Q13 ont été recalculées indépendamment en Python à partir des mêmes données. Q12 a aussi été testée sur des cas où la réponse doit être négative : une contre-indication médicale, un conflit de dates.

Deux conventions sont à connaître pour lire les résultats :
- **La date de référence du scénario est le 30 octobre 2026.** Elle est écrite en dur dans Q8 : un groupe compte comme « encadré » seulement si son départ s'est terminé avant cette date. Nous n'utilisons pas `NOW()`, sinon le résultat changerait selon le jour d'exécution.
- **Q13 compte aussi les départs futurs.** Son chiffre d'affaires est la somme des montants déjà encaissés, y compris les acomptes des réservations à venir, et non le prix total des voyages. Son taux de remplissage inclut lui aussi les réservations futures non annulées.

## 4. Validation avec SHACL

RDFS permet des inférences, mais il ne rejette jamais une donnée. Une difficulté de 12 ou une réservation pour zéro personne passent sans erreur. Pour contrôler notre graphe, `cto_shapes.ttl` définit 24 shapes SHACL, sur trois niveaux.

**1. Les contraintes de forme :**
- cardinalités (`sh:minCount`, `sh:maxCount`) et types (`sh:datatype`, `sh:class`) ;
- bornes : difficulté et note entre 1 et 5 ;
- formats avec `sh:pattern` : `mailto:`, `tel:`, IRI DBpedia ;
- un seul libellé par langue (`sh:uniqueLang`) ;
- un statut choisi dans une liste (`sh:in`) ;
- une date de début antérieure ou égale à la date de fin.

Pour les dates, un premier essai avec `sh:lessThan` interdisait les treks d'une journée. `sh:lessThanOrEquals` a corrigé ce cas.

**2. Les contraintes logiques :** un client doit avoir un e-mail ou un téléphone (`sh:or`), et un guide ne peut pas être aussi client (`sh:not`).

**3. Quinze règles métier en SHACL-SPARQL (`sh:sparql`)** : pas de surréservation, pas de conflit d'affectation ni d'indisponibilité des guides, certifications du guide principal, stock suffisant, réservation antérieure au départ, avis seulement après un voyage terminé, pas de cycle dans `cto:locatedIn`, une étape par jour d'itinéraire.

Nous distinguons les violations (`sh:Violation`), qui sont des données à corriger, des avertissements (`sh:Warning`), qui demandent une vérification humaine. Par exemple, un guide qui ne connaît pas la région, ou un client asthmatique inscrit au trek de l'Everest, déclenchent un avertissement et non un rejet. SHACL est aussi plus strict que le schéma sur un point voulu : un `SummitAscent` doit viser un `Summit`, alors que RDFS accepte n'importe quel lieu.

Une shape protège la cohérence entre le catalogue et les opérations : elle signale deux ressources de même classe qui portent le même libellé, par exemple une langue « French » déclarée deux fois au lieu d'être réutilisée.

**Test des règles.** Nous avons introduit quatorze erreurs dans les données réelles :
- dates inversées, départ sans date de fin ;
- réservation pour zéro personne, statut invalide ;
- surréservation, guide affecté pendant un congé, stock insuffisant ;
- note supérieure à 5 ;
- séjour qui ne contient pas le trek réservé ;
- cycle de localisation, langue dupliquée, durée en double ;
- e-mail écrit comme un simple texte ;
- guide déclaré client.

Les quatorze ont été détectées par les règles attendues. Un cas témoin, la même surréservation mais sur une réservation annulée, ne déclenche rien, comme prévu. Ce test a aussi montré une limite : en cas de dépassement de stock, le rapport signale une location déjà présente, et non la nouvelle location qui a causé le dépassement.

## 5. Données et liens avec le Web de données

Les données sont réparties entre `cto_data_catalog.ttl` et `cto_data_operations.ttl`.

**Le catalogue** est écrit à la main à partir d'informations réelles : 10 treks, 3 séjours, 10 articles de matériel et une hiérarchie de massifs.

**Les opérations** sont produites par `generate_operations.py` (rdflib, graine aléatoire fixe) :
- les situations clés sont écrites à la main : 9 guides, 15 départs, 4 indisponibilités ;
- le script génère le reste : 20 clients, 54 réservations, 28 locations et 15 avis ;
- il reprend les durées, les prix et le matériel du catalogue, et respecte les règles SHACL.

Nous avons ajouté des situations ciblées pour les requêtes : un départ complet en juillet 2027 (Q2), deux guides déjà pris aux dates du Tre Cime (Q7), six baudriers loués en même temps en août 2026 (Q10). Nous avons aussi ajouté des cas limites : un départ sans réservation, des clients qui n'ont jamais voyagé, un client joignable seulement par téléphone, un trek d'une journée.

Le graphe compte 1 931 triplets. Les lieux et sentiers sont reliés à DBpedia par 85 liens `owl:sameAs`. Toutes ces IRI ont été vérifiées par script, en suivant les redirections. Les coordonnées et les altitudes viennent de DBpedia.

Nous n'utilisons `owl:sameAs` que pour deux ressources qui désignent vraiment la même chose. Le sentier du Tour du Mont-Blanc est lié à `dbr:Tour_du_Mont_Blanc`. Notre offre de trek ne l'est pas : elle a ses propres prix, durées et départs, que l'on attribuerait sinon au sentier.

La validation donne aucune violation et deux avertissements voulus. Selon la spécification SHACL, un avertissement suffit pour que le rapport ne soit pas conforme : pyshacl lancé sans option affiche donc `Conforms: False`. Notre script `validate.py` accepte les avertissements et n'échoue que sur les violations.

## 6. Analyse critique, limites et perspectives

En faisant tourner notre travail dans plusieurs outils, nous avons trouvé des différences importantes. Nous avons développé avec rdflib et pyshacl, puis exécuté les requêtes dans Corese 4.5, l'outil utilisé en TD.
- **Q2** a dû être réécrite, car Corese refusait un `ORDER BY` placé après `HAVING`. Une sous-requête suivie d'un `FILTER` fonctionne dans les deux outils.
- **Q10** : quand le schéma est chargé, l'inférence RDFS de Corese ajoute le type `cto:Equipment` aux baudriers déjà typés `cto:TechnicalGear`. Les articles apparaissaient alors dans deux catégories (17 lignes au lieu de 10). Nous ne gardons plus que la catégorie la plus précise, et le résultat est le même avec ou sans inférence.
- **Les contraintes `sh:sparql`** n'ont pas été évaluées par la validation SHACL de Corese lors de nos essais. Des règles comme « un guide affecté pendant son congé » ne sont donc vérifiées que par pyshacl, qui reste l'outil de l'intégration continue.

Q3 dépend de DBpedia et donc d'une connexion Internet : c'est une limite de reproductibilité. De plus, rdflib ne transmet pas nos variables locales au service distant. Les ressources à interroger sont donc écrites dans un `VALUES`.

Le modèle a aussi ses limites :
- le matériel est géré par quantité et non par exemplaire ;
- une location reprend les dates du départ ;
- la proximité de Q4 est le carré d'une distance en degrés (SPARQL n'a pas de trigonométrie) : elle suffit pour classer, pas pour mesurer en kilomètres ;
- le client n'a pas de niveau physique, qui serait pourtant le premier critère pour recommander un trek.

Nos IRI suivent les conventions Linked Data, mais elles ne sont publiées sur aucun serveur. On ne peut pas les déréférencer, et le troisième principe Linked Data n'est donc pas respecté. Les mettre en ligne serait une amélioration importante.

OWL permettrait d'aller plus loin : `cto:locatedIn` transitive, des propriétés inverses, des classes disjointes, ou des classes définies comme « départ complet » et « guide éligible ». OWL déduirait ces faits, mais il ne remplacerait pas SHACL. Avec OWL, un guide déclaré client rend le graphe incohérent. Avec SHACL, il produit un message qui dit précisément quoi corriger.

Enfin, la graine fixe rend la génération reproductible. Mais modifier une seule liste du générateur change une grande partie des données. Il faut donc figer les données avant de recopier des résultats chiffrés dans le rapport.

## 7. Utilisation de l'intelligence artificielle

**Imane.** J'ai utilisé Claude Code, un assistant en ligne de commande qui a accès au dépôt. Il m'a servi à :
- vérifier des points précis de syntaxe et de comportement des outils (listes RDF, SHACL-SPARQL, inférence) ;
- obtenir une première version de certaines shapes, du catalogue et du générateur ;
- lancer les tests avec pyshacl et rdflib, et vérifier les IRI DBpedia par script.

Les décisions sont restées les nôtres. J'ai choisi de partir des questions métier et de n'ajouter que les données utiles à ces questions. J'ai organisé le travail pour que l'assistant n'intervienne pas dans la partie de Salma. En relisant Q7, j'ai remarqué qu'elle faisait référence à un départ qui n'existait pas dans nos données.

Plusieurs propositions de l'outil étaient fausses :
- `sh:lessThan` excluait les treks d'une journée ;
- une première règle de stock donnait de fausses alertes, et c'est Salma qui l'a corrigée ;
- des requêtes qui fonctionnaient dans rdflib échouaient ou donnaient des doublons dans Corese.

Aucun de ces problèmes ne se voyait à la lecture. Nous les avons trouvés en exécutant le code dans les outils du cours, en testant des cas positifs et négatifs, et en relisant le travail de l'autre.

**Salma.** [À écrire par Salma, à la première personne : l'outil utilisé ou non, pour quelles tâches, ce qu'elle a vérifié ou corrigé elle-même.]

## Conclusion

Le graphe compte 1 931 triplets. Il repose sur un vocabulaire RDFS de 28 classes et 53 propriétés, 24 shapes SHACL et quinze requêtes SPARQL, qui couvrent la vente, la planification, le matériel et le pilotage de l'agence.