# Projet Stripe - From SQL to NoSQL (Bloc 2)

Conception d'une architecture de données pour Stripe : une base **OLTP** pour enregistrer les paiements, une base **OLAP** pour les analyser et une base **NoSQL** pour les données libres (logs, sessions, avis, features du modèle de fraude).

## Contenu

| Fichier | Description |
|---|---|
| `Projet_Stripe_Bloc2.pdf` | Présentation : architecture, OLTP, OLAP, NoSQL, pipeline, sécurité, machine learning |
| `schemas/oltp_transactions.dbml` et `.png` | Schéma de la base OLTP (PostgreSQL) |
| `schemas/olap_star_schema.dbml` et `olap_analyses.png` | Schéma en étoile de la base OLAP (Snowflake) |
| `schemas/nosql_mongodb_model.md` | Collections MongoDB (imbriqué ou référencé) |
| `schemas/requetes_sql_nosql.md` | 4 requêtes SQL et 3 requêtes MongoDB, avec la question métier |

Les fichiers `.dbml` se visualisent en les collant dans [dbdiagram.io](https://dbdiagram.io).

## Outils

PostgreSQL (OLTP), Snowflake et dbt (OLAP), MongoDB (NoSQL), Airflow (pipeline), S3 (zone de transit), MLflow (modèle de fraude).

## Limites

- Il s'agit d'une conception : les colonnes détaillées et les seuils des exemples sont des hypothèses.
- Pas de Kafka : le quasi temps réel est fait par des lots Airflow toutes les minutes.
