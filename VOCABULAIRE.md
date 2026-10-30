# Vocabulaire du projet (issue #2)

Le vocabulaire est défini dans [`cto_schema.ttl`](cto_schema.ttl) : 27 classes et 49 propriétés, avec des labels en anglais et en français.
Ce document résume ce qui a été choisi et ce qui a changé par rapport à notre brainstorming.

## Préfixes

| Préfixe | IRI | Usage |
|---|---|---|
| `cto:` | `http://ns.cto-trekking.org/schema#` | nos classes et propriétés |
| `d:` | `http://ns.cto-trekking.org/data#` | nos instances (fichiers de données) |
| `foaf:` | `http://xmlns.com/foaf/0.1/` | personnes : `foaf:Person`, `givenName`, `familyName`, `mbox`, `phone` |
| `schema:` | `http://schema.org/` | `schema:birthDate` |
| `geo:` | `http://www.w3.org/2003/01/geo/wgs84_pos#` | coordonnées `geo:lat` / `geo:long` |
| `dbr:` | `http://dbpedia.org/resource/` | liens vers DBpedia avec `owl:sameAs` |

On garde un namespace pour le schéma et un autre pour les données, comme le recommande le cours.
On nomme les classes en `PascalCase` et les propriétés en `camelCase`.

## Les classes

| Thème | Classes |
|---|---|
| Lieux | `Place` → `MountainRange`, `Country`, `Settlement`, `Summit` |
| Catalogue | `Offer` → `Trek` (→ `HutToHutTrek`, `CampingTrek`, `SummitAscent`) et `TourPackage` ; `HikingTrail`, `Stage` |
| Planning | `Departure` |
| Personnes | `Client`, `Guide` (sous-classes de `foaf:Person`) ; `Language`, `Certification`, `MedicalCondition`, `Insurer` |
| Réservations | `Booking`, `BookingStatus` (valeurs : `cto:Pending`, `cto:Confirmed`, `cto:Cancelled`) |
| Matériel | `Equipment` → `CampingGear`, `TechnicalGear` ; `Rental` |
| Avis | `Review` |

## Du brainstorming au vocabulaire

### Guide
| Brainstorming | Vocabulaire |
|---|---|
| nom | `foaf:givenName`, `foaf:familyName` |
| âge | `schema:birthDate`. On stocke la date de naissance, car l'âge change chaque année. |
| sexe | **supprimé** : aucune question n'en a besoin, et c'est une donnée personnelle |
| note | **pas stockée** : c'est la moyenne des `cto:Review` (`cto:rating`, `cto:aboutGuide`, `cto:reviewDate`) |
| certifications | `cto:hasCertification` → `cto:Certification` |
| zones connues | `cto:knowsArea` → `cto:MountainRange` |
| langues | `cto:speaks` → `cto:Language` |

### Client
| Brainstorming | Vocabulaire |
|---|---|
| nom, email, téléphone | `foaf:givenName`, `foaf:familyName`, `foaf:mbox` ou `foaf:phone` (au moins l'un des deux, vérifié par SHACL) |
| adresse / ville | `cto:livesIn` → `cto:Settlement`. Les coordonnées de la ville servent pour les distances. |
| âge | `schema:birthDate` |
| nationalité | `cto:nationality` → `cto:Country` |
| langues | `cto:speaks` → `cto:Language` |
| conditions médicales | `cto:hasMedicalCondition` → `cto:MedicalCondition` (et côté trek : `cto:notRecommendedFor`) |
| assurance | `cto:insuredBy` → `cto:Insurer`. On peut ainsi chercher l'assureur le plus utilisé. |

### Trek
| Brainstorming | Vocabulaire |
|---|---|
| `owl:sameAs` | **déplacé** : un trek est **notre** produit commercial, il n'est pas *identique* à une ressource DBpedia. Le `owl:sameAs` se met sur le **sentier** (`cto:HikingTrail`, ex. `dbr:Tour_du_Mont_Blanc`) et sur les **lieux**. Le trek pointe vers le sentier avec `cto:followsTrail`. |
| coordonnées | sur les lieux (`geo:lat`, `geo:long`), pas sur le trek |
| départ / arrivée | `cto:startPoint`, `cto:endPoint` → `cto:Settlement` |
| niveau de difficulté | `cto:difficulty` (entier de 1 à 5) |
| certifications requises | `cto:requiresCertification` → `cto:Certification` |
| liste des guides éligibles | **pas stockée** : on la calcule par une requête (certifications du guide + zone connue). Si on la stockait, elle ne serait plus à jour dès qu'un guide change. |
| équipements, type d'équipement | `cto:requiresEquipment` → `cto:Equipment`. Une tente, un piolet, etc. sont des **instances** ; seules deux sous-classes existent (`CampingGear`, `TechnicalGear`). |
| (nouveau) | `cto:durationDays`, `cto:basePrice`, `cto:maxGroupSize`, `cto:highestPoint` → `cto:Summit`, `cto:inMountainRange` |

### Ce qu'on a ajouté (et pourquoi)
- **`cto:Departure`** : c'est le changement le plus important. Un trek (ex. le Tour du Mont-Blanc) est proposé plusieurs fois. Les **dates**, le **nombre de places** et le **guide** appartiennent à un départ, pas au trek. Les questions 2, 10, 11 et 18 en ont besoin. Propriétés : `cto:ofTrek`, `cto:startDate`, `cto:endDate`, `cto:capacity`, `cto:leadGuide`.
- **`cto:Booking`** : `cto:bookedBy`, `cto:forDeparture`, `cto:bookingDate`, `cto:numberOfParticipants`, `cto:amountPaid`, `cto:status`, `cto:withPackage`.
- **`cto:Rental`** : `cto:forBooking`, `cto:rentedItem`, `cto:quantity`. Côté matériel : `cto:stockQuantity`, `cto:dailyRentalPrice`.
- **`cto:Stage`** et **`cto:itinerary`** : les étapes d'un trek forment une **liste RDF ordonnée** (`rdf:List`, vue en cours), parce que l'ordre compte (question 21). Chaque étape a `cto:dayNumber`, `cto:passesBy` et `cto:overnightAt`.
- **`cto:TourPackage`** : un trek avec des extras. Il est relié au trek par `cto:includesTrek`.

## Trois points du cours qu'on applique (à expliquer dans le rapport)

1. **Plusieurs `rdfs:domain` = intersection, pas union.** `cto:speaks` sert pour les clients **et** les guides. Si on déclarait deux domaines, `Client` et `Guide`, ça voudrait dire « Client ET Guide ». On met donc un seul domaine, la super-classe commune `foaf:Person`. Pour la même raison, `cto:basePrice` a le domaine `cto:Offer`, la super-classe de `Trek` et `TourPackage`.
2. **Transitivité.** RDFS ne permet pas de dire que `cto:locatedIn` est transitif. Ce sont les requêtes qui suivent le chemin `cto:locatedIn+`. Par exemple : Dolomites → Alpes calcaires du Sud → Alpes, ce qui permet de trouver les « treks dans les Alpes ».
3. **RDFS décrit, il ne contraint pas.** `rdfs:range xsd:integer` n'empêche pas une difficulté de 12. Les contraintes (difficulté de 1 à 5, cardinalités…) iront dans `cto_shapes.ttl` (issue #3).

On a aussi une **sous-propriété** : `cto:leadGuide rdfs:subPropertyOf cto:hasGuide`.
