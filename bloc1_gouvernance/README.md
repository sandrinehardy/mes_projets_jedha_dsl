# Bloc 1 – Data Governance : gouvernance des données de Spotify

Lien GitHub du projet : https://github.com/sandrinehardy/mes_projets_jedha_dsl/tree/main/bloc1_gouvernance

Projet du bloc 1 (gouvernance des données). Il répond à une question : comment Spotify peut-il mieux gouverner ses données, c'est-à-dire savoir qui décide, qui applique et quelles règles suivre ? Le travail est livré en trois rapports, qui se lisent dans l'ordre : l'état des lieux, les règles à adopter, puis la manière de les mettre en place.

## Le fil conducteur

1. **Diagnostic** : la maturité moyenne de Spotify est de 3,1 sur 5. Le niveau « proactif » est atteint : la gouvernance existe, mais elle est inégale selon les équipes. La cible est le niveau 4 (« maîtrisé »).
2. **Politique** : 9 principes (issus du guide *governance-principles-guide* du cours) sont traduits en règles, en indicateurs et en rôles. Le RGPD s'applique en Europe, les réglementations locales ailleurs, et la norme PCI-DSS (sécurité des cartes bancaires) pour les paiements.
3. **Plan** : la mise en place se fait en deux temps, pour limiter la résistance au changement et s'appuyer sur l'existant.

### Les rôles

| Rôle | Ce qu'il fait |
| --- | --- |
| CDO (Chief Data Officer, directeur des données) | porte la stratégie et préside le comité de gouvernance |
| DPO (délégué à la protection des données) | veille au respect du RGPD, de façon indépendante |
| Data Owner (propriétaire de la donnée) | décide des règles d'usage de ses données et en répond |
| Data Steward (référent données) | applique les règles au quotidien dans son équipe |
| Équipes techniques (Data Engineering) | mettent en œuvre les règles dans les outils |

### Le plan en deux temps

| Temps | Période | Ce qui se passe |
| --- | --- | --- |
| Temps 1 : décentralisé mais structuré | mois 1 à 12 | pilote sur le marketing (mois 1 à 6) ; si tout est au vert au mois 6 (go / no-go), déploiement dans les autres équipes, sans changer leur organisation (mois 7 à 12) |
| Temps 2 : centralisation | mois 13 à 24, après le bilan du mois 12 | les Data Stewards et les équipes techniques rejoignent le Centre d'Excellence (CoE) pour harmoniser les pratiques |

## Contenu du dossier

- `Bloc1_01_Rapport_maturite.pdf` : rapport de maturité
- `Bloc1_02_Politique_gouvernance.pdf` : politique de gouvernance, rôles et organigramme
- `Bloc1_03_Plan_implementation.pdf` : plan d'implémentation et diagramme de Gantt
